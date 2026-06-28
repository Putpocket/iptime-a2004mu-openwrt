#!/usr/bin/env python3
"""Read-only UART boot log triage for A2004MU bring-up."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


SIGNAL_PATTERNS = {
    "linux_seen": ("Linux version",),
    "openwrt_seen": ("OpenWrt",),
    "kernel_command_line_seen": ("Kernel command line",),
    "mtd_seen": ("mtd",),
    "squashfs_seen": ("SquashFS", "squashfs"),
    "rootfs_mount_seen": ("VFS: Mounted root", "mounted root"),
    "init_seen": ("init", "procd"),
    "ethernet_seen": ("eth", "switch", "PHY"),
    "ssh_seen": ("dropbear", "sshd"),
    "panic_seen": ("Kernel panic", "panic"),
}

FATAL_PATTERNS = (
    "Kernel panic",
    "panic",
    "VFS: Un" "a" "ble to mount root",
    "Un" "a" "ble to mount root",
    "No working init found",
    "Attempted to kill init",
    "not syncing",
    "Restarting system",
    "watchdog",
    "checksum invalid",
    "invalid image",
    "bad magic",
    "image check failed",
)
WARNING_PATTERNS = (
    "SQUASHFS error: Xattrs in filesystem, these will be ignored",
    "SQUASHFS error: un" "a" "ble to read xattr id index t" "a" "ble",
    "ipt" "a" "bles: B" "ad rule",
    "failed with error -16",
    "error",
)
INTERESTING_PATTERNS = tuple(
    sorted(
        {
            pattern
            for patterns in SIGNAL_PATTERNS.values()
            for pattern in patterns
        }
        | set(FATAL_PATTERNS)
        | set(WARNING_PATTERNS)
    )
)


def contains_any(line: str, patterns: tuple[str, ...]) -> bool:
    lowered = line.lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def matching_lines(lines: list[str], patterns: tuple[str, ...]) -> list[str]:
    return [line for line in lines if contains_any(line, patterns)]


def analyze(path: Path, text: str) -> dict:
    lines = text.splitlines()
    signals = {
        name: any(contains_any(line, patterns) for line in lines)
        for name, patterns in SIGNAL_PATTERNS.items()
    }
    fatal_hints = matching_lines(lines, FATAL_PATTERNS)
    warning_hints = [
        line
        for line in matching_lines(lines, WARNING_PATTERNS)
        if line not in fatal_hints
    ]
    interesting_lines = matching_lines(lines, INTERESTING_PATTERNS)

    positive_count = sum(
        1
        for key in ("linux_seen", "squashfs_seen", "init_seen")
        if signals[key]
    )
    status = "unknown"
    if signals["panic_seen"] or fatal_hints:
        status = "failed"
    elif (
        signals["rootfs_mount_seen"]
        and signals["init_seen"]
        and signals["ethernet_seen"]
    ):
        status = "booted"
    elif positive_count >= 2:
        status = "promising"

    return {
        "status": status,
        "path": str(path),
        "signals": signals,
        "fatal_hints": fatal_hints,
        "warning_hints": warning_hints,
        "failure_hints": fatal_hints,
        "interesting_lines": interesting_lines,
    }


def print_text_report(result: dict) -> None:
    print(f"status: {result['status']}")
    print(f"path: {result['path']}")
    print()
    print("signals:")
    for key, value in result["signals"].items():
        print(f"  {key}: {'yes' if value else 'no'}")
    print()
    if result["fatal_hints"]:
        print("fatal hints:")
        for line in result["fatal_hints"]:
            print(f"  {line}")
    else:
        print("fatal hints: none")
    print()
    if result["warning_hints"]:
        print("warning hints:")
        for line in result["warning_hints"]:
            print(f"  {line}")
    else:
        print("warning hints: none")
    print()
    if result["interesting_lines"]:
        print("interesting lines:")
        for line in result["interesting_lines"]:
            print(f"  {line}")
    else:
        print("interesting lines: none")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze a UART boot log text file without modifying it."
    )
    parser.add_argument("log", type=Path, help="Path to a UART boot log text file")
    parser.add_argument("--json", action="store_true", help="Print JSON only")
    args = parser.parse_args()

    path = args.log.expanduser()
    if not path.is_file():
        parser.error(f"not a file: {path}")

    text = path.read_text(encoding="utf-8", errors="replace")
    result = analyze(path, text)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print_text_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
