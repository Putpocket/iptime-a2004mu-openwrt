#!/usr/bin/env python3
"""Inspect an OpenWrt uImage and its appended DTB."""

from __future__ import annotations

import argparse
import gzip
import lzma
import shutil
import struct
import subprocess
from pathlib import Path


UIMAGE_MAGIC = 0x27051956
DTB_MAGIC = b"\xd0\x0d\xfe\xed"
COMPRESSIONS = {
    0: "none",
    1: "gzip",
    2: "bzip2",
    3: "lzma",
    5: "lz4",
    6: "zstd",
}


def parse_uimage(data: bytes) -> dict:
    if len(data) < 64:
        raise ValueError("input is too small for a uImage header")
    fields = struct.unpack(">IIIIIIIBBBB32s", data[:64])
    magic = fields[0]
    if magic != UIMAGE_MAGIC:
        raise ValueError(f"uImage magic not found at offset 0: 0x{magic:08x}")
    data_size = fields[3]
    if 64 + data_size > len(data):
        raise ValueError("uImage payload length exceeds input size")
    return {
        "data_size": data_size,
        "load": fields[4],
        "entry": fields[5],
        "os": fields[7],
        "arch": fields[8],
        "type": fields[9],
        "compression": fields[10],
        "name": fields[11].rstrip(b"\0").decode("ascii", errors="replace"),
        "payload": data[64 : 64 + data_size],
    }


def decompress_payload(payload: bytes, compression: int) -> bytes:
    if compression == 0:
        return payload
    if compression == 1:
        return gzip.decompress(payload)
    if compression == 3:
        try:
            return lzma.decompress(payload, format=lzma.FORMAT_ALONE)
        except lzma.LZMAError:
            return lzma.decompress(payload)
    raise ValueError(f"unsupported compression type: {compression}")


def decompile_dtb(dtb: Path, dts: Path) -> bool:
    dtc = shutil.which("dtc")
    if not dtc:
        return False
    subprocess.run(
        [dtc, "-I", "dtb", "-O", "dts", "-o", str(dts), str(dtb)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def contains_any(text: str, needles: list[str]) -> bool:
    return any(needle in text for needle in needles)


def check_dts(dts_text: str) -> list[tuple[str, str]]:
    checks = [
        ("compatible iptime,a2004mu", "PASS" if "iptime,a2004mu" in dts_text else "FAIL"),
        (
            "compatible realtek,rtl8197f-soc",
            "PASS" if "realtek,rtl8197f-soc" in dts_text else "FAIL",
        ),
        ("model", "PASS" if "model = \"ipTIME A2004MU\"" in dts_text else "FAIL"),
        ("memory node", "PASS" if "device_type = \"memory\"" in dts_text else "FAIL"),
        (
            "memory size 0x04000000",
            "PASS" if contains_any(dts_text, ["0x4000000", "0x04000000"]) else "FAIL",
        ),
        ("chosen bootargs", "PASS" if "bootargs =" in dts_text else "FAIL"),
        ("console=ttyS0,38400", "PASS" if "console=ttyS0,38400" in dts_text else "FAIL"),
        ("rootfstype", "PASS" if "rootfstype=" in dts_text else "FAIL"),
    ]
    return checks


def find_appended_dtb(data: bytes) -> tuple[int, bytes]:
    candidates: list[tuple[int, int]] = []
    start = 0
    while True:
        offset = data.find(DTB_MAGIC, start)
        if offset < 0:
            break
        if offset + 8 <= len(data):
            total_size = struct.unpack_from(">I", data, offset + 4)[0]
            if 0 < total_size <= len(data) - offset:
                candidates.append((offset, total_size))
        start = offset + 1
    if not candidates:
        raise ValueError("DTB magic not found")
    offset, total_size = candidates[-1]
    return offset, data[offset : offset + total_size]


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an OpenWrt uImage appended DTB.")
    parser.add_argument("uimage", type=Path)
    parser.add_argument("--out-dtb", type=Path)
    parser.add_argument("--out-dts", type=Path)
    args = parser.parse_args()

    data = args.uimage.read_bytes()
    image = parse_uimage(data)
    compression_name = COMPRESSIONS.get(image["compression"], f"unknown-{image['compression']}")
    decompressed = decompress_payload(image["payload"], image["compression"])

    print(f"uImage: {args.uimage}")
    print(f"name: {image['name']}")
    print(f"compression: {compression_name} ({image['compression']})")
    print(f"uImage data size: {image['data_size']} bytes (0x{image['data_size']:x})")
    print(f"decompressed size: {len(decompressed)} bytes (0x{len(decompressed):x})")
    try:
        dtb_offset, dtb = find_appended_dtb(decompressed)
    except ValueError:
        print("DTB: FAIL not found")
        return 1
    print(f"DTB: PASS offset 0x{dtb_offset:x}, size {len(dtb)} bytes")

    dts_text = ""
    if args.out_dtb:
        args.out_dtb.write_bytes(dtb)
        print(f"wrote dtb: {args.out_dtb}")
    if args.out_dts:
        dtb_path = args.out_dtb or args.out_dts.with_suffix(".dtb")
        if not args.out_dtb:
            dtb_path.write_bytes(dtb)
        if decompile_dtb(dtb_path, args.out_dts):
            dts_text = args.out_dts.read_text(encoding="utf-8", errors="replace")
            print(f"wrote dts: {args.out_dts}")
        else:
            print("DTS: WARN dtc unavailable")

    if dts_text:
        failed = False
        for label, status in check_dts(dts_text):
            print(f"{label}: {status}")
            failed = failed or status == "FAIL"
        return 1 if failed else 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
