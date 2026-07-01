#!/usr/bin/env python3
"""Check whether observed ipTIME web-updater offsets are file-predictable."""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path


FW_OFFSET = 0x40000
HEADER_LEN = 0x38


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
    return {
        "path": str(obs.path),
        "observed_get_sys_params_offset": obs.offset,
        "observed_updater_write_offset": FW_OFFSET + obs.offset,
        "size": len(data),
        "sha256": sha256,
        "header_rootfs_offset": u32le(data, FW_OFFSET + 0x2C),
        "header_check_length": u32le(data, FW_OFFSET + 0x30),
        "header_primary_checksum": u32le(data, FW_OFFSET + 0x34),
        "header_sum_mod256": sum(header) & 0xFF,
        "file_sum_mod256": sum(data) & 0xFF,
    }


def find_content_conflicts(rows: list[dict]) -> list[dict]:
    by_sha: dict[str, set[int]] = {}
    paths: dict[str, list[str]] = {}
    for row in rows:
        by_sha.setdefault(row["sha256"], set()).add(row["observed_get_sys_params_offset"])
        paths.setdefault(row["sha256"], []).append(row["path"])
    conflicts = []
    for digest, offsets in by_sha.items():
        if len(offsets) > 1:
            conflicts.append(
                {
                    "sha256": digest,
                    "observed_offsets": sorted(offsets),
                    "paths": paths[digest],
                }
            )
    return conflicts


def candidate_features(row: dict) -> dict[str, int]:
    features = {
        "size_mod256": row["size"] & 0xFF,
        "header_sum_mod256": row["header_sum_mod256"],
        "file_sum_mod256": row["file_sum_mod256"],
    }
    for key in ("header_rootfs_offset", "header_check_length", "header_primary_checksum"):
        value = row[key]
        if value is None:
            continue
        features[f"{key}_mod256"] = value & 0xFF
        features[f"{key}_byte1"] = (value >> 8) & 0xFF
        features[f"{key}_byte2"] = (value >> 16) & 0xFF
        features[f"{key}_byte3"] = (value >> 24) & 0xFF
    return features


def find_exact_predictors(rows: list[dict]) -> list[str]:
    if not rows:
        return []
    names = set(candidate_features(rows[0]))
    for row in rows[1:]:
        names &= set(candidate_features(row))

    predictors = []
    for name in sorted(names):
        if all(candidate_features(row)[name] == row["observed_get_sys_params_offset"] for row in rows):
            predictors.append(name)
    return predictors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Regress observed A2004MU web-admin get_sys_params offsets against candidate files."
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
    conflicts = find_content_conflicts(rows)
    exact_predictors = [] if conflicts else find_exact_predictors(rows)
    status = "pass" if exact_predictors else "fail"
    reason = None
    if conflicts:
        reason = "same file content produced different observed offsets"
    elif not exact_predictors:
        reason = "no exact file-content predictor found for supplied observations"

    result = {
        "status": status,
        "reason": reason,
        "rows": rows,
        "content_conflicts": conflicts,
        "exact_predictors": exact_predictors,
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
                f"offset=0x{row['observed_get_sys_params_offset']:02x} "
                f"write=0x{row['observed_updater_write_offset']:x} "
                f"size=0x{row['size']:x} "
                f"sha256={row['sha256']} "
                f"path={row['path']}"
            )
        for conflict in conflicts:
            offsets = ",".join(f"0x{x:02x}" for x in conflict["observed_offsets"])
            print(f"content_conflict sha256={conflict['sha256']} offsets={offsets}")
            for path in conflict["paths"]:
                print(f"content_conflict_path {path}")
        if exact_predictors:
            print("exact_predictors " + " ".join(exact_predictors))

    return 0 if status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
