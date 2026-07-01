#!/usr/bin/env python3
"""Build an experimental A2004MU ipTIME candidate with a CR6B-style payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
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
DEFAULT_UPDATER_SKIP_OFFSET = 0x400C0
BODY_HEADER_OFFSET = 0
BODY_KDESC_OFFSET = HEADER_LEN
BODY_CR6B_OFFSET = HEADER_LEN + KDESC_LEN
UIMAGE_MAGIC = b"\x27\x05\x19\x56"
SQUASHFS_MAGIC = b"hsqs"
KERNEL_MARKER = b"kernel\x00\x00"
STOCK_LZMA_MAGIC = b"\x5d\x00\x00\x80\x00"


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



def parse_int(value: str) -> int:
    return int(value, 0)


def find_stock_loader_end(stock_data: bytes, loader_source_offset: int) -> int:
    body = stock_data[loader_source_offset:]
    offset = body.find(STOCK_LZMA_MAGIC)
    if offset < 0:
        raise ValueError("stock flash body LZMA marker not found")
    return offset


def parse_lzma_props(props: bytes) -> tuple[int, int, int]:
    if len(props) != 5:
        raise ValueError("LZMA properties must be exactly 5 bytes")
    value = props[0]
    if value >= 9 * 5 * 5:
        raise ValueError(f"invalid LZMA property byte: 0x{value:02x}")
    lc = value % 9
    value //= 9
    lp = value % 5
    pb = value // 5
    dict_size = struct.unpack_from("<I", props, 1)[0]
    return lc, lp, pb, dict_size


def make_stock_compatible_lzma(kernel_body: bytes, props: bytes) -> tuple[bytes, int]:
    try:
        raw_kernel = lzma.decompress(kernel_body, format=lzma.FORMAT_ALONE)
    except lzma.LZMAError as exc:
        raise ValueError(f"OpenWrt uImage payload is not LZMA-alone decodable: {exc}") from exc
    lc, lp, pb, dict_size = parse_lzma_props(props)
    filters = [{"id": lzma.FILTER_LZMA1, "dict_size": dict_size, "lc": lc, "lp": lp, "pb": pb}]
    repacked = bytearray(lzma.compress(raw_kernel, format=lzma.FORMAT_ALONE, filters=filters))
    if not repacked.startswith(props):
        raise ValueError("repacked kernel does not use stock-compatible LZMA properties")
    struct.pack_into("<Q", repacked, 5, len(raw_kernel))
    return bytes(repacked), len(raw_kernel)


def lzma_contract_report(body: bytes, lzma_offset: int, rootfs_offset: int) -> tuple[bool, dict]:
    report = {
        "lzma_offset": lzma_offset,
        "rootfs_offset": rootfs_offset,
        "payload_end_before_rootfs": False,
        "props": None,
        "header_uncompressed_size": None,
        "actual_uncompressed_size": None,
        "compressed_payload_size": None,
        "status": "fail",
    }
    if lzma_offset < 0 or rootfs_offset <= lzma_offset:
        report["error"] = "invalid LZMA/rootfs offsets"
        return False, report
    payload = body[lzma_offset:rootfs_offset]
    if len(payload) < 13:
        report["error"] = "truncated LZMA header"
        return False, report
    report["props"] = payload[:5].hex()
    report["header_uncompressed_size"] = struct.unpack_from("<Q", payload, 5)[0]
    try:
        decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        raw = decompressor.decompress(payload)
    except lzma.LZMAError as exc:
        report["error"] = str(exc)
        return False, report
    consumed = len(payload) - len(decompressor.unused_data)
    report["actual_uncompressed_size"] = len(raw)
    report["compressed_payload_size"] = consumed
    report["payload_end_before_rootfs"] = lzma_offset + consumed <= rootfs_offset
    if report["header_uncompressed_size"] != len(raw):
        report["error"] = "LZMA header uncompressed size mismatch"
        return False, report
    if not decompressor.eof:
        report["error"] = "LZMA stream did not reach EOF"
        return False, report
    report["status"] = "pass"
    return True, report


def build_stock_loader_image(
    stock_data: bytes,
    template_data: bytes,
    openwrt_data: bytes,
    rootfs_offset_arg: str,
    updater_skip_offset: int,
    loader_source_offset: int,
    kernel_payload_mode: str,
    lzma_props: bytes,
    variant: str | None,
) -> tuple[bytes, dict]:
    kernel_body, uimage_offset, uimage_kernel_end = read_uimage_kernel(openwrt_data)
    original_kernel_body = kernel_body
    uncompressed_kernel_size = None
    if kernel_payload_mode == "stock-lzma":
        kernel_body, uncompressed_kernel_size = make_stock_compatible_lzma(kernel_body, lzma_props)
    elif kernel_payload_mode != "uimage-lzma":
        raise ValueError(f"unknown kernel payload mode: {kernel_payload_mode}")

    squashfs_offset = find_required(openwrt_data, SQUASHFS_MAGIC, "SquashFS")
    if squashfs_offset < uimage_kernel_end:
        raise ValueError("SquashFS marker overlaps uImage kernel")
    rootfs_blob = openwrt_data[squashfs_offset:]

    if len(stock_data) < updater_skip_offset:
        raise ValueError("stock firmware is too small for updater prefix copy")
    header, _ = read_template(template_data)
    if len(stock_data) < loader_source_offset:
        raise ValueError("stock firmware is too small for stock loader source offset")
    stock_body = stock_data[loader_source_offset:]
    loader_end = find_stock_loader_end(stock_data, loader_source_offset)
    loader_prefix = stock_body[:loader_end]

    requested_rootfs_offset = None
    if rootfs_offset_arg == "auto":
        stock_body_rootfs = stock_body.find(SQUASHFS_MAGIC)
        rootfs_offset = stock_body_rootfs if stock_body_rootfs >= 0 else struct.unpack_from("<I", template_data, FW_OFFSET + 0x2C)[0]
    else:
        rootfs_offset = int(rootfs_offset_arg, 0)
        requested_rootfs_offset = rootfs_offset

    min_rootfs_offset = len(loader_prefix) + len(kernel_body)
    if rootfs_offset < min_rootfs_offset:
        if requested_rootfs_offset is not None:
            raise ValueError(
                "requested flash-body rootfs offset overlaps stock-loader kernel payload: "
                f"requested=0x{requested_rootfs_offset:x} minimum=0x{min_rootfs_offset:x}"
            )
        rootfs_offset = min_rootfs_offset

    body_size = rootfs_offset + len(rootfs_blob)
    file_size = updater_skip_offset + body_size
    if body_size > FLASH_SIZE:
        raise ValueError(f"planned flash body exceeds 8MB flash: 0x{body_size:x}")

    image = bytearray(stock_data[:updater_skip_offset])
    image.extend(b"\x00" * body_size)

    body_start = updater_skip_offset
    body_end = body_start + body_size
    image[body_start : body_start + len(loader_prefix)] = loader_prefix
    image[body_start + loader_end : body_start + loader_end + len(kernel_body)] = kernel_body
    image[body_start + rootfs_offset : body_start + rootfs_offset + len(rootfs_blob)] = rootfs_blob
    contract_ok, contract = lzma_contract_report(
        bytes(image[body_start:body_end]),
        loader_end,
        rootfs_offset,
    )
    if not contract_ok:
        raise ValueError(f"stock-loader LZMA contract failed: {contract.get('error', 'unknown')}")

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
        "updater_skip_offset": updater_skip_offset,
        "stock_loader_source_offset": loader_source_offset,
        "flash_body_size": body_size,
        "variant": variant,
        "entry_layout": "stock-loader-raw-lzma",
        "kernel_payload_mode": kernel_payload_mode,
        "stock_loader_size": len(loader_prefix),
        "original_uimage_payload_size": len(original_kernel_body),
        "raw_kernel_payload_size": len(kernel_body),
        "uncompressed_kernel_size": uncompressed_kernel_size,
        "lzma_properties": kernel_body[:5].hex(),
        "lzma_header_uncompressed_size": struct.unpack_from("<Q", kernel_body, 5)[0] if len(kernel_body) >= 13 else None,
        "lzma_contract": contract,
        "rootfs_size": len(rootfs_blob),
        "rootfs_offset": rootfs_offset,
        "requested_rootfs_offset": requested_rootfs_offset,
        "uimage_offset": uimage_offset,
        "uimage_header_removed": True,
        "uimage_kernel_end": uimage_kernel_end,
        "squashfs_input_offset": squashfs_offset,
        "payload_marker_offset": body_start + loader_end,
        "cr6b_offset": None,
        "flash_body_payload_marker_offset": loader_end,
        "flash_body_cr6b_offset": None,
        "flash_body_squashfs_offset": rootfs_offset,
        "upload_check_length": upload_check_length,
        "upload_primary_checksum": upload_primary,
        "upload_protect2_checksum": upload_protect2,
        "fits_8mb": body_size <= FLASH_SIZE,
    }
    return bytes(image), report

def build_image(
    stock_data: bytes,
    template_data: bytes,
    openwrt_data: bytes,
    rootfs_offset_arg: str,
    updater_skip_offset: int,
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
    file_size = updater_skip_offset + body_size
    if body_size > FLASH_SIZE:
        raise ValueError(f"planned flash body exceeds 8MB flash: 0x{body_size:x}")
    if file_size <= updater_skip_offset:
        raise ValueError("planned output has empty flash body")
    if len(stock_data) < updater_skip_offset:
        raise ValueError("stock firmware is too small for updater prefix copy")

    image = bytearray(stock_data[:updater_skip_offset])
    image.extend(b"\x00" * body_size)

    body_start = updater_skip_offset
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
        "updater_skip_offset": updater_skip_offset,
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
    parser.add_argument(
        "--path-mode",
        choices=("explicit", "web-admin"),
        default="explicit",
        help="web-admin mode is disabled until get_sys_params offset prediction passes regression",
    )
    parser.add_argument("--entry-layout", choices=("stock-loader", "flash-body-cr6b"), default="stock-loader")
    parser.add_argument(
        "--updater-skip-offset",
        "--skip-offset",
        "--force-updater-skip",
        default=hex(DEFAULT_UPDATER_SKIP_OFFSET),
        help="file offset that the web updater is expected to skip before writing the flash body",
    )
    parser.add_argument("--variant")
    parser.add_argument("--loader-source-offset", default=hex(DEFAULT_UPDATER_SKIP_OFFSET))
    parser.add_argument("--lzma-props", default=STOCK_LZMA_MAGIC.hex())
    parser.add_argument(
        "--kernel-payload-mode",
        choices=("stock-lzma", "uimage-lzma"),
        default="stock-lzma",
        help="stock-lzma recompresses the OpenWrt kernel with stock-compatible LZMA properties",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    if args.path_mode == "web-admin":
        parser.error(
            "--path-mode web-admin requires a validated get_sys_params offset predictor; "
            "run tools/regress_a2004mu_web_offset.py first"
        )
    updater_skip_offset = parse_int(args.updater_skip_offset)
    loader_source_offset = parse_int(args.loader_source_offset)
    lzma_props = bytes.fromhex(args.lzma_props)

    repo = Path.cwd()
    if not output_outside_repo(args.output, repo):
        parser.error("--output must be outside this repository")

    openwrt = require_file(parser, args.input_openwrt_sysupgrade, "--input-openwrt-sysupgrade")
    stock = require_file(parser, args.stock_firmware, "--stock-firmware")
    template = require_file(parser, args.sdk_candidate, "--sdk-candidate") if args.sdk_candidate else stock

    stock_data = stock.read_bytes()
    template_data = template.read_bytes()
    openwrt_data = openwrt.read_bytes()
    if args.entry_layout == "stock-loader":
        image, report = build_stock_loader_image(
            stock_data,
            template_data,
            openwrt_data,
            args.rootfs_offset,
            updater_skip_offset,
            loader_source_offset,
            args.kernel_payload_mode,
            lzma_props,
            args.variant,
        )
    else:
        image, report = build_image(
            stock_data,
            template_data,
            openwrt_data,
            args.rootfs_offset,
            updater_skip_offset,
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
        if "kernel_size" in report:
            print(f"kernel size: {report['kernel_size']} bytes (0x{report['kernel_size']:x})")
        if "stock_loader_size" in report:
            print(f"stock loader size: {report['stock_loader_size']} bytes (0x{report['stock_loader_size']:x})")
            print(f"kernel payload mode: {report['kernel_payload_mode']}")
            if report.get("variant"):
                print(f"variant: {report['variant']}")
            if report.get("uncompressed_kernel_size") is not None:
                print(
                    "uncompressed kernel size: "
                    f"{report['uncompressed_kernel_size']} bytes (0x{report['uncompressed_kernel_size']:x})"
                )
            print(f"LZMA properties: {report['lzma_properties']}")
            print(f"LZMA header uncompressed size: 0x{report['lzma_header_uncompressed_size']:x}")
            print(f"LZMA contract: {report['lzma_contract']['status']}")
            print(f"raw kernel payload size: {report['raw_kernel_payload_size']} bytes (0x{report['raw_kernel_payload_size']:x})")
        print(f"rootfs size: {report['rootfs_size']} bytes (0x{report['rootfs_size']:x})")
        print(f"rootfs offset: 0x{report['rootfs_offset']:x}")
        print(f"payload marker file offset: 0x{report['payload_marker_offset']:x}")
        if report.get("cr6b_offset") is not None:
            print(f"cr6b file offset: 0x{report['cr6b_offset']:x}")
        else:
            print("cr6b file offset: none")
        print(f"flash-body payload marker offset: 0x{report['flash_body_payload_marker_offset']:x}")
        if report.get("flash_body_cr6b_offset") is not None:
            print(f"flash-body cr6b offset: 0x{report['flash_body_cr6b_offset']:x}")
        else:
            print("flash-body cr6b offset: none")
        print(f"SquashFS input offset: 0x{report['squashfs_input_offset']:x}")
        print(f"self-check status: {self_check['status']}")
        print(f"self-check all matched: {'yes' if self_check['matches']['all'] else 'no'}")

    return 0 if self_check["matches"]["all"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
