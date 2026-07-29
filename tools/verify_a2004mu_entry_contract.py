#!/usr/bin/env python3
"""Verify that an A2004MU candidate satisfies the bootloader's entry contract.

The RTL8197F boot code copies the cr6b payload into RAM and jumps to a fixed
entry address. The first-stage loader placed there is position-dependent MIPS
code, so it must be *linked* for that same address. A loader linked elsewhere
executes a few instructions and then jumps into uninitialised RAM, which shows
up on UART as "Undefined Exception happen." with no loader output at all.

This tool reads a local image, reconstructs what lands at the entry address and
reports whether the loader's link base agrees with it.
"""

from __future__ import annotations

import argparse
import collections
import json
import struct
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
KDESC_LEN = 0x10
KDESC_OFFSET = FW_OFFSET + HEADER_LEN
CR6B_OFFSET = KDESC_OFFSET + KDESC_LEN
CR6B_HEADER_LEN = 0x10
OBSERVED_ENTRY = 0x80A00000
# Stock uses lc=3,lp=0,pb=2 (0x5d); OpenWrt's lzma step uses -lc1 -lp2 -pb2 (0x6d).
LZMA_PROPS_BYTES = (0x5D, 0x6D)
SCAN_LEN = 0x4000
FILL_WORD = 0xFFFFFFFF


def u32le(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def read_cr6b(data: bytes) -> dict:
    if len(data) < CR6B_OFFSET + CR6B_HEADER_LEN:
        raise ValueError("image is too small to contain a cr6b header")
    signature = data[CR6B_OFFSET : CR6B_OFFSET + 4]
    start_addr, burn_addr, length = struct.unpack_from(">III", data, CR6B_OFFSET + 4)
    return {
        "signature": signature.decode("ascii", "replace"),
        "start_addr": start_addr,
        "burn_addr": burn_addr,
        "payload_len": length,
        "payload_file_offset": CR6B_OFFSET + CR6B_HEADER_LEN,
    }


def lui_histogram(data: bytes, start: int, end: int) -> collections.Counter:
    """Count LUI immediates. A position-dependent loader's link base dominates."""
    hits: collections.Counter = collections.Counter()
    for off in range(start, min(end, len(data)) - 3, 4):
        word = u32le(data, off)
        if word >> 26 == 0x0F:  # LUI
            hits[word & 0xFFFF] += 1
    return hits


def kseg0_bases(hits: collections.Counter) -> list[tuple[int, int]]:
    """kseg0 LUI immediates, most common first, as (address, count) pairs.

    A position-dependent loader references its own text, data and heap through
    LUI, so several kseg0 bases show up. The most common one is usually the heap
    or data region, not the text base, so the link base cannot be inferred from
    frequency alone -- it has to be tested against the entry address.
    """
    return [
        (immediate << 16, count)
        for immediate, count in hits.most_common()
        if 0x8000 <= immediate < 0x8400
    ]


def find_lzma(data: bytes, start: int, end: int) -> int:
    """Locate an LZMA-alone stream, accepting either props byte and any dict size."""
    for off in range(start, min(end, len(data)) - 13):
        if data[off] in LZMA_PROPS_BYTES and data[off + 1 : off + 3] == b"\x00\x00":
            return off
    return -1


def analyze(path: Path, expected_entry: int) -> dict:
    data = path.read_bytes()
    cr6b = read_cr6b(data)
    payload_start = cr6b["payload_file_offset"]
    payload_end = payload_start + cr6b["payload_len"]

    result: dict = {
        "path": str(path),
        "file_size": len(data),
        "cr6b": dict(cr6b),
        "expected_entry": expected_entry,
        "checks": {},
    }

    checks = result["checks"]
    checks["cr6b_signature"] = cr6b["signature"] == "cr6b"
    checks["payload_within_file"] = payload_end <= len(data)
    checks["start_addr_matches_expected_entry"] = cr6b["start_addr"] == expected_entry

    hits = lui_histogram(data, payload_start, payload_start + SCAN_LEN)
    bases = kseg0_bases(hits)
    image_lo = expected_entry
    image_hi = expected_entry + cr6b["payload_len"]
    inside = [(base, count) for base, count in bases if image_lo <= base < image_hi]

    result["kseg0_lui_bases"] = [
        {
            "base": f"0x{base:08x}",
            "count": count,
            "inside_image": image_lo <= base < image_hi,
        }
        for base, count in bases
    ]
    result["loaded_image_range"] = f"0x{image_lo:08x}..0x{image_hi:08x}"
    result["entry_words"] = [
        f"0x{u32le(data, payload_start + 4 * i):08x}"
        for i in range(8)
        if payload_start + 4 * i + 4 <= len(data)
    ]

    # A position-dependent loader always addresses something inside the image it
    # was linked into -- its own text, its payload or its BSS. If every absolute
    # reference points outside the region the boot code actually loaded, it was
    # linked for a different address and will fault on its first absolute jump.
    checks["loader_references_own_image"] = bool(inside)

    # 0xff fill at the entry is the classic symptom: the loader was written at a
    # padded offset instead of the first byte of the cr6b payload, so the CPU
    # executes fill bytes, which decode to a reserved instruction.
    first_word = u32le(data, payload_start) if payload_start + 4 <= len(data) else FILL_WORD
    checks["entry_is_not_fill"] = first_word != FILL_WORD

    lzma_offset = find_lzma(data, payload_start, payload_end if checks["payload_within_file"] else len(data))
    result["lzma_file_offset"] = lzma_offset if lzma_offset >= 0 else None
    result["lzma_entry_relative_offset"] = lzma_offset - payload_start if lzma_offset >= 0 else None
    result["lzma_ram_address"] = (
        expected_entry + (lzma_offset - payload_start) if lzma_offset >= 0 else None
    )
    checks["lzma_inside_cr6b_payload"] = lzma_offset >= 0

    result["status"] = "pass" if all(checks.values()) else "fail"
    result["diagnosis"] = diagnose(result)
    return result


def diagnose(result: dict) -> list[str]:
    notes: list[str] = []
    checks = result["checks"]
    entry = result["expected_entry"]

    if not checks["cr6b_signature"]:
        notes.append("cr6b header missing at 0x40048; bootloader will not find the image")
    if not checks["payload_within_file"]:
        notes.append("cr6b payload length runs past end of file")
    if not checks["start_addr_matches_expected_entry"]:
        notes.append(
            f"cr6b startAddr is 0x{result['cr6b']['start_addr']:08x} but the boot code "
            f"jumps to 0x{entry:08x}"
        )
    if not checks["entry_is_not_fill"]:
        notes.append(
            f"the first instruction at 0x{entry:08x} is 0xffffffff (fill), a reserved MIPS "
            "instruction; the loader is not at the start of the cr6b payload "
            "-> Undefined Exception with no loader output"
        )
    if not checks["loader_references_own_image"]:
        outside = ", ".join(b["base"] for b in result["kseg0_lui_bases"][:3])
        notes.append(
            f"loader makes no absolute reference inside {result['loaded_image_range']} "
            f"but does reference {outside}; it is linked for another address and will fault "
            "on its first absolute jump -> Undefined Exception with no loader output"
        )
    if not checks["lzma_inside_cr6b_payload"]:
        notes.append("no LZMA stream inside the cr6b payload; loader has nothing to decompress")
    if not notes:
        notes.append("entry contract satisfied")
    return notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--expected-entry", default=hex(OBSERVED_ENTRY))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    expected_entry = int(args.expected_entry, 0)
    results = [analyze(path, expected_entry) for path in args.images]

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for result in results:
            cr6b = result["cr6b"]
            print(f"{result['path']}")
            print(f"  status: {result['status'].upper()}")
            print(
                f"  cr6b: sig={cr6b['signature']} startAddr=0x{cr6b['start_addr']:08x} "
                f"burnAddr=0x{cr6b['burn_addr']:08x} len=0x{cr6b['payload_len']:x}"
            )
            print(f"  boot code jumps to:      0x{result['expected_entry']:08x}")
            print(f"  loaded image range:      {result['loaded_image_range']}")
            print(f"  entry first word:        {result['entry_words'][0]}")
            bases = ", ".join(
                f"{b['base']}({b['count']}{',in' if b['inside_image'] else ''})"
                for b in result["kseg0_lui_bases"][:4]
            )
            print(f"  kseg0 bases referenced:  {bases or 'none'}")
            if result["lzma_ram_address"] is not None:
                print(f"  LZMA lands at RAM:       0x{result['lzma_ram_address']:08x}")
            else:
                print("  LZMA lands at RAM:       none found in payload")
            for note in result["diagnosis"]:
                print(f"  - {note}")
            print()

    return 0 if all(r["status"] == "pass" for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
