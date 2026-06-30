#!/usr/bin/env python3
"""Build an experimental A2004MU ipTIME candidate with a CR6B-style payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from make_experimental_iptime_image import sha256_bytes, self_check_output
from plan_iptime_wrapper import FLASH_SIZE, FW_OFFSET, HEADER_LEN, require_file
from verify_iptime_checksum import (
    PROTECT2_MAGIC,
    PROTECT2_SECRET_CANDIDATE,
    protect_crc2_candidate,
    protect_crc_candidate,
)


KDESC_LEN = 0x10
CR6B_OFFSET = FW_OFFSET + HEADER_LEN + KDESC_LEN
UIMAGE_MAGIC = b"\x27\x05\x19\x56"
SQUASHFS_MAGIC = b"hsqs"
KERNEL_MARKER = b"kernel\x00\x00"


def align_up(value: int, alignment: int) -> int:
    return (value + alignment - 1) & ~(alignment - 1)


def find_required(data: bytes, marker: bytes, name: str) -> int:
    offset = data.find(marker)
    if offset < 0:
        raise ValueError(f"{name} marker not found")
    return offset


def output_outside_repo(path: Path, repo: Path) -> bool:
    resolved = path.expanduser().resolve()
    try:
        resolved.relative_to(repo.resolve())
    except ValueError:
        return True
    return False


def read_uimage_kernel(data: bytes) -> tuple[bytes, int, int]:
    uimage_offset = find_required(data, UIMAGE_MAGIC, "uImage")
    if uimage_offset + 0x40 > len(data):
        raise ValueError("uImage header is truncated")
    data_size = struct.unpack_from(">I", data, uimage_offset + 0x0C)[0]
    kernel_end = uimage_offset + 0x40 + data_size
    if kernel_end > len(data):
        raise ValueError("uImage data length exceeds input size")
    return data[uimage_offset + 0x40 : kernel_end], uimage_offset, kernel_end


def read_template(data: bytes) -> tuple[bytearray, bytes]:
    if len(data) < CR6B_OFFSET + 0x10:
        raise ValueError("template image is too small")
    if data[FW_OFFSET + HEADER_LEN : FW_OFFSET + HEADER_LEN + len(KERNEL_MARKER)] != KERNEL_MARKER:
        raise ValueError("template does not contain kernel descriptor at 0x40038")
    if data[CR6B_OFFSET : CR6B_OFFSET + 4] != b"cr6b":
        raise ValueError("template does not contain cr6b at 0x40048")
    return bytearray(data[FW_OFFSET : FW_OFFSET + HEADER_LEN]), data[CR6B_OFFSET : CR6B_OFFSET + 0x10]


def build_image(
    stock_data: bytes,
    template_data: bytes,
    openwrt_data: bytes,
    rootfs_offset_arg: str,
) -> tuple[bytes, dict]:
    kernel_body, uimage_offset, uimage_kernel_end = read_uimage_kernel(openwrt_data)
    squashfs_offset = find_required(openwrt_data, SQUASHFS_MAGIC, "SquashFS")
    if squashfs_offset < uimage_kernel_end:
        raise ValueError("SquashFS marker overlaps uImage kernel")
    rootfs_blob = openwrt_data[squashfs_offset:]

    header, cr6b_template = read_template(template_data)
    kernel_blob = cr6b_template + kernel_body

    requested_rootfs_offset = None
    if rootfs_offset_arg == "auto":
        template_rootfs_offset = struct.unpack_from("<I", template_data, FW_OFFSET + 0x2C)[0]
        rootfs_offset = template_rootfs_offset
    else:
        rootfs_offset = int(rootfs_offset_arg, 0)
        requested_rootfs_offset = rootfs_offset

    min_rootfs_offset = align_up(CR6B_OFFSET + len(kernel_blob), 0x10000)
    if rootfs_offset < min_rootfs_offset:
        rootfs_offset = min_rootfs_offset

    file_size = rootfs_offset + len(rootfs_blob)
    if file_size > FLASH_SIZE:
        raise ValueError(f"planned output exceeds 8MB flash: 0x{file_size:x}")
    if len(stock_data) < FW_OFFSET:
        raise ValueError("stock firmware is too small for prefix copy")

    image = bytearray(stock_data[:FW_OFFSET])
    image.extend(b"\x00" * (file_size - len(image)))

    struct.pack_into("<I", header, 0x10, PROTECT2_MAGIC)
    struct.pack_into("<I", header, 0x14, 0)
    struct.pack_into("<I", header, 0x2C, rootfs_offset)
    struct.pack_into("<I", header, 0x30, 0)
    struct.pack_into("<I", header, 0x34, 0)

    kernel_sum = sum(kernel_blob) & 0xFFFFFFFF
    descriptor = KERNEL_MARKER + struct.pack("<I", len(kernel_blob)) + struct.pack("<I", kernel_sum)

    image[FW_OFFSET : FW_OFFSET + HEADER_LEN] = header
    image[FW_OFFSET + HEADER_LEN : FW_OFFSET + HEADER_LEN + KDESC_LEN] = descriptor
    image[CR6B_OFFSET : CR6B_OFFSET + len(kernel_blob)] = kernel_blob
    image[rootfs_offset : rootfs_offset + len(rootfs_blob)] = rootfs_blob

    check_length = file_size - (FW_OFFSET + HEADER_LEN)
    struct.pack_into("<I", image, FW_OFFSET + 0x30, check_length)

    payload = image[FW_OFFSET + HEADER_LEN : file_size]
    byte_sum = sum(payload) & 0xFFFFFFFF
    primary = protect_crc_candidate(byte_sum, PROTECT2_SECRET_CANDIDATE, header)
    protect2 = protect_crc2_candidate(primary, PROTECT2_SECRET_CANDIDATE, header)
    struct.pack_into("<I", image, FW_OFFSET + 0x14, protect2)
    struct.pack_into("<I", image, FW_OFFSET + 0x34, primary)

    report = {
        "file_size": file_size,
        "kernel_size": len(kernel_blob),
        "kernel_sum": kernel_sum,
        "rootfs_size": len(rootfs_blob),
        "rootfs_offset": rootfs_offset,
        "requested_rootfs_offset": requested_rootfs_offset,
        "uimage_offset": uimage_offset,
        "uimage_kernel_end": uimage_kernel_end,
        "squashfs_input_offset": squashfs_offset,
        "payload_marker_offset": FW_OFFSET + HEADER_LEN,
        "cr6b_offset": CR6B_OFFSET,
        "check_length": check_length,
        "primary_checksum": primary,
        "protect2_checksum": protect2,
        "fits_8mb": file_size <= FLASH_SIZE,
    }
    return bytes(image), report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build an experimental CR6B-style A2004MU candidate outside this repo."
    )
    parser.add_argument("--input-openwrt-sysupgrade", type=Path, required=True)
    parser.add_argument("--stock-firmware", type=Path, required=True)
    parser.add_argument("--sdk-candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rootfs-offset", default="auto")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    repo = Path.cwd()
    if not output_outside_repo(args.output, repo):
        parser.error("--output must be outside this repository")

    openwrt = require_file(parser, args.input_openwrt_sysupgrade, "--input-openwrt-sysupgrade")
    stock = require_file(parser, args.stock_firmware, "--stock-firmware")
    template = require_file(parser, args.sdk_candidate, "--sdk-candidate") if args.sdk_candidate else stock

    image, report = build_image(
        stock.read_bytes(),
        template.read_bytes(),
        openwrt.read_bytes(),
        args.rootfs_offset,
    )

    output = args.output.expanduser()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)
    self_check = self_check_output(output, image)

    result = {
        "status": "written",
        "warning": "EXPERIMENTAL OUTPUT ONLY; not web-admin tested; not hardware validated",
        "input_openwrt_sysupgrade": str(openwrt),
        "stock_firmware": str(stock),
        "template": str(template),
        "output": {
            "path": str(output),
            "file_size": len(image),
            "sha256": hashlib.sha256(image).hexdigest(),
        },
        "layout": report,
        "self_check": self_check,
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("WARNING: EXPERIMENTAL OUTPUT ONLY; not web-admin tested; not hardware validated")
        print(f"output: {output}")
        print(f"file size: {len(image)} bytes (0x{len(image):x})")
        print(f"sha256: {sha256_bytes(image)}")
        print(f"kernel size: {report['kernel_size']} bytes (0x{report['kernel_size']:x})")
        print(f"rootfs size: {report['rootfs_size']} bytes (0x{report['rootfs_size']:x})")
        print(f"rootfs offset: 0x{report['rootfs_offset']:x}")
        print(f"payload marker offset: 0x{report['payload_marker_offset']:x}")
        print(f"cr6b offset: 0x{report['cr6b_offset']:x}")
        print(f"SquashFS input offset: 0x{report['squashfs_input_offset']:x}")
        print(f"self-check status: {self_check['status']}")
        print(f"self-check all matched: {'yes' if self_check['matches']['all'] else 'no'}")

    return 0 if self_check["matches"]["all"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
