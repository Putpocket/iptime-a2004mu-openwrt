#!/usr/bin/env python3
"""Experimental ipTIME image writer guarded by dry-run planning checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path

from plan_iptime_wrapper import FLASH_SIZE, FW_OFFSET, HEADER_LEN, build_plan, require_file
from verify_iptime_checksum import (
    PROTECT2_MAGIC,
    PROTECT2_SECRET_CANDIDATE,
    build_result,
    protect_crc2_candidate,
    protect_crc_candidate,
    read_header,
)


WARNING = (
    "EXPERIMENTAL OUTPUT ONLY; NOT FLASH VERIFIED; "
    "requires independent validation"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def output_under_out(path: Path) -> bool:
    expanded = path.expanduser()
    if expanded.is_absolute():
        try:
            expanded.relative_to((Path.cwd() / "out").resolve())
            return True
        except ValueError:
            return False
    return bool(expanded.parts) and expanded.parts[0] == "out"


def refuse(message: str, plan: dict | None, json_mode: bool, code: int) -> int:
    if json_mode:
        print(
            json.dumps(
                {
                    "status": "refused",
                    "warning": WARNING,
                    "error": message,
                    "plan": plan,
                },
                indent=2,
                sort_keys=True,
            )
        )
    else:
        print(f"WARNING: {WARNING}")
        print(f"refusing to write: {message}")
    return code


def build_experimental_image(stock_data: bytes, sdk_data: bytes, plan: dict) -> bytes:
    layout = plan["layout"]
    proposed_size = layout["proposed_full_image_size"]
    if proposed_size > FLASH_SIZE:
        raise ValueError("planned output exceeds expected flash size")
    if not plan["sdk_image"]["squashfs_offsets"]:
        raise ValueError("cannot calculate rootfs offset without SDK SquashFS marker")

    payload_start = layout["proposed_payload_start"]
    rootfs_offset = payload_start + plan["sdk_image"]["squashfs_offsets"][0]
    check_length = len(sdk_data)

    image = bytearray(proposed_size)
    header = bytearray(stock_data[FW_OFFSET : FW_OFFSET + HEADER_LEN])

    struct.pack_into("<I", header, 0x10, PROTECT2_MAGIC)
    struct.pack_into("<I", header, 0x2C, rootfs_offset)
    struct.pack_into("<I", header, 0x30, check_length)
    struct.pack_into("<I", header, 0x34, 0)
    struct.pack_into("<I", header, 0x14, 0)

    image[FW_OFFSET : FW_OFFSET + HEADER_LEN] = header
    image[payload_start : payload_start + len(sdk_data)] = sdk_data

    byte_sum = sum(image[payload_start : payload_start + check_length]) & 0xFFFFFFFF
    primary = protect_crc_candidate(byte_sum, PROTECT2_SECRET_CANDIDATE, header)
    protect2 = protect_crc2_candidate(primary, PROTECT2_SECRET_CANDIDATE, header)

    struct.pack_into("<I", image, FW_OFFSET + 0x14, protect2)
    struct.pack_into("<I", image, FW_OFFSET + 0x30, check_length)
    struct.pack_into("<I", image, FW_OFFSET + 0x34, primary)
    return bytes(image)


def self_check_output(path: Path, data: bytes) -> dict:
    header = read_header(data)
    result, _ = build_result(path, data, sha256_bytes(data), header)
    return result


def print_text_success(report: dict) -> None:
    print(f"WARNING: {WARNING}")
    print("Generated experimental output under out/.")
    print(f"output: {report['output']['path']}")
    print(f"output size: {report['output']['file_size']} bytes (0x{report['output']['file_size']:x})")
    print(f"sha256: {report['output']['sha256']}")
    print(f"self-check status: {report['self_check']['status']}")
    print(f"self-check all matched: {'yes' if report['self_check']['matches']['all'] else 'no'}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create an experimental ipTIME A2004MU wrapper candidate. "
            "Default execution refuses to write."
        )
    )
    parser.add_argument("--stock", type=Path, required=True, help="Local stock firmware path")
    parser.add_argument("--sdk-image", type=Path, required=True, help="Local SDK AP-fw image path")
    parser.add_argument("--output", type=Path, required=True, help="Output path under out/")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only")
    parser.add_argument(
        "--force-experimental",
        action="store_true",
        help="Allow writing an experimental, not flash-verified output",
    )
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Allow writing when dry-run plan status is warning",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Allow replacing an existing output; still requires --force-experimental",
    )
    args = parser.parse_args()

    stock = require_file(parser, args.stock, "--stock")
    sdk_image = require_file(parser, args.sdk_image, "--sdk-image")
    output = args.output.expanduser()

    if not output_under_out(output):
        return refuse("--output must be under out/", None, args.json, 2)
    if output.exists() and output.is_dir():
        return refuse("--output is a directory", None, args.json, 2)

    plan = build_plan(stock, sdk_image)
    if plan["status"] == "error":
        return refuse("dry-run plan status is error", plan, args.json, 2)
    if plan["status"] == "warning" and not args.allow_warnings:
        return refuse("dry-run plan has warnings; pass --allow-warnings to continue", plan, args.json, 2)
    if not args.force_experimental:
        return refuse("pass --force-experimental to write experimental output", plan, args.json, 2)
    if output.exists() and not args.overwrite:
        return refuse("output already exists; pass --overwrite to replace it", plan, args.json, 2)

    stock_data = stock.read_bytes()
    sdk_data = sdk_image.read_bytes()
    try:
        image = build_experimental_image(stock_data, sdk_data, plan)
    except ValueError as exc:
        return refuse(str(exc), plan, args.json, 2)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(image)

    self_check = self_check_output(output, image)
    if not self_check["matches"]["all"]:
        output.unlink(missing_ok=True)
        return refuse("self-check did not match after writing; output removed", plan, args.json, 1)

    report = {
        "status": "written",
        "warning": WARNING,
        "plan": plan,
        "output": {
            "path": str(output),
            "file_size": len(image),
            "sha256": sha256_bytes(image),
        },
        "self_check": self_check,
    }

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text_success(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
