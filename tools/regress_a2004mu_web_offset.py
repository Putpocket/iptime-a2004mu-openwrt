#!/usr/bin/env python3
"""Validate the A2004MU web-updater multipart-prefix offset model."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38
STOCK_LOADER_START = b"\x00\x10\x08\x21"


@dataclass(frozen=True)
class Observation:
    path: Path
    offset: int


def parse_observation(value: str) -> Observation:
    if "=" not in value:
        raise argparse.ArgumentTypeError("expected PATH=OFFSET")
    path_text, offset_text = value.rsplit("=", 1)
    path = Path(path_text)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"not a file: {path}")
    return Observation(path, int(offset_text, 0))


def u32le(data: bytes, offset: int) -> int | None:
    if offset + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, offset)[0]


def row_for(obs: Observation) -> dict:
    data = obs.path.read_bytes()
    sha256 = hashlib.sha256(data).hexdigest()
    header = data[FW_OFFSET : FW_OFFSET + HEADER_LEN] if len(data) >= FW_OFFSET + HEADER_LEN else b""
    body = data[FW_OFFSET:] if len(data) >= FW_OFFSET else b""
    return {
        "path": str(obs.path),
        "observed_multipart_prefix": obs.offset,
        "observed_tmp_firmware_write_offset": FW_OFFSET + obs.offset,
        "candidate_internal_body_offset": FW_OFFSET,
        "expected_written_length": max(0, len(data) - FW_OFFSET),
        "body_starts_with_stock_loader": body.startswith(STOCK_LOADER_START),
        "size": len(data),
        "sha256": sha256,
        "header_rootfs_offset": u32le(data, FW_OFFSET + 0x2C),
        "header_check_length": u32le(data, FW_OFFSET + 0x30),
        "header_primary_checksum": u32le(data, FW_OFFSET + 0x34),
        "header_sum_mod256": sum(header) & 0xFF,
        "file_sum_mod256": sum(data) & 0xFF,
    }


def validate_multipart_model(rows: list[dict]) -> tuple[bool, list[str]]:
    errors = []
    for row in rows:
        if row["observed_tmp_firmware_write_offset"] != FW_OFFSET + row["observed_multipart_prefix"]:
            errors.append(f"write offset mismatch for {row['path']}")
        if row["size"] <= FW_OFFSET:
            errors.append(f"candidate too small for 0x40000 body offset: {row['path']}")
    return not errors, errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate observed A2004MU web-admin get_sys_params offsets as multipart prefixes."
    )
    parser.add_argument(
        "--observed",
        action="append",
        type=parse_observation,
        required=True,
        help="candidate path and observed low offset, for example /tmp/candidate.bin=0xc0",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    rows = [row_for(obs) for obs in args.observed]
    model_ok, errors = validate_multipart_model(rows)
    status = "pass" if model_ok else "fail"
    reason = None if model_ok else "; ".join(errors)

    result = {
        "status": status,
        "reason": reason,
        "rows": rows,
        "model": "observed offset is multipart/form-data prefix; candidate internal flash body offset is 0x40000",
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status {status}")
        if reason:
            print(f"reason {reason}")
        for row in rows:
            print(
                "row "
                f"multipart_prefix=0x{row['observed_multipart_prefix']:02x} "
                f"tmp_write=0x{row['observed_tmp_firmware_write_offset']:x} "
                f"candidate_body=0x{row['candidate_internal_body_offset']:x} "
                f"write_length=0x{row['expected_written_length']:x} "
                f"size=0x{row['size']:x} "
                f"sha256={row['sha256']} "
                f"path={row['path']}"
            )

    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
