#!/usr/bin/env python3
"""Inspect selected fields from a local ipTIME stock firmware image."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


FIELDS = [
    ("model field at 0x40000", 0x40000, "string", 8),
    ("version field at 0x40008", 0x40008, "string", 8),
    ("protect2 magic at 0x40010", 0x40010, "u32le", 4),
    ("protect2 checksum at 0x40014", 0x40014, "u32le", 4),
    ("rootfs absolute offset at 0x4002c", 0x4002C, "u32le", 4),
    ("check length at 0x40030", 0x40030, "u32le", 4),
    ("primary checksum at 0x40034", 0x40034, "u32le", 4),
    ("kernel string at 0x40038", 0x40038, "string", 16),
    ("firmware offset field near 0x40050", 0x40050, "u32both", 4),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def clean_string(data: bytes) -> str:
    return data.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx == -1:
            return offsets
        offsets.append(idx)
        start = idx + 1


def format_field(data: bytes | None, kind: str) -> str:
    if data is None:
        return "not present"
    if kind == "string":
        return f"{clean_string(data)!r} (raw {data.hex()})"
    if kind == "u32le":
        value = int.from_bytes(data, "little")
        return f"0x{value:08x} ({value}, raw {data.hex()})"
    if kind == "u32both":
        le_value = int.from_bytes(data, "little")
        be_value = int.from_bytes(data, "big")
        return (
            f"le 0x{le_value:08x} ({le_value}), "
            f"be 0x{be_value:08x} ({be_value}), raw {data.hex()}"
        )
    raise ValueError(f"unknown field kind: {kind}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect selected ipTIME A2004MU stock firmware fields."
    )
    parser.add_argument("firmware", type=Path, help="Path to a local stock firmware file")
    args = parser.parse_args()

    path = args.firmware.expanduser()
    if not path.is_file():
        parser.error(f"not a file: {path}")

    data = path.read_bytes()

    print(f"path: {path}")
    print(f"file size: {len(data)} bytes (0x{len(data):x})")
    print(f"sha256: {sha256_file(path)}")
    print()

    for label, offset, kind, size in FIELDS:
        print(f"{label}: {format_field(data[offset : offset + size] if len(data) >= offset + size else None, kind)}")

    print()
    squashfs_offsets = find_all(data, b"hsqs")
    if squashfs_offsets:
        print("detected SquashFS magic offsets:")
        for offset in squashfs_offsets:
            print(f"  0x{offset:x} ({offset})")
    else:
        print("detected SquashFS magic offsets: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
