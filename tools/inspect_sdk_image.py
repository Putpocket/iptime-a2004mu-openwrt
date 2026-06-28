#!/usr/bin/env python3
"""Inspect selected properties of a local Realtek SDK AP-fw/AP-ramfs image."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path


STRING_RE = re.compile(rb"[\x20-\x7e]{4,}")
STRING_KEYWORDS = ("board=", "console=", "linuxpart=", "hwpart=", "root=")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx == -1:
            return offsets
        offsets.append(idx)
        start = idx + 1


def matching_strings(data: bytes) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()
    for match in STRING_RE.finditer(data):
        text = match.group(0).decode("ascii", errors="replace")
        if any(keyword in text for keyword in STRING_KEYWORDS) and text not in seen:
            seen.add(text)
            matches.append(text)
    return matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a Realtek SDK AP-fw/AP-ramfs image without modifying it."
    )
    parser.add_argument("image", type=Path, help="Path to a local SDK image")
    args = parser.parse_args()

    path = args.image.expanduser()
    if not path.is_file():
        parser.error(f"not a file: {path}")

    data = path.read_bytes()

    print(f"path: {path}")
    print(f"file size: {len(data)} bytes (0x{len(data):x})")
    print(f"sha256: {sha256_file(path)}")
    print(f"first 64 bytes: {data[:64].hex(' ')}")
    print(f"starts with cs6c: {'yes' if data.startswith(b'cs6c') else 'no'}")
    print()

    squashfs_offsets = find_all(data, b"hsqs")
    if squashfs_offsets:
        print("detected SquashFS magic offsets:")
        for offset in squashfs_offsets:
            print(f"  0x{offset:x} ({offset})")
    else:
        print("detected SquashFS magic offsets: none")

    print()
    strings = matching_strings(data)
    if strings:
        print("matching strings:")
        for text in strings:
            print(f"  {text}")
    else:
        print("matching strings: none")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
