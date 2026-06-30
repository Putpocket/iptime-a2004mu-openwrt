#!/usr/bin/env python3
"""Analyze observed A2004MU kernel descriptor and CR6B payload structure."""

from __future__ import annotations

import argparse
import hashlib
import struct
from pathlib import Path

from verify_iptime_checksum import build_result, read_header


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
KDESC_LEN = 0x10
KDESC_OFFSET = FW_OFFSET + HEADER_LEN
CR6B_OFFSET = KDESC_OFFSET + KDESC_LEN
FLASH_SIZE = 0x800000
MAGICS = {
    "kernel": b"kernel",
    "cr6b": b"cr6b",
    "cs6c": b"cs6c",
    "hsqs": b"hsqs",
    "uImage": b"\x27\x05\x19\x56",
}


def u32le(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, offset)[0]


def u32be(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from(">I", data, offset)[0]


def find_all(data: bytes, marker: bytes) -> list[int]:
    offsets = []
    start = 0
    while True:
        offset = data.find(marker, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def checksum_status(path: Path, data: bytes) -> str:
    try:
        header = read_header(data)
        result, _ = build_result(path, data, hashlib.sha256(data).hexdigest(), header)
    except ValueError as exc:
        return f"unavailable: {exc}"
    return "MATCH" if result["matches"]["all"] else "MISMATCH"


def known_values(data: bytes) -> dict[str, int]:
    size = len(data)
    rootfs = data.find(MAGICS["hsqs"])
    cr6b = data.find(MAGICS["cr6b"])
    kdesc = data.find(b"kernel\x00\x00")
    values = {
        "file_size": size,
        "flash_size": FLASH_SIZE,
        "payload_start": KDESC_OFFSET,
        "cr6b_offset": cr6b,
        "kernel_descriptor_offset": kdesc,
    }
    if rootfs >= 0:
        values["rootfs_offset"] = rootfs
        values["rootfs_size"] = size - rootfs
    if cr6b >= 0:
        values["kernel_region_size"] = (rootfs if rootfs >= 0 else size) - cr6b
        values["cr6b_relative_rootfs_offset"] = rootfs - cr6b if rootfs >= 0 else -1
    if kdesc >= 0:
        length = u32le(data, kdesc + 8)
        checksum = u32le(data, kdesc + 12)
        if length is not None:
            values["descriptor_kernel_size"] = length
            values["cr6b_body_size"] = max(0, length - KDESC_LEN)
        if checksum is not None:
            values["descriptor_kernel_sum"] = checksum
    return values


def labels_for(value: int, known: dict[str, int]) -> str:
    labels = [name for name, candidate in known.items() if candidate == value and value >= 0]
    return ",".join(labels) if labels else "-"


def print_file(path: Path) -> None:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    known = known_values(data)

    print(f"FILE {path}")
    print(f"size {len(data)} 0x{len(data):x}")
    print(f"sha256 {digest}")
    print(f"fits_8mb {'yes' if len(data) <= FLASH_SIZE else 'no'}")
    print(f"checksum {checksum_status(path, data)}")

    for name, marker in MAGICS.items():
        offsets = find_all(data, marker)
        if offsets:
            rendered = " ".join(f"0x{x:x}" for x in offsets[:8])
            suffix = "" if len(offsets) <= 8 else f" ... ({len(offsets)} total)"
            print(f"{name}_offsets {rendered}{suffix}")
        else:
            print(f"{name}_offsets none")

    kdesc = known.get("kernel_descriptor_offset", -1)
    if kdesc >= 0 and kdesc + KDESC_LEN <= len(data):
        marker = data[kdesc : kdesc + 8]
        length = u32le(data, kdesc + 8)
        checksum = u32le(data, kdesc + 12)
        actual_sum = None
        if length is not None and CR6B_OFFSET + length <= len(data):
            actual_sum = sum(data[CR6B_OFFSET : CR6B_OFFSET + length]) & 0xFFFFFFFF
        print(
            "kernel_descriptor "
            f"offset=0x{kdesc:x} marker={marker!r} "
            f"length=0x{length:x} checksum=0x{checksum:08x} "
            f"actual_sum={('0x%08x' % actual_sum) if actual_sum is not None else 'n/a'}"
        )

    cr6b = known.get("cr6b_offset", -1)
    if cr6b >= 0:
        print("cr6b_words offset rel hex le32 le_match be32 be_match")
        limit = min(cr6b + 0x100, len(data))
        for off in range(cr6b, limit, 4):
            word = data[off : off + 4]
            le = u32le(data, off)
            be = u32be(data, off)
            print(
                f"0x{off:08x} +0x{off - cr6b:03x} {word.hex()} "
                f"0x{le:08x} {labels_for(le, known)} "
                f"0x{be:08x} {labels_for(be, known)}"
            )

    print()


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze A2004MU CR6B candidate structure.")
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()

    for path in args.paths:
        if not path.is_file():
            parser.error(f"not a file: {path}")
        print_file(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
