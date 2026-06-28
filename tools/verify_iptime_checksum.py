#!/usr/bin/env python3
"""Verify observed ipTIME checksum candidates against a local stock image."""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
PROTECT2_MAGIC = 0x9A8F998B
PROTECT2_SECRET_CANDIDATE = 0x128A8392
WARNING = (
    "experimental observed-candidate validation, not a final image format "
    "specification"
)


@dataclass(frozen=True)
class Header:
    model_raw: bytes
    version_raw: bytes
    protect2_magic: int
    protect2_checksum: int
    rootfs_offset: int
    check_length: int
    primary_checksum: int
    kernel_raw: bytes


def c_string(data: bytes) -> bytes:
    return data.split(b"\x00", 1)[0]


def ascii_field(data: bytes) -> str:
    return c_string(data).decode("ascii", errors="replace")


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_u32le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 4], "little")


def read_header(data: bytes) -> Header:
    required = FW_OFFSET + HEADER_LEN
    if len(data) < required:
        raise ValueError(
            f"file is too small for header at 0x{FW_OFFSET:x}: "
            f"{len(data)} bytes"
        )

    return Header(
        model_raw=data[FW_OFFSET : FW_OFFSET + 8],
        version_raw=data[FW_OFFSET + 8 : FW_OFFSET + 16],
        protect2_magic=read_u32le(data, FW_OFFSET + 0x10),
        protect2_checksum=read_u32le(data, FW_OFFSET + 0x14),
        rootfs_offset=read_u32le(data, FW_OFFSET + 0x2C),
        check_length=read_u32le(data, FW_OFFSET + 0x30),
        primary_checksum=read_u32le(data, FW_OFFSET + 0x34),
        kernel_raw=data[FW_OFFSET + 0x38 : FW_OFFSET + 0x48],
    )


def protect_crc_candidate(base_sum: int, secret: int, model_raw: bytes) -> int:
    model_len = len(c_string(model_raw))
    return u32(u32(model_len * secret) + u32(~base_sum)) ^ base_sum


def protect_crc2_candidate(base_sum: int, secret: int, model_raw: bytes) -> int:
    model = c_string(model_raw)
    model_len = len(model)
    value = protect_crc_candidate(base_sum, secret, model_raw)
    for byte in model:
        value = u32(value + byte * model_len)
    return value


def status(calculated: int, stored: int) -> str:
    return "MATCH" if calculated == stored else "MISMATCH"


def print_field(label: str, value: int) -> None:
    print(f"{label}: 0x{value:08x} ({value})")


def build_result(path: Path, data: bytes, digest: str, header: Header) -> tuple[dict, int]:
    payload_start = FW_OFFSET + HEADER_LEN
    payload_end = payload_start + header.check_length

    result = {
        "path": str(path),
        "file_size": len(data),
        "sha256": digest,
        "fields": {
            "model": ascii_field(header.model_raw),
            "version": ascii_field(header.version_raw),
            "protect2_magic": header.protect2_magic,
            "protect2_checksum": header.protect2_checksum,
            "rootfs_offset": header.rootfs_offset,
            "check_length": header.check_length,
            "primary_checksum": header.primary_checksum,
            "kernel_string": ascii_field(header.kernel_raw),
        },
        "candidates": {
            "payload_start": payload_start,
            "payload_end": payload_end,
            "primary_byte_sum": None,
            "primary_checksum_candidate": None,
            "protect2_checksum_candidate": None,
            "protect2_magic_candidate": PROTECT2_MAGIC,
        },
        "matches": {
            "primary_checksum": False,
            "protect2_checksum": False,
            "protect2_magic": PROTECT2_MAGIC == header.protect2_magic,
            "all": False,
        },
        "status": "range_error",
        "warning": WARNING,
    }

    if payload_end > len(data):
        result["error"] = (
            f"payload range 0x{payload_start:x}-0x{payload_end:x} "
            f"exceeds file size 0x{len(data):x}"
        )
        return result, 1

    payload = data[payload_start:payload_end]
    byte_sum = sum(payload) & 0xFFFFFFFF
    primary_candidate = protect_crc_candidate(
        byte_sum, PROTECT2_SECRET_CANDIDATE, header.model_raw
    )
    protect2_candidate = protect_crc2_candidate(
        primary_candidate, PROTECT2_SECRET_CANDIDATE, header.model_raw
    )
    primary_match = primary_candidate == header.primary_checksum
    protect2_match = protect2_candidate == header.protect2_checksum
    all_match = (
        primary_match
        and protect2_match
        and result["matches"]["protect2_magic"]
    )

    result["candidates"].update(
        {
            "primary_byte_sum": byte_sum,
            "primary_checksum_candidate": primary_candidate,
            "protect2_checksum_candidate": protect2_candidate,
        }
    )
    result["matches"].update(
        {
            "primary_checksum": primary_match,
            "protect2_checksum": protect2_match,
            "all": all_match,
        }
    )
    result["status"] = "match" if all_match else "mismatch"
    return result, 0


def print_text_result(result: dict, header: Header) -> None:
    print("WARNING: checksum logic below is experimental observed-candidate validation.")
    print("It is not a final ipTIME image format specification.")
    print()
    print(f"path: {result['path']}")
    print(f"file size: {result['file_size']} bytes (0x{result['file_size']:x})")
    print(f"sha256: {result['sha256']}")
    print()

    print(f"model field at 0x40000: {result['fields']['model']!r} (raw {header.model_raw.hex()})")
    print(
        f"version field at 0x40008: "
        f"{result['fields']['version']!r} (raw {header.version_raw.hex()})"
    )
    print_field("Protect2 magic field at 0x40010", result["fields"]["protect2_magic"])
    print_field("Protect2 checksum field at 0x40014", result["fields"]["protect2_checksum"])
    print_field("rootfs offset field at 0x4002c", result["fields"]["rootfs_offset"])
    print_field("check length field at 0x40030", result["fields"]["check_length"])
    print_field("primary checksum field at 0x40034", result["fields"]["primary_checksum"])
    print(
        f"kernel string at 0x40038: "
        f"{result['fields']['kernel_string']!r} (raw {header.kernel_raw.hex()})"
    )
    print()

    if result["status"] == "range_error":
        print(f"experimental primary byte-sum candidate: skipped ({result['error']})")
        return

    candidates = result["candidates"]
    matches = result["matches"]
    print("experimental observed checksum candidates:")
    print(f"  payload range: 0x{candidates['payload_start']:x}-0x{candidates['payload_end']:x}")
    print(f"  primary byte-sum candidate: 0x{candidates['primary_byte_sum']:08x}")
    print(
        "  primary checksum candidate using model length and "
        f"0x{PROTECT2_SECRET_CANDIDATE:08x}: "
        f"0x{candidates['primary_checksum_candidate']:08x} "
        f"{'MATCH' if matches['primary_checksum'] else 'MISMATCH'}"
    )
    print(
        "  Protect2 checksum candidate using model length and "
        f"0x{PROTECT2_SECRET_CANDIDATE:08x}: "
        f"0x{candidates['protect2_checksum_candidate']:08x} "
        f"{'MATCH' if matches['protect2_checksum'] else 'MISMATCH'}"
    )
    print(
        f"  Protect2 magic candidate 0x{candidates['protect2_magic_candidate']:08x}: "
        f"{'MATCH' if matches['protect2_magic'] else 'MISMATCH'}"
    )

    if matches["all"]:
        print("result: observed candidates MATCH this image")
    else:
        print("result: one or more observed candidates MISMATCH this image")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify observed ipTIME checksum candidates against a local stock "
            "firmware image. This is experimental and not a format spec."
        )
    )
    parser.add_argument(
        "firmware",
        type=Path,
        help="Path to a local stock firmware image; the file is read only",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only",
    )
    args = parser.parse_args()

    path = args.firmware.expanduser()
    if not path.is_file():
        parser.error(f"not a file: {path}")

    data = path.read_bytes()
    header = read_header(data)
    result, exit_code = build_result(path, data, sha256_file(path), header)

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_result(result, header)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
