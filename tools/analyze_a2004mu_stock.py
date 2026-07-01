#!/usr/bin/env python3
"""Validate stock ipTIME A2004M/A2004MU firmware structure."""

from __future__ import annotations

import argparse
import hashlib
import lzma
import struct
from pathlib import Path


EXPECTED = {
    "size": 0x759000,
    "sha256": "d0802fa7f961d9599fdf245e2f31d8a19f40bff0513467d93612bdec1d50ef88",
    "sysparam_magic": b"BTMAGIN\x00",
    "product": "a2004m",
    "version": "15.352",
    "protect2": 0x9A8F998B,
    "rootfs_field": 0x2C0000,
    "body_size_field": 0x718FC8,
    "total_checksum": 0x0EBC146B,
    "kernel_marker": b"kernel\x00\x00",
    "kernel_size": 0x271412,
    "kernel_checksum": 0x136937D3,
    "cr6b": b"cr6b",
    "load_addr": 0x80A00000,
    "flash_offset": 0x00040000,
    "cr6b_size": 0x00271402,
    "lzma_offset": 0x42860,
    "lzma_body_offset": 0x2860,
    "lzma_props": bytes.fromhex("5d00008000"),
    "lzma_usize": 0x8168FC,
    "rootfs_offset": 0x2C0000,
    "rootfs_body_offset": 0x280000,
    "squashfs_bytes_used": 0x49831C,
}

FW_OFFSET = 0x40000
SYS_MAGIC_OFFSET = 0x1FC00
SYS_PRODUCT_OFFSET = 0x1FC08
SQUASHFS_MAGIC = b"hsqs"


def cstr(data: bytes) -> str:
    return data.split(b"\x00", 1)[0].decode("ascii", errors="replace")


def u32le(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def u32be(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def u64le(data: bytes, off: int) -> int:
    return struct.unpack_from("<Q", data, off)[0]


def check(label: str, actual, expected) -> bool:
    ok = actual == expected
    if isinstance(actual, int):
        actual_text = f"0x{actual:x}"
    else:
        actual_text = repr(actual)
    if isinstance(expected, int):
        expected_text = f"0x{expected:x}"
    else:
        expected_text = repr(expected)
    print(f"{label}: {'PASS' if ok else 'FAIL'} actual={actual_text} expected={expected_text}")
    return ok


def lzma_info(data: bytes, lzma_offset: int, rootfs_offset: int) -> tuple[bool, dict]:
    payload = data[lzma_offset:rootfs_offset]
    info = {
        "props": payload[:5],
        "usize": u64le(payload, 5) if len(payload) >= 13 else None,
        "actual_size": None,
        "consumed": None,
        "error": None,
    }
    try:
        dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        out = dec.decompress(payload)
    except lzma.LZMAError as exc:
        info["error"] = str(exc)
        return False, info
    info["actual_size"] = len(out)
    info["consumed"] = len(payload) - len(dec.unused_data)
    return dec.eof, info


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate stock A2004M firmware structure.")
    parser.add_argument("firmware", type=Path)
    args = parser.parse_args()

    path = args.firmware
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    ok = True

    print(f"path: {path}")
    print(f"size: 0x{len(data):x}")
    print(f"sha256: {digest}")
    ok &= check("file_size", len(data), EXPECTED["size"])
    ok &= check("sha256", digest, EXPECTED["sha256"])

    ok &= check("sysparam_magic@0x1fc00", data[SYS_MAGIC_OFFSET:SYS_MAGIC_OFFSET + 8], EXPECTED["sysparam_magic"])
    ok &= check("sysparam_product@0x1fc08", cstr(data[SYS_PRODUCT_OFFSET:SYS_PRODUCT_OFFSET + 8]), EXPECTED["product"])
    ok &= check("firmware_product@0x40000", cstr(data[FW_OFFSET:FW_OFFSET + 8]), EXPECTED["product"])
    ok &= check("firmware_version@0x40008", cstr(data[FW_OFFSET + 8:FW_OFFSET + 16]), EXPECTED["version"])
    ok &= check("protect2@0x40010", u32le(data, FW_OFFSET + 0x10), EXPECTED["protect2"])
    ok &= check("rootfs_field@0x4002c", u32le(data, FW_OFFSET + 0x2C), EXPECTED["rootfs_field"])
    ok &= check("body_size_field@0x40030", u32le(data, FW_OFFSET + 0x30), EXPECTED["body_size_field"])
    ok &= check("total_checksum_field@0x40034", u32le(data, FW_OFFSET + 0x34), EXPECTED["total_checksum"])
    ok &= check("kernel_marker@0x40038", data[FW_OFFSET + 0x38:FW_OFFSET + 0x40], EXPECTED["kernel_marker"])
    ok &= check("kernel_size@0x40040", u32le(data, FW_OFFSET + 0x40), EXPECTED["kernel_size"])
    ok &= check("kernel_checksum_field@0x40044", u32le(data, FW_OFFSET + 0x44), EXPECTED["kernel_checksum"])
    ok &= check("cr6b@0x40048", data[FW_OFFSET + 0x48:FW_OFFSET + 0x4C], EXPECTED["cr6b"])
    ok &= check("load_addr@0x4004c", u32be(data, FW_OFFSET + 0x4C), EXPECTED["load_addr"])
    ok &= check("flash_offset@0x40050", u32be(data, FW_OFFSET + 0x50), EXPECTED["flash_offset"])
    ok &= check("cr6b_size@0x40054", u32be(data, FW_OFFSET + 0x54), EXPECTED["cr6b_size"])

    lzma_offset = data.find(EXPECTED["lzma_props"], FW_OFFSET)
    rootfs_offset = data.find(SQUASHFS_MAGIC, FW_OFFSET)
    ok &= check("lzma_offset", lzma_offset, EXPECTED["lzma_offset"])
    ok &= check("lzma_body_offset", lzma_offset - FW_OFFSET, EXPECTED["lzma_body_offset"])
    ok &= check("lzma_props", data[lzma_offset:lzma_offset + 5], EXPECTED["lzma_props"])
    lzma_ok, lzma = lzma_info(data, lzma_offset, rootfs_offset)
    ok &= check("lzma_header_usize", lzma["usize"], EXPECTED["lzma_usize"])
    ok &= check("lzma_decode", lzma_ok, True)
    ok &= check("lzma_actual_size", lzma["actual_size"], EXPECTED["lzma_usize"])
    print(f"lzma_stream_consumed: 0x{lzma['consumed']:x}")

    ok &= check("rootfs_offset", rootfs_offset, EXPECTED["rootfs_offset"])
    ok &= check("rootfs_body_offset", rootfs_offset - FW_OFFSET, EXPECTED["rootfs_body_offset"])
    bytes_used = u64le(data, rootfs_offset + 0x28)
    ok &= check("squashfs_bytes_used", bytes_used, EXPECTED["squashfs_bytes_used"])

    kernel_sum = sum(data[FW_OFFSET + 0x48:FW_OFFSET + 0x48 + EXPECTED["kernel_size"]]) & 0xFFFFFFFF
    ok &= check("kernel_checksum_reproduced", kernel_sum, EXPECTED["kernel_checksum"])
    print("total_checksum_reproduced: CHECKSUM_UNKNOWN")

    print(f"stock_status: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
