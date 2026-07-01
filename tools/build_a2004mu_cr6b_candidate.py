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
UPDATER_SKIP_OFFSET = 0x400C2
BODY_HEADER_OFFSET = 0
BODY_KDESC_OFFSET = HEADER_LEN
BODY_CR6B_OFFSET = HEADER_LEN + KDESC_LEN
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
        raise ValueError("template does not contain kernel descriptor at upload offset 0x40038")
    if data[CR6B_OFFSET : CR6B_OFFSET + 4] != b"cr6b":
        raise ValueError("template does not contain cr6b at upload offset 0x40048")
    return bytearray(data[FW_OFFSET : FW_OFFSET + HEADER_LEN]), data[CR6B_OFFSET : CR6B_OFFSET + 0x10]


def fill_iptime_header(image: bytearray, header_offset: int, check_start: int, check_end: int, rootfs_offset: int) -> tuple[int, int, int]:
    struct.pack_into("<I", image, header_offset + 0x10, PROTECT2_MAGIC)
    struct.pack_into("<I", image, header_offset + 0x14, 0)
    struct.pack_into("<I", image, header_offset + 0x2C, rootfs_offset)
    struct.pack_into("<I", image, header_offset + 0x30, check_end - check_start)
    struct.pack_into("<I", image, header_offset + 0x34, 0)

    payload = image[check_start:check_end]
    byte_sum = sum(payload) & 0xFFFFFFFF
    primary = protect_crc_candidate(byte_sum, PROTECT2_SECRET_CANDIDATE, image[header_offset : header_offset + 8])
    protect2 = protect_crc2_candidate(primary, PROTECT2_SECRET_CANDIDATE, image[header_offset : header_offset + 8])
    struct.pack_into("<I", image, header_offset + 0x14, protect2)
    struct.pack_into("<I", image, header_offset + 0x34, primary)
    return check_end - check_start, primary, protect2


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
    cr6b_header = bytearray(cr6b_template)
    struct.pack_into(">I", cr6b_header, 0x0C, len(kernel_body))
    kernel_blob = bytes(cr6b_header) + kernel_body

    requested_rootfs_offset = None
    if rootfs_offset_arg == "auto":
        rootfs_offset = struct.unpack_from("<I", template_data, FW_OFFSET + 0x2C)[0]
    else:
        rootfs_offset = int(rootfs_offset_arg, 0)
        requested_rootfs_offset = rootfs_offset

    min_rootfs_offset = align_up(BODY_CR6B_OFFSET + len(kernel_blob), 0x10000)
    if rootfs_offset < min_rootfs_offset:
        if requested_rootfs_offset is not None:
            raise ValueError(
                "requested flash-body rootfs offset overlaps kernel: "
                f"requested=0x{requested_rootfs_offset:x} minimum=0x{min_rootfs_offset:x}"
            )
        rootfs_offset = min_rootfs_offset

    body_size = rootfs_offset + len(rootfs_blob)
    file_size = UPDATER_SKIP_OFFSET + body_size
    if body_size > FLASH_SIZE:
        raise ValueError(f"planned flash body exceeds 8MB flash: 0x{body_size:x}")
    if file_size <= UPDATER_SKIP_OFFSET:
        raise ValueError("planned output has empty flash body")
    if len(stock_data) < UPDATER_SKIP_OFFSET:
        raise ValueError("stock firmware is too small for updater prefix copy")

    image = bytearray(stock_data[:UPDATER_SKIP_OFFSET])
    image.extend(b"\x00" * body_size)

    body_start = UPDATER_SKIP_OFFSET
    body_end = body_start + body_size
    body_header_offset = body_start + BODY_HEADER_OFFSET
    body_kdesc_offset = body_start + BODY_KDESC_OFFSET
    body_cr6b_offset = body_start + BODY_CR6B_OFFSET
    body_rootfs_offset = body_start + rootfs_offset

    image[body_header_offset : body_header_offset + HEADER_LEN] = header

    kernel_sum = sum(kernel_blob) & 0xFFFFFFFF
    descriptor = KERNEL_MARKER + struct.pack("<I", len(kernel_blob)) + struct.pack("<I", kernel_sum)

    image[body_kdesc_offset : body_kdesc_offset + KDESC_LEN] = descriptor
    image[body_cr6b_offset : body_cr6b_offset + len(kernel_blob)] = kernel_blob
    image[body_rootfs_offset : body_rootfs_offset + len(rootfs_blob)] = rootfs_blob

    body_check_length, body_primary, body_protect2 = fill_iptime_header(
        image,
        body_header_offset,
        body_kdesc_offset,
        body_end,
        rootfs_offset,
    )

    # The web updater still validates the upload header at 0x40000. Keep that
    # header valid for the whole uploaded file while placing a second valid
    # header at the flash body start that the bootloader will see after the
    # updater skips 0x400c2 bytes.
    image[FW_OFFSET : FW_OFFSET + HEADER_LEN] = header
    upload_check_length, upload_primary, upload_protect2 = fill_iptime_header(
        image,
        FW_OFFSET,
        FW_OFFSET + HEADER_LEN,
        file_size,
        rootfs_offset,
    )

    report = {
        "file_size": file_size,
        "updater_skip_offset": UPDATER_SKIP_OFFSET,
        "flash_body_size": body_size,
        "kernel_size": len(kernel_blob),
        "kernel_sum": kernel_sum,
        "rootfs_size": len(rootfs_blob),
        "rootfs_offset": rootfs_offset,
        "requested_rootfs_offset": requested_rootfs_offset,
        "uimage_offset": uimage_offset,
        "uimage_kernel_end": uimage_kernel_end,
        "squashfs_input_offset": squashfs_offset,
        "payload_marker_offset": body_kdesc_offset,
        "cr6b_offset": body_cr6b_offset,
        "flash_body_payload_marker_offset": BODY_KDESC_OFFSET,
        "flash_body_cr6b_offset": BODY_CR6B_OFFSET,
        "flash_body_squashfs_offset": rootfs_offset,
        "upload_check_length": upload_check_length,
        "upload_primary_checksum": upload_primary,
        "upload_protect2_checksum": upload_protect2,
        "body_check_length": body_check_length,
        "body_primary_checksum": body_primary,
        "body_protect2_checksum": body_protect2,
        "fits_8mb": body_size <= FLASH_SIZE,
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
        print(f"updater skip offset: 0x{report['updater_skip_offset']:x}")
        print(f"flash body size: {report['flash_body_size']} bytes (0x{report['flash_body_size']:x})")
        print(f"sha256: {sha256_bytes(image)}")
        print(f"kernel size: {report['kernel_size']} bytes (0x{report['kernel_size']:x})")
        print(f"rootfs size: {report['rootfs_size']} bytes (0x{report['rootfs_size']:x})")
        print(f"rootfs offset: 0x{report['rootfs_offset']:x}")
        print(f"payload marker file offset: 0x{report['payload_marker_offset']:x}")
        print(f"cr6b file offset: 0x{report['cr6b_offset']:x}")
        print(f"flash-body payload marker offset: 0x{report['flash_body_payload_marker_offset']:x}")
        print(f"flash-body cr6b offset: 0x{report['flash_body_cr6b_offset']:x}")
        print(f"SquashFS input offset: 0x{report['squashfs_input_offset']:x}")
        print(f"self-check status: {self_check['status']}")
        print(f"self-check all matched: {'yes' if self_check['matches']['all'] else 'no'}")

    return 0 if self_check["matches"]["all"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
