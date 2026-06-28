#!/usr/bin/env python3
"""Dry-run planner for an experimental ipTIME wrapper layout."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
FLASH_SIZE = 0x800000
WARNING = "dry-run planning only; does not generate firmware image"
STRING_RE = re.compile(rb"[\x20-\x7e]{4,}")
STRING_KEYWORDS = ("board=", "console=", "linuxpart=", "hwpart=")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_u32le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def c_string(data: bytes) -> str:
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


def matching_strings(data: bytes) -> list[str]:
    matches: list[str] = []
    seen: set[str] = set()
    for match in STRING_RE.finditer(data):
        text = match.group(0).decode("ascii", errors="replace")
        if any(keyword in text for keyword in STRING_KEYWORDS) and text not in seen:
            seen.add(text)
            matches.append(text)
    return matches


def require_file(parser: argparse.ArgumentParser, path: Path, label: str) -> Path:
    resolved = path.expanduser()
    if not resolved.is_file():
        parser.error(f"{label} is not a file: {resolved}")
    return resolved


def build_plan(stock_path: Path, sdk_path: Path) -> dict:
    stock_data = stock_path.read_bytes()
    sdk_data = sdk_path.read_bytes()

    required_stock_size = FW_OFFSET + HEADER_LEN
    risks: list[str] = []
    if len(stock_data) < required_stock_size:
        risks.append("stock image is too small to contain the expected header")
        model = ""
        version = ""
        rootfs_offset = 0
        check_length = 0
        primary_checksum = 0
    else:
        model = c_string(stock_data[FW_OFFSET : FW_OFFSET + 8])
        version = c_string(stock_data[FW_OFFSET + 8 : FW_OFFSET + 16])
        rootfs_offset = read_u32le(stock_data, FW_OFFSET + 0x2C)
        check_length = read_u32le(stock_data, FW_OFFSET + 0x30)
        primary_checksum = read_u32le(stock_data, FW_OFFSET + 0x34)

    sdk_strings = matching_strings(sdk_data)
    squashfs_offsets = find_all(sdk_data, b"hsqs")
    starts_with_cs6c = sdk_data.startswith(b"cs6c")
    linuxpart_is_0x40000 = any("linuxpart=0x40000" in item for item in sdk_strings)

    proposed_payload_start = FW_OFFSET + HEADER_LEN
    proposed_payload_length = len(sdk_data)
    proposed_payload_end = proposed_payload_start + proposed_payload_length
    proposed_full_image_size = proposed_payload_end
    fits_flash = proposed_full_image_size <= FLASH_SIZE

    if not starts_with_cs6c:
        risks.append("SDK image does not start with cs6c")
    if not linuxpart_is_0x40000:
        risks.append("SDK image does not report linuxpart=0x40000")
    if not squashfs_offsets:
        risks.append("SDK image has no detected SquashFS magic")
    if model != "a2004m":
        risks.append("stock model field is not a2004m")
    if rootfs_offset < FW_OFFSET:
        risks.append("stock rootfs offset is zero or unexpectedly below firmware region")
    if not fits_flash:
        risks.append("proposed full image size exceeds 8MB flash size")

    status = "ok"
    if risks:
        status = "warning"
    if not fits_flash or len(stock_data) < required_stock_size:
        status = "error"

    return {
        "status": status,
        "warning": WARNING,
        "stock": {
            "path": str(stock_path),
            "file_size": len(stock_data),
            "sha256": sha256_file(stock_path),
            "model": model,
            "version": version,
            "rootfs_offset": rootfs_offset,
            "check_length": check_length,
            "primary_checksum": primary_checksum,
        },
        "sdk_image": {
            "path": str(sdk_path),
            "file_size": len(sdk_data),
            "sha256": sha256_file(sdk_path),
            "starts_with_cs6c": starts_with_cs6c,
            "squashfs_offsets": squashfs_offsets,
            "strings": sdk_strings,
        },
        "layout": {
            "firmware_region_start": FW_OFFSET,
            "flash_size": FLASH_SIZE,
            "expected_max_full_image_size": FLASH_SIZE,
            "proposed_payload_start": proposed_payload_start,
            "proposed_payload_length": proposed_payload_length,
            "proposed_payload_end": proposed_payload_end,
            "proposed_full_image_size": proposed_full_image_size,
            "fits_flash": fits_flash,
            "linuxpart_is_0x40000": linuxpart_is_0x40000,
        },
        "risks": risks,
    }


def print_hex_field(label: str, value: int) -> None:
    print(f"{label}: 0x{value:x} ({value})")


def print_text_plan(plan: dict) -> None:
    print("WARNING: dry-run planning only; does not generate firmware image")
    print("This is not image-generation logic and is not flash-verified.")
    print()
    print(f"status: {plan['status']}")
    print()

    stock = plan["stock"]
    print("stock:")
    print(f"  path: {stock['path']}")
    print_hex_field("  file size", stock["file_size"])
    print(f"  sha256: {stock['sha256']}")
    print(f"  model: {stock['model']!r}")
    print(f"  version: {stock['version']!r}")
    print_hex_field("  rootfs offset", stock["rootfs_offset"])
    print_hex_field("  check length", stock["check_length"])
    print_hex_field("  primary checksum field", stock["primary_checksum"])
    print()

    sdk = plan["sdk_image"]
    print("sdk image:")
    print(f"  path: {sdk['path']}")
    print_hex_field("  file size", sdk["file_size"])
    print(f"  sha256: {sdk['sha256']}")
    print(f"  starts with cs6c: {'yes' if sdk['starts_with_cs6c'] else 'no'}")
    if sdk["squashfs_offsets"]:
        print("  SquashFS magic offsets:")
        for offset in sdk["squashfs_offsets"]:
            print(f"    0x{offset:x} ({offset})")
    else:
        print("  SquashFS magic offsets: none")
    if sdk["strings"]:
        print("  matching strings:")
        for item in sdk["strings"]:
            print(f"    {item}")
    else:
        print("  matching strings: none")
    print()

    layout = plan["layout"]
    print("layout proposal:")
    print_hex_field("  expected firmware region start", layout["firmware_region_start"])
    print_hex_field("  expected flash size", layout["flash_size"])
    print_hex_field("  expected max full image size", layout["expected_max_full_image_size"])
    print_hex_field("  proposed payload start", layout["proposed_payload_start"])
    print_hex_field("  proposed payload length", layout["proposed_payload_length"])
    print_hex_field("  proposed payload end", layout["proposed_payload_end"])
    print_hex_field("  proposed full image size", layout["proposed_full_image_size"])
    print(f"  fits flash: {'yes' if layout['fits_flash'] else 'no'}")
    print(f"  linuxpart is 0x40000: {'yes' if layout['linuxpart_is_0x40000'] else 'no'}")
    print()

    if plan["risks"]:
        print("risks:")
        for risk in plan["risks"]:
            print(f"  - {risk}")
    else:
        print("risks: none")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run layout planner for an experimental ipTIME wrapper. "
            "This tool does not generate firmware images."
        )
    )
    parser.add_argument("--stock", type=Path, required=True, help="Local stock firmware path")
    parser.add_argument("--sdk-image", type=Path, required=True, help="Local SDK AP-fw image path")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    args = parser.parse_args()

    stock_path = require_file(parser, args.stock, "--stock")
    sdk_path = require_file(parser, args.sdk_image, "--sdk-image")
    plan = build_plan(stock_path, sdk_path)

    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_text_plan(plan)

    return 1 if plan["status"] == "error" else 0


if __name__ == "__main__":
    raise SystemExit(main())
