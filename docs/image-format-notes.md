# Image Format Notes

These notes collect current observations about ipTIME A2004MU stock images and
Realtek SDK outputs. They are incomplete and must not be treated as a final
format specification.

## Stock ipTIME Image

The observed stock flash layout places the firmware region at absolute offset
`0x40000`. Header fields below are absolute file offsets from a full flash-style
image.

Observed fields in ipTIME stock firmware version 15.352:

| Offset | Observation |
| --- | --- |
| `0x40000` | model string, observed as `a2004m` |
| `0x40008` | version field |
| `0x40010` | Protect2 magic, observed as little-endian `0x9a8f998b` |
| `0x40014` | Protect2 checksum |
| `0x4002c` | rootfs absolute offset |
| `0x40030` | check length |
| `0x40034` | primary checksum |
| `0x40038` | kernel descriptor string, observed as `kernel` |
| near `0x40050` | firmware offset field; bytes at `0x40050` observed as `00 04 00 00`, which reads as big-endian `0x00040000` and little-endian `0x00000400` |

Uncertain details:

* Exact field widths and all padding/alignment rules are not fully documented.
* The version field encoding is not fully documented here.
* The firmware offset field is described as "near `0x40050`" until more images
  are compared; endian and alignment should remain uncertain for now.
* Rootfs offset varies between observed images and must not be hardcoded.
* Stock firmware version 15.352 had rootfs at absolute offset `0x2c0000`.
* An older bootlog showed rootfs offset `0x270000`.

## Checksum Observations

The following checksum behavior has been observed during local research:

* The primary checksum is based on a byte sum over the checked region.
* Protect2 uses the model string length and secret `0x128a8392`.

These observations are not a final public format specification. Treat checksum
logic as `observed` only when a tool verifies it against a specific local stock
image. Otherwise keep it `uncertain`.

`tools/verify_iptime_checksum.py` checks these observed checksum candidates
against a user-provided local stock firmware image. It is a validation helper,
not final image-format documentation and not image-generation logic.

`tools/plan_iptime_wrapper.py` is a dry-run layout sanity checker for work that
may happen before wrapper generation. It reports proposed offsets, size limits,
SDK image markers, and risk flags. It does not implement image generation and
does not produce a flash-verified image.

## Realtek SDK AP-fw Image

Realtek SDK output path used during local research:

```text
~/rtl8197f-research/openwrt_rtk/rtk_openwrt_sdk/bin/rtkmipsel
```

Observed SDK artifacts include:

```text
openwrt-rtkmipsel-rtl8197f-AP-fw.bin
openwrt-rtkmipsel-rtl8197f-AP-ramfs.bin
```

Current observations:

* SDK build succeeded.
* A ramfs image was generated.
* SDK generated `AP-fw.bin` is a Realtek `cvimg`/raw image, not ipTIME web
  update format.
* `AP-fw.bin` starts with `cs6c`.
* Current `AP-fw.bin` SquashFS magic was detected at offset `0x19c000`.
* Earlier notes indicated an SDK image using `linuxpart=0x60000`.
* A2004MU stock firmware region starts at `0x40000`, so any generated image
  using `linuxpart=0x60000` must be corrected before serious image wrapping
  work.
* The current locally inspected `AP-fw.bin` reports
  `board=AP console=ttyS0,38400 linuxpart=0x40000 hwpart=0x20000`.
* The current locally inspected `AP-ramfs.bin` starts with `cs6c`, has no
  detected SquashFS magic, and reports
  `board=AP console=ttyS0,38400 linuxpart=0x hwpart=0x root=/dev/mtdblock2`.

## Legacy Local Tools

Some older scripts in `tools/` are preserved for reference and should not be
deleted without a separate cleanup decision:

| Tool | Role |
| --- | --- |
| `analyze_header.py` | Local exploratory script for header words and CRC candidates; reads repo-local firmware path. |
| `verify_iptime_header.py` | Local checksum reproduction experiment; reads repo-local firmware path. |
| `verify_iptime_any.py` | Checksum reproduction experiment that can read a path argument. |
| `pack_a2004m_openwrt.py` | Legacy local packing experiment that writes a firmware candidate under `firmware/`; not part of the safe workflow. |

## Current Tooling Scope

The safe inspection scripts in `tools/` read local firmware artifacts without
modifying them. The experimental wrapper skeleton is intentionally conservative
and does not claim final correctness.

No image from this repository is flash-verified.
