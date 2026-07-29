# A2004MU Bootloader Entry Contract

This note records why a candidate image can pass every upload and bootloader
check and still die with `Undefined Exception happen.` immediately after
`Jump to image start=0x80a00000...`.

Verify any candidate against this contract with:

```sh
python3 tools/verify_a2004mu_entry_contract.py <image.bin>
```

## What the boot code actually does

The `cr6b` header sits at file offset `0x40048` (ipTIME header `0x38` bytes +
kernel descriptor `0x10` bytes). It is 16 bytes, big-endian:

| Offset | Field | Stock value |
| --- | --- | --- |
| `0x00` | signature | `cr6b` |
| `0x04` | `startAddr` | `0x80A00000` |
| `0x08` | `burnAddr` | `0x00040000` |
| `0x0C` | `len` | `0x271402` |

The boot code copies `len` bytes starting at `cr6b + 0x10` (file `0x40058`) into
RAM at `startAddr`, then jumps to `startAddr`. Both observed values line up with
the stock UART log: `Check Firmware(00040000)` is `burnAddr`, and
`Jump to image start=0x80a00000` is `startAddr`.

`Check Firmware ... [ OK ]` only validates the ipTIME header magic, size and
checksum. **It says nothing about whether the bytes at the entry are executable
code.**

## The contract the first-stage loader must satisfy

The first-stage loader is **position-dependent MIPS code**. It is not relocated
and not PIC, so it must be *linked* for the address the boot code jumps to.

Evidence, from the LUI immediates in the stock loader (a MIPS `lui` carries the
high half of every absolute address the code touches):

| kseg0 base referenced | LUI hits | Meaning |
| --- | --- | --- |
| `0x80C70000` | 30 | loader heap / working buffers |
| `0x80A00000` | 25 | **loader's own text — its link base** |
| `0x80000000` | 14 | where the kernel is decompressed to |

So the stock memory map at jump time is:

```text
0x80000000  kernel decompress target (grows upward)
   ...
0x80A00000  first-stage loader text   <- boot code jumps here
0x80A02808  LZMA stream (immediately after loader text)
   ...
0x80C70000  loader heap
```

The loader lives *above* the kernel decompress target on purpose: it must not be
overwritten by the kernel it is unpacking.

Note that the most frequent LUI base is the heap, not the text base. The link
base cannot be inferred from frequency alone. The reliable test is whether the
loader makes *any* absolute reference inside the range the boot code actually
loaded (`startAddr .. startAddr + len`): a position-dependent loader always
addresses its own text, payload or BSS, so a loader with no reference into that
range was linked for somewhere else.

## Failure modes seen on this board

Three distinct ways to violate the contract were observed, all producing the
same `Undefined Exception happen.` with no loader output.

### 1. Loader linked for the wrong address

An early candidate reused a loader linked for `0x80500000` while the boot code
jumps to `0x80A00000`. Its LUI references all pointed at `0x805xxxxx` and never
at the loaded image range. It executed the few position-independent leading
instructions and then took its first absolute reference into uninitialised RAM
and faulted, before any UART output.

### 2. Padding in front of the loader (the actual A2004MU bug)

The factory wrapper wrote the loader at file offset `0x40080` while placing the
`cr6b` header at `0x40048`. The boot code starts executing at `cr6b + 0x10 =
0x40058`, so the CPU ran the 40 bytes of `0xff` image fill between `0x40058` and
`0x40080` first. `0xffffffff` is a reserved MIPS instruction, so the very first
fetch faulted. The loader itself was correct and correctly linked; it was simply
40 bytes too late. Fix: write the loader at exactly `cr6b + 0x10`.

### 3. Wrong entry symbol inside the loader

Once the loader sat at the right offset, an intermediate build entered at
`decompress.c`'s `entry()` instead of `start.S`'s `_start`, because the generic
`lzma.lds.in` places `*(.text.entry)` first and `-ffunction-sections` puts
`entry()` in that section. That skips cache setup and passes `entry()` garbage
arguments. Fix: give `_start` its own `.text.start` section and place it first.

The earlier candidate that printed `Uncompressing Linux...LZMA: Decoding error =
1` had a correctly placed, correctly linked, correctly entered loader — it ran
far enough to reach its own decompression error path. That is the signature of a
loader that executes; the failures above never execute at all.

## Requirements for a bootable candidate

1. `cr6b.startAddr` = `0x80A00000` and `cr6b.burnAddr` = `0x00040000`.
2. `cr6b.len` covers loader text + LZMA payload, measured from `cr6b + 0x10`.
3. The loader begins at exactly `cr6b + 0x10` (file `0x40058`), with no padding.
4. The loader is **linked for `0x80A00000`** and its first instruction is
   `start.S`'s `_start`, not `entry()`.
5. The loader decompresses the kernel to its load base and jumps to the kernel's
   entry symbol. On this MIPS kernel these differ (`_text=0x80000000`,
   `kernel_entry=0x8066xxxx`); both are read from the built ELF by
   `image/kernel-addrs.py`.
6. The loader+payload (`0x80A00000..`) must not overlap the kernel decompression
   region (`0x80000000..0x809b8ad0`). Current headroom is `0x47530` bytes.

For a clean-room port this means building OpenWrt's `lzma-loader` with its text
address set to `0x80A00000` rather than reusing the stock loader binary, and
placing it at the first byte of the cr6b payload.
