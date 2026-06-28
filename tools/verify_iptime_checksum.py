#!/usr/bin/env python3
"""Verify observed ipTIME checksum candidates against a local stock image."""

from __future__ import annotations

import argparse
import hashlib
from dataclasses import dataclass
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
PROTECT2_MAGIC = 0x9A8F998B
PROTECT2_SECRET_CANDIDATE = 0x128A8392


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
    args = parser.parse_args()

    path = args.firmware.expanduser()
    if not path.is_file():
        parser.error(f"not a file: {path}")

    data = path.read_bytes()
    header = read_header(data)

    print("WARNING: checksum logic below is experimental observed-candidate validation.")
    print("It is not a final ipTIME image format specification.")
    print()
    print(f"path: {path}")
    print(f"file size: {len(data)} bytes (0x{len(data):x})")
    print(f"sha256: {sha256_file(path)}")
    print()

    print(f"model field at 0x40000: {ascii_field(header.model_raw)!r} (raw {header.model_raw.hex()})")
    print(
        f"version field at 0x40008: "
        f"{ascii_field(header.version_raw)!r} (raw {header.version_raw.hex()})"
    )
    print_field("Protect2 magic field at 0x40010", header.protect2_magic)
    print_field("Protect2 checksum field at 0x40014", header.protect2_checksum)
    print_field("rootfs offset field at 0x4002c", header.rootfs_offset)
    print_field("check length field at 0x40030", header.check_length)
    print_field("primary checksum field at 0x40034", header.primary_checksum)
    print(
        f"kernel string at 0x40038: "
        f"{ascii_field(header.kernel_raw)!r} (raw {header.kernel_raw.hex()})"
    )
    print()

    payload_start = FW_OFFSET + HEADER_LEN
    payload_end = payload_start + header.check_length
    if payload_end > len(data):
        print(
            "experimental primary byte-sum candidate: skipped "
            f"(range 0x{payload_start:x}-0x{payload_end:x} exceeds file size)"
        )
        return 1

    payload = data[payload_start:payload_end]
    byte_sum = sum(payload) & 0xFFFFFFFF
    primary_candidate = protect_crc_candidate(
        byte_sum, PROTECT2_SECRET_CANDIDATE, header.model_raw
    )
    protect2_candidate = protect_crc2_candidate(
        primary_candidate, PROTECT2_SECRET_CANDIDATE, header.model_raw
    )

    print("experimental observed checksum candidates:")
    print(f"  payload range: 0x{payload_start:x}-0x{payload_end:x}")
    print(f"  primary byte-sum candidate: 0x{byte_sum:08x}")
    print(
        "  primary checksum candidate using model length and "
        f"0x{PROTECT2_SECRET_CANDIDATE:08x}: "
        f"0x{primary_candidate:08x} "
        f"{status(primary_candidate, header.primary_checksum)}"
    )
    print(
        "  Protect2 checksum candidate using model length and "
        f"0x{PROTECT2_SECRET_CANDIDATE:08x}: "
        f"0x{protect2_candidate:08x} "
        f"{status(protect2_candidate, header.protect2_checksum)}"
    )

    magic_status = status(PROTECT2_MAGIC, header.protect2_magic)
    print(
        f"  Protect2 magic candidate 0x{PROTECT2_MAGIC:08x}: "
        f"{magic_status}"
    )

    if (
        primary_candidate == header.primary_checksum
        and protect2_candidate == header.protect2_checksum
        and PROTECT2_MAGIC == header.protect2_magic
    ):
        print("result: observed candidates MATCH this image")
    else:
        print("result: one or more observed candidates MISMATCH this image")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
