#!/usr/bin/env python3
"""Analyze A2004MU stock-loader LZMA/kernel-image contracts."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import struct
from pathlib import Path


FW_OFFSET = 0x40000
LZMA_OFFSET = 0x42860
BODY_LZMA_OFFSET = 0x2860
ROOTFS_OFFSET = 0x2C0000
HEADER_LEN = 0x38
KDESC_OFFSET = FW_OFFSET + HEADER_LEN
CR6B_OFFSET = KDESC_OFFSET + 0x10
STOCK_LOAD_ADDR = 0x80A00000
PROTECT2_MAGIC = 0x9A8F998B
PROTECT2_SECRET_CANDIDATE = 0x128A8392
SQUASHFS_MAGIC = b"hsqs"
LZMA_PROPS = b"\x5d\x00\x00\x80\x00"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def u32le(data: bytes, off: int) -> int:
    return struct.unpack_from("<I", data, off)[0]


def u32be(data: bytes, off: int) -> int:
    return struct.unpack_from(">I", data, off)[0]


def c_string(data: bytes) -> bytes:
    return data.split(b"\x00", 1)[0]


def u32(value: int) -> int:
    return value & 0xFFFFFFFF


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


def decode_lzma(data: bytes, off: int, limit: int | None = None) -> dict:
    payload = data[off:limit]
    result = {
        "offset": off,
        "header13": payload[:13].hex(),
        "props": payload[:5].hex() if len(payload) >= 5 else "",
        "dict": struct.unpack_from("<I", payload, 1)[0] if len(payload) >= 5 else None,
        "declared_uncompressed_size": struct.unpack_from("<Q", payload, 5)[0] if len(payload) >= 13 else None,
        "decode_ok": False,
    }
    try:
        dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        raw = dec.decompress(payload)
    except lzma.LZMAError as exc:
        result["error"] = str(exc)
        return result
    result["decode_ok"] = True
    result["decompressed"] = raw
    result["actual_uncompressed_size"] = len(raw)
    result["consumed"] = len(payload) - len(dec.unused_data)
    result["unused_len"] = len(dec.unused_data)
    result["unused_prefix"] = dec.unused_data[:32].hex(" ")
    result["eof"] = dec.eof
    return result


def first_nonzero(data: bytes) -> int:
    for i, b in enumerate(data):
        if b:
            return i
    return -1


def find_string(data: bytes, needle: bytes) -> int:
    return data.find(needle)


def mips_jump_target(word: int) -> int | None:
    op = word >> 26
    if op not in (0x02, 0x03):
        return None
    return (word & 0x03FFFFFF) << 2


def first_jump(data: bytes) -> dict | None:
    scan = min(len(data), 0x1000)
    for off in range(0, scan - 3, 4):
        le = u32le(data, off)
        be = u32be(data, off)
        for endian, word in (("le", le), ("be", be)):
            target = mips_jump_target(word)
            if target is not None:
                return {"offset": off, "endian": endian, "word": f"0x{word:08x}", "target_low": f"0x{target:08x}"}
    return None


def classify(name: str, data: bytes, decoded: dict) -> list[str]:
    classes: list[str] = []
    if not decoded.get("decode_ok"):
        classes.append("ENCODER_COMPAT_UNKNOWN")
        return classes
    raw = decoded["decompressed"]
    if name != "stock" and decoded.get("consumed") != u32le(data, FW_OFFSET + 0x40):
        classes.append("SIZE_CONTRACT_MISMATCH")
    first = first_nonzero(raw)
    if name != "stock" and first != 0x400:
        classes.append("IMAGE_LAYOUT_MISMATCH")
    jump = first_jump(raw)
    if name != "stock" and (not jump or jump.get("target_low") not in ("0x004c3f90", "0x00563230")):
        classes.append("ENTRYPOINT_MISMATCH")
    if not classes:
        classes.append("NO_LOCAL_CONTRACT_MISMATCH")
    return classes


def analyze_file(path: Path, name: str) -> dict:
    data = path.read_bytes()
    rootfs = data.find(SQUASHFS_MAGIC, FW_OFFSET)
    lz = decode_lzma(data, LZMA_OFFSET, rootfs if rootfs >= 0 else None)
    raw = lz.get("decompressed", b"")
    result = {
        "name": name,
        "path": str(path),
        "file_size": len(data),
        "sha256": sha256_bytes(data),
        "lzma_file_offset": LZMA_OFFSET,
        "lzma_body_offset": BODY_LZMA_OFFSET,
        "header_lzma_size_field": u32le(data, FW_OFFSET + 0x40),
        "cr6b_body_size_field": u32be(data, FW_OFFSET + 0x54),
        "header_lzma_size_minus_consumed": None,
        "cr6b_body_size_minus_consumed": None,
        "lzma_stream_limit": rootfs,
        "lzma_stream_padding_len_to_rootfs": None,
        "lzma_stream_padding_prefix": "",
        "lzma": {k: v for k, v in lz.items() if k != "decompressed"},
        "decompressed_first_nonzero": first_nonzero(raw) if raw else None,
        "decompressed_first_0x100": raw[:0x100].hex(" ") if raw else "",
        "linux_version_offset": find_string(raw, b"Linux version") if raw else -1,
        "console_offset": find_string(raw, b"console=") if raw else -1,
        "root_string_offset": find_string(raw, b"root=") if raw else -1,
        "first_jump": first_jump(raw) if raw else None,
        "normal_start_address_candidate": "0x804c3f90",
        "classes": [],
    }
    if lz.get("decode_ok"):
        result["header_lzma_size_minus_consumed"] = result["header_lzma_size_field"] - lz["consumed"]
        result["cr6b_body_size_minus_consumed"] = result["cr6b_body_size_field"] - lz["consumed"]
        result["lzma_stream_padding_len_to_rootfs"] = rootfs - (LZMA_OFFSET + lz["consumed"]) if rootfs >= 0 else None
        if rootfs >= 0:
            pad_start = LZMA_OFFSET + lz["consumed"]
            result["lzma_stream_padding_prefix"] = data[pad_start:pad_start + 32].hex(" ")
    result["classes"] = classify(name, data, lz)
    return result


def recompress_stock(stock: Path, output: Path) -> dict:
    data = bytearray(stock.read_bytes())
    rootfs = data.find(SQUASHFS_MAGIC, FW_OFFSET)
    if rootfs != ROOTFS_OFFSET:
        raise ValueError(f"stock rootfs offset mismatch: 0x{rootfs:x}")
    decoded = decode_lzma(data, LZMA_OFFSET, rootfs)
    if not decoded.get("decode_ok"):
        raise ValueError("stock LZMA did not decode")
    raw = decoded["decompressed"]
    filters = [{"id": lzma.FILTER_LZMA1, "dict_size": 0x800000, "lc": 3, "lp": 0, "pb": 2}]
    repacked = bytearray(lzma.compress(raw, format=lzma.FORMAT_ALONE, filters=filters))
    if not repacked.startswith(LZMA_PROPS):
        raise ValueError("repacked stock payload did not keep stock LZMA props")
    struct.pack_into("<Q", repacked, 5, len(raw))
    if LZMA_OFFSET + len(repacked) > ROOTFS_OFFSET:
        raise ValueError("repacked stock LZMA overlaps rootfs")
    old_range = ROOTFS_OFFSET - LZMA_OFFSET
    data[LZMA_OFFSET:ROOTFS_OFFSET] = b"\x00" * old_range
    data[LZMA_OFFSET:LZMA_OFFSET + len(repacked)] = repacked

    descriptor_len = (LZMA_OFFSET - CR6B_OFFSET) + len(repacked)
    cr6b_body_size = descriptor_len - 0x10
    struct.pack_into("<I", data, FW_OFFSET + 0x40, descriptor_len)
    struct.pack_into(">I", data, FW_OFFSET + 0x54, cr6b_body_size)
    checksum = sum(data[CR6B_OFFSET:CR6B_OFFSET + descriptor_len]) & 0xFFFFFFFF
    struct.pack_into("<I", data, FW_OFFSET + 0x44, checksum)

    payload_start = FW_OFFSET + HEADER_LEN
    check_length = u32le(data, FW_OFFSET + 0x30)
    payload_end = payload_start + check_length
    byte_sum = sum(data[payload_start:payload_end]) & 0xFFFFFFFF
    primary = protect_crc_candidate(byte_sum, PROTECT2_SECRET_CANDIDATE, data[FW_OFFSET:FW_OFFSET + 8])
    protect2 = protect_crc2_candidate(primary, PROTECT2_SECRET_CANDIDATE, data[FW_OFFSET:FW_OFFSET + 8])
    struct.pack_into("<I", data, FW_OFFSET + 0x10, PROTECT2_MAGIC)
    struct.pack_into("<I", data, FW_OFFSET + 0x14, protect2)
    struct.pack_into("<I", data, FW_OFFSET + 0x34, primary)

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    verify = decode_lzma(data, LZMA_OFFSET, ROOTFS_OFFSET)
    return {
        "path": str(output),
        "sha256": sha256_bytes(data),
        "file_size": len(data),
        "lzma_size": len(repacked),
        "decompressed_sha256_matches_stock": sha256_bytes(verify["decompressed"]) == sha256_bytes(raw),
        "python_lzma_decode": "PASS" if verify.get("decode_ok") else "FAIL",
        "kernel_checksum_field": f"0x{checksum:08x}",
        "total_checksum_field": f"0x{primary:08x}",
        "protect2_checksum_field": f"0x{protect2:08x}",
        "total_checksum": "PATCHED_WITH_OBSERVED_ALGORITHM",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stock", type=Path, required=True)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--make-stock-recompressed", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    output: dict = {"stock": analyze_file(args.stock, "stock")}
    if args.candidate:
        output["candidate"] = analyze_file(args.candidate, "candidate")
    if args.make_stock_recompressed:
        output["stock_recompressed"] = recompress_stock(args.stock, args.make_stock_recompressed)

    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    else:
        for key, value in output.items():
            print(f"{key}:")
            print(json.dumps(value, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
