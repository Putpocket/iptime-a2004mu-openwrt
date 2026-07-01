#!/usr/bin/env python3
"""Analyze observed A2004MU kernel descriptor and CR6B payload structure."""

from __future__ import annotations

import argparse
import hashlib
import lzma
import struct
from pathlib import Path

from verify_iptime_checksum import (
    PROTECT2_MAGIC,
    PROTECT2_SECRET_CANDIDATE,
    build_result,
    protect_crc2_candidate,
    protect_crc_candidate,
    read_header,
)


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
KDESC_LEN = 0x10
KDESC_OFFSET = FW_OFFSET + HEADER_LEN
CR6B_OFFSET = KDESC_OFFSET + KDESC_LEN
FLASH_SIZE = 0x800000
DEFAULT_UPDATER_SKIP_OFFSET = 0x400C0
WEB_ADMIN_BODY_OFFSET = FW_OFFSET
WEB_ADMIN_HEADER_OFFSET = FW_OFFSET - HEADER_LEN
WEB_ADMIN_LZMA_OFFSET = 0x27A0
BODY_HEADER_LEN = 0x38
BODY_KDESC_OFFSET = BODY_HEADER_LEN
BODY_CR6B_OFFSET = BODY_HEADER_LEN + KDESC_LEN
MAGICS = {
    "lzma_alone_stock": b"\x5d\x00\x00\x80\x00",
    "lzma_alone_openwrt": b"\x6d\x00\x00\x80\x00",
    "gzip": b"\x1f\x8b",
    "xz": b"\xfd7zXZ\x00",
    "kernel": b"kernel",
    "cr6b": b"cr6b",
    "cs6c": b"cs6c",
    "hsqs": b"hsqs",
    "uImage": b"\x27\x05\x19\x56",
}


def u32le(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, offset)[0]


def u32be(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from(">I", data, offset)[0]


def find_all(data: bytes, marker: bytes) -> list[int]:
    offsets = []
    start = 0
    while True:
        offset = data.find(marker, start)
        if offset < 0:
            return offsets
        offsets.append(offset)
        start = offset + 1


def checksum_status_at(path: Path, data: bytes, header_offset: int) -> str:
    if header_offset == FW_OFFSET:
        try:
            header = read_header(data)
            result, _ = build_result(path, data, hashlib.sha256(data).hexdigest(), header)
        except ValueError as exc:
            return f"unavailable: {exc}"
        return "MATCH" if result["matches"]["all"] else "MISMATCH"
    if len(data) < header_offset + HEADER_LEN:
        return "unavailable: header range exceeds file size"
    model_raw = data[header_offset : header_offset + 8]
    magic = u32le(data, header_offset + 0x10)
    protect2 = u32le(data, header_offset + 0x14)
    check_length = u32le(data, header_offset + 0x30)
    primary = u32le(data, header_offset + 0x34)
    if None in (magic, protect2, check_length, primary):
        return "unavailable: truncated header"
    payload_start = header_offset + HEADER_LEN
    payload_end = payload_start + check_length
    if payload_end > len(data):
        return "unavailable: payload range exceeds file size"
    byte_sum = sum(data[payload_start:payload_end]) & 0xFFFFFFFF
    primary_candidate = protect_crc_candidate(byte_sum, PROTECT2_SECRET_CANDIDATE, model_raw)
    protect2_candidate = protect_crc2_candidate(primary_candidate, PROTECT2_SECRET_CANDIDATE, model_raw)
    matched = (
        magic == PROTECT2_MAGIC
        and primary_candidate == primary
        and protect2_candidate == protect2
    )
    return "MATCH" if matched else "MISMATCH"


def checksum_status(path: Path, data: bytes) -> str:
    try:
        header = read_header(data)
        result, _ = build_result(path, data, hashlib.sha256(data).hexdigest(), header)
    except ValueError as exc:
        return f"unavailable: {exc}"
    return "MATCH" if result["matches"]["all"] else "MISMATCH"


def known_values(data: bytes, base_offset: int = 0) -> dict[str, int]:
    size = len(data)
    rootfs = data.find(MAGICS["hsqs"])
    cr6b = data.find(MAGICS["cr6b"])
    kdesc = data.find(b"kernel\x00\x00")
    values = {
        "file_size": size,
        "flash_size": FLASH_SIZE,
        "payload_start": base_offset + BODY_KDESC_OFFSET if base_offset else KDESC_OFFSET,
        "cr6b_offset": cr6b,
        "kernel_descriptor_offset": kdesc,
    }
    if rootfs >= 0:
        values["rootfs_offset"] = rootfs
        values["rootfs_size"] = size - rootfs
    if cr6b >= 0:
        values["kernel_region_size"] = (rootfs if rootfs >= 0 else size) - cr6b
        values["cr6b_relative_rootfs_offset"] = rootfs - cr6b if rootfs >= 0 else -1
    if kdesc >= 0:
        length = u32le(data, kdesc + 8)
        checksum = u32le(data, kdesc + 12)
        if length is not None:
            values["descriptor_kernel_size"] = length
            values["cr6b_body_size"] = max(0, length - KDESC_LEN)
        if checksum is not None:
            values["descriptor_kernel_sum"] = checksum
    return values


def labels_for(value: int, known: dict[str, int]) -> str:
    labels = [name for name, candidate in known.items() if candidate == value and value >= 0]
    return ",".join(labels) if labels else "-"



def looks_like_mips_code(data: bytes, offset: int = 0) -> bool:
    if offset + 16 > len(data):
        return False
    words = [u32be(data, offset + i) for i in range(0, 16, 4)]
    if any(word is None for word in words):
        return False
    opcodes = [(word >> 26) & 0x3f for word in words if word is not None]
    return any(op in {0x02, 0x03, 0x04, 0x05, 0x08, 0x09, 0x0f, 0x23, 0x2b} for op in opcodes)


def lzma_details(data: bytes, offset: int, end: int | None = None) -> dict:
    details = {
        "ok": False,
        "props": None,
        "header_uncompressed_size": None,
        "actual_uncompressed_size": None,
        "consumed": None,
        "unused": None,
        "eof": False,
        "error": None,
    }
    if offset < 0:
        details["error"] = "unavailable"
        return details
    payload = data[offset:end] if end is not None and end > offset else data[offset:]
    details["props"] = payload[:5].hex() if len(payload) >= 5 else payload.hex()
    if len(payload) >= 13:
        details["header_uncompressed_size"] = struct.unpack_from("<Q", payload, 5)[0]
    try:
        decompressor = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        out = decompressor.decompress(payload)
    except lzma.LZMAError as exc:
        details["error"] = str(exc)
        return details
    consumed = len(payload) - len(decompressor.unused_data)
    details.update(
        {
            "ok": True,
            "actual_uncompressed_size": len(out),
            "consumed": consumed,
            "unused": len(decompressor.unused_data),
            "eof": decompressor.eof,
        }
    )
    return details


def lzma_status(data: bytes, offset: int, end: int | None = None) -> str:
    details = lzma_details(data, offset, end)
    if not details["ok"]:
        return f"FAIL props={details['props']} error={details['error']}"
    eof = "yes" if details["eof"] else "no"
    return (
        f"OK props={details['props']} "
        f"header_uncompressed_size=0x{details['header_uncompressed_size']:x} "
        f"actual_uncompressed_size=0x{details['actual_uncompressed_size']:x} "
        f"consumed=0x{details['consumed']:x} unused=0x{details['unused']:x} eof={eof}"
    )


def value_hits(data: bytes, value: int) -> list[str]:
    hits = []
    for endian, fmt in (("le", "<I"), ("be", ">I")):
        needle = struct.pack(fmt, value & 0xFFFFFFFF)
        start = 0
        while True:
            offset = data.find(needle, start)
            if offset < 0:
                break
            hits.append(f"{endian}@0x{offset:x}")
            start = offset + 1
    return hits


def print_hexdump_line(label: str, data: bytes, offset: int, length: int = 64) -> None:
    if offset >= len(data):
        print(f"{label} 0x{offset:x} unavailable")
        return
    print(f"{label} 0x{offset:x} {data[offset:offset+length].hex(' ')}")

def print_magic_offsets(data: bytes, prefix: str = "") -> None:
    for name, marker in MAGICS.items():
        offsets = find_all(data, marker)
        if offsets:
            rendered = " ".join(f"0x{x:x}" for x in offsets[:8])
            suffix = "" if len(offsets) <= 8 else f" ... ({len(offsets)} total)"
            print(f"{prefix}{name}_offsets {rendered}{suffix}")
        else:
            print(f"{prefix}{name}_offsets none")


def print_cr6b_words(data: bytes, cr6b: int, known: dict[str, int], absolute_base: int = 0) -> None:
    print("cr6b_words offset rel hex le32 le_match be32 be_match")
    limit = min(cr6b + 0x100, len(data))
    for off in range(cr6b, limit, 4):
        word = data[off : off + 4]
        le = u32le(data, off)
        be = u32be(data, off)
        print(
            f"0x{absolute_base + off:08x} +0x{off - cr6b:03x} {word.hex()} "
            f"0x{le:08x} {labels_for(le, known)} "
            f"0x{be:08x} {labels_for(be, known)}"
        )


def print_file(
    path: Path,
    updater_skip_offset: int,
    contract_check: bool = False,
    header_offset: int = FW_OFFSET,
    expected_lzma_offset: int | None = None,
) -> bool:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    known = known_values(data)

    print(f"FILE {path}")
    print(f"size {len(data)} 0x{len(data):x}")
    print(f"sha256 {digest}")
    print(f"fits_8mb {'yes' if len(data) <= FLASH_SIZE else 'no'}")
    print(f"checksum {checksum_status_at(path, data, header_offset)}")
    print(f"checksum_header_offset 0x{header_offset:x}")

    print_magic_offsets(data)

    kdesc = known.get("kernel_descriptor_offset", -1)
    if kdesc >= 0 and kdesc + KDESC_LEN <= len(data):
        marker = data[kdesc : kdesc + 8]
        length = u32le(data, kdesc + 8)
        checksum = u32le(data, kdesc + 12)
        actual_sum = None
        if length is not None and CR6B_OFFSET + length <= len(data):
            actual_sum = sum(data[CR6B_OFFSET : CR6B_OFFSET + length]) & 0xFFFFFFFF
        print(
            "kernel_descriptor "
            f"offset=0x{kdesc:x} marker={marker!r} "
            f"length=0x{length:x} checksum=0x{checksum:08x} "
            f"actual_sum={('0x%08x' % actual_sum) if actual_sum is not None else 'n/a'}"
        )

    cr6b = known.get("cr6b_offset", -1)
    if cr6b >= 0:
        print_cr6b_words(data, cr6b, known)

    print("flash_body_analysis")
    print(f"updater_skip_offset 0x{updater_skip_offset:x}")
    if len(data) <= updater_skip_offset:
        print("flash_body unavailable: file smaller than updater skip offset")
        print()
        return not contract_check

    body = data[updater_skip_offset:]
    body_known = known_values(body, updater_skip_offset)
    print(f"upload_file_size {len(data)} 0x{len(data):x}")
    print(f"flash_body_size {len(body)} 0x{len(body):x}")
    print(f"flash_body_fits_8mb {'yes' if len(body) <= FLASH_SIZE else 'no'}")
    print(f"flash_body_check_firmware_size_candidate {len(body)} 0x{len(body):x}")
    print_hexdump_line("flash_body_entry_bytes", body, 0, 64)
    print_hexdump_line("flash_body_offset_0x38_bytes", body, 0x38, 64)
    print_hexdump_line("flash_body_offset_0x48_bytes", body, 0x48, 64)
    print_hexdump_line("flash_body_offset_0x100_bytes", body, 0x100, 64)
    print_hexdump_line("flash_body_offset_0x1000_bytes", body, 0x1000, 64)
    print_hexdump_line("flash_body_offset_0x10000_bytes", body, 0x10000, 64)
    print(f"flash_body_entry_code_heuristic {'yes' if looks_like_mips_code(body, 0) else 'no'}")
    if body.startswith(b'a2004m') or body.startswith(b'kernel') or body.startswith(MAGICS["cr6b"]):
        print("flash_body_entry_warning metadata_at_entry")
    elif not looks_like_mips_code(body, 0):
        print("flash_body_entry_warning not_obviously_mips_code")
    else:
        print("flash_body_entry_warning none")
    print_magic_offsets(body, "flash_body_")
    body_kdesc_probe = body.find(b"kernel\x00\x00")
    body_cr6b_probe = body.find(MAGICS["cr6b"])
    body_squashfs_probe = body.find(MAGICS["hsqs"])
    body_lzma_openwrt = body.find(MAGICS["lzma_alone_openwrt"])
    body_lzma_stock = body.find(MAGICS["lzma_alone_stock"])
    cr6b_structure_pass = (
        body_kdesc_probe == BODY_KDESC_OFFSET
        and body_cr6b_probe == BODY_CR6B_OFFSET
        and body_squashfs_probe >= 0
        and body_squashfs_probe % 0x10000 == 0
    )
    stock_lzma_offset = body_lzma_stock if body_lzma_stock >= 0 else body_lzma_openwrt
    stock_loader_lzma_ok = stock_lzma_offset >= 0 and lzma_status(
        body,
        stock_lzma_offset,
        body_squashfs_probe if body_squashfs_probe >= 0 else None,
    ).startswith("OK ")
    stock_loader_structure_pass = (
        looks_like_mips_code(body, 0)
        and body_kdesc_probe != 0
        and body_cr6b_probe != 0
        and stock_loader_lzma_ok
        and body_squashfs_probe >= 0
    )
    if cr6b_structure_pass:
        print("flash_body_structure PASS cr6b-body")
    elif stock_loader_structure_pass:
        print("flash_body_structure PASS stock-loader")
    else:
        print("flash_body_structure WARN")

    body_kdesc = body_kdesc_probe
    if body_kdesc >= 0 and body_kdesc + KDESC_LEN <= len(body):
        marker = body[body_kdesc : body_kdesc + 8]
        length = u32le(body, body_kdesc + 8)
        checksum = u32le(body, body_kdesc + 12)
        body_cr6b = body.find(MAGICS["cr6b"])
        actual_sum = None
        if body_cr6b >= 0 and length is not None and body_cr6b + length <= len(body):
            actual_sum = sum(body[body_cr6b : body_cr6b + length]) & 0xFFFFFFFF
        print(
            "flash_body_kernel_descriptor "
            f"body_offset=0x{body_kdesc:x} file_offset=0x{updater_skip_offset + body_kdesc:x} "
            f"marker={marker!r} length=0x{length:x} checksum=0x{checksum:08x} "
            f"actual_sum={('0x%08x' % actual_sum) if actual_sum is not None else 'n/a'}"
        )

    body_cr6b = body.find(MAGICS["cr6b"])
    if body_cr6b >= 0:
        print(f"flash_body_cr6b body_offset=0x{body_cr6b:x} file_offset=0x{updater_skip_offset + body_cr6b:x}")
        print_cr6b_words(body, body_cr6b, body_known, updater_skip_offset)

    lzma_offsets = [
        offset
        for offset in (body_lzma_stock, body_lzma_openwrt)
        if offset >= 0
    ]
    body_rootfs = body.find(MAGICS["hsqs"])
    for offset in sorted(set(lzma_offsets)):
        print(
            "flash_body_lzma "
            f"body_offset=0x{offset:x} file_offset=0x{updater_skip_offset + offset:x} "
            f"{lzma_status(body, offset, body_rootfs if body_rootfs >= 0 else None)}"
        )

    contract_pass = True
    if contract_check:
        lzma_offset = body_lzma_stock if body_lzma_stock >= 0 else body_lzma_openwrt
        details = lzma_details(body, lzma_offset, body_rootfs if body_rootfs >= 0 else None)
        compressed_size = details["consumed"] if details["ok"] else None
        checks = {
            "loader_entry_code": looks_like_mips_code(body, 0),
            "lzma_payload_found": lzma_offset >= 0,
            "lzma_payload_expected_offset": expected_lzma_offset is None or lzma_offset == expected_lzma_offset,
            "lzma_props_stock": details["props"] == MAGICS["lzma_alone_stock"].hex(),
            "lzma_decodes": details["ok"],
            "lzma_header_size_matches_actual": details["ok"]
            and details["header_uncompressed_size"] == details["actual_uncompressed_size"],
            "compressed_payload_end_before_rootfs": details["ok"]
            and body_rootfs >= 0
            and lzma_offset + details["consumed"] <= body_rootfs,
            "squashfs_found": body_rootfs >= 0,
        }
        contract_pass = all(checks.values())
        print(f"contract_status {'PASS' if contract_pass else 'FAIL'}")
        for name, passed in checks.items():
            print(f"contract_{name} {'PASS' if passed else 'FAIL'}")
        if details["ok"]:
            loader_prefix = body[:lzma_offset]
            candidates = {
                "compressed_size": compressed_size,
                "uncompressed_size": details["actual_uncompressed_size"],
                "payload_offset": lzma_offset,
                "load_address": 0x80A00000,
                "flash_offset": 0x40000,
            }
            for name, value in candidates.items():
                if value is None:
                    continue
                hits = value_hits(loader_prefix, value)
                rendered = " ".join(hits[:16]) if hits else "none"
                print(f"contract_loader_field_hits {name}=0x{value:x} {rendered}")

    print()
    return contract_pass or not contract_check


def main() -> int:
    parser = argparse.ArgumentParser(description="Analyze A2004MU CR6B candidate structure.")
    parser.add_argument("--updater-skip-offset", "--skip-offset", default=hex(DEFAULT_UPDATER_SKIP_OFFSET))
    parser.add_argument("--path-mode", choices=("explicit", "web-admin"), default="explicit")
    parser.add_argument("--contract-check", action="store_true")
    parser.add_argument("paths", type=Path, nargs="+")
    args = parser.parse_args()
    if args.path_mode == "web-admin":
        updater_skip_offset = WEB_ADMIN_BODY_OFFSET
        header_offset = WEB_ADMIN_HEADER_OFFSET
        expected_lzma_offset = WEB_ADMIN_LZMA_OFFSET
    else:
        updater_skip_offset = int(args.updater_skip_offset, 0)
        header_offset = FW_OFFSET
        expected_lzma_offset = None

    ok = True
    for path in args.paths:
        if not path.is_file():
            parser.error(f"not a file: {path}")
        ok = print_file(path, updater_skip_offset, args.contract_check, header_offset, expected_lzma_offset) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
