#!/usr/bin/env python3
"""Conservative skeleton for future experimental ipTIME image wrapping."""

from __future__ import annotations

import argparse
from pathlib import Path


WARNING = """
WARNING: EXPERIMENTAL OUTPUT ONLY

This tool is a conservative skeleton. The generated file is not flash-verified.
Header generation, checksum behavior, partition offsets, boot behavior, and
recovery behavior must be independently validated before any device write is
considered.

Do not claim output from this tool is safe to flash.
"""


def require_file(parser: argparse.ArgumentParser, path: Path, label: str) -> Path:
    resolved = path.expanduser()
    if not resolved.is_file():
        parser.error(f"{label} is not a file: {resolved}")
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Skeleton for an experimental ipTIME A2004MU image wrapper."
    )
    parser.add_argument("--stock", type=Path, required=True, help="Local stock firmware path")
    parser.add_argument("--sdk-image", type=Path, required=True, help="Local SDK AP-fw image path")
    parser.add_argument("--output", type=Path, required=True, help="Output path")
    parser.add_argument(
        "--force-experimental",
        action="store_true",
        help="Allow writing an explicitly experimental, not flash-verified output",
    )
    args = parser.parse_args()

    stock = require_file(parser, args.stock, "--stock")
    sdk_image = require_file(parser, args.sdk_image, "--sdk-image")
    output = args.output.expanduser()

    print(WARNING.strip())
    print()
    print(f"stock input: {stock}")
    print(f"sdk image input: {sdk_image}")
    print(f"output: {output}")
    print()

    if not args.force_experimental:
        print("refusing to write: pass --force-experimental to create placeholder output")
        return 2

    if output.exists() and output.is_dir():
        parser.error(f"--output is a directory: {output}")

    output.parent.mkdir(parents=True, exist_ok=True)

    # Placeholder only. Future work should construct a validated ipTIME header,
    # copy only user-provided local inputs, and recompute all required checksums.
    payload = (
        b"EXPERIMENTAL-IPTIME-A2004MU-PLACEHOLDER\n"
        b"NOT FLASH VERIFIED\n"
        b"This is not a complete firmware image.\n"
    )
    output.write_bytes(payload)

    print("wrote placeholder experimental output")
    print("this is not a complete firmware image and is not safe to flash")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
