# Tooling

This repository keeps tools separated by role. Safe tools may inspect local
artifacts by user-provided path, but they must not copy vendor firmware,
extracted rootfs contents, SDK binaries, `.so`, `.ko`, or generated images into
git.

The primary deliverable is a clean-room mainline OpenWrt port. No actual
OpenWrt source patches exist in this repository yet.

## Evidence Tools

These tools collect or summarize evidence for the mainline porting work. They
are read-only with respect to their input files.

| Tool | Role |
| --- | --- |
| `tools/inspect_stock_firmware.py` | Reads a user-provided local stock firmware path and prints header/layout observations. |
| `tools/inspect_sdk_image.py` | Reads a user-provided local SDK image path and prints image markers, strings, and SquashFS offsets. |
| `tools/analyze_uart_boot_log.py` | Reads a user-provided UART log and reports heuristic boot signals in text or JSON. |

Evidence from these tools should be used to design the clean-room OpenWrt DTS,
target integration, image recipe, and network bring-up plan. The tools do not
interact with devices.

## Experimental Side-path Tools

These tools are retained for image-format research. They are not mainline port
deliverables and must not drive the project direction.

| Tool | Role |
| --- | --- |
| `tools/verify_iptime_checksum.py` | Checks observed checksum candidates against a local image. |
| `tools/plan_iptime_wrapper.py` | Dry-run wrapper layout planner. It does not create output images. |
| `tools/make_experimental_iptime_image.py` | Guarded experimental writer that requires `--force-experimental` and writes only under `out/`. |

Outputs from the side-path tools are not flash-verified. This path is not a
substitute for clean-room OpenWrt support.

## Repo Safety

| Tool | Role |
| --- | --- |
| `scripts/check_repo_safety.sh` | Checks for forbidden binary artifacts, extracted rootfs directories, and large files. |
| `scripts/check_clean_room_boundaries.sh` | Checks for SDK/vendor/generated artifacts and clean-room boundary violations. |

Run both before publishing or committing:

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_clean_room_boundaries.sh
```

## Legacy Local Tools

Legacy local scripts were moved outside the repository under local artifacts.
They are not commit candidates unless rewritten cleanly.

| Tool | Status |
| --- | --- |
| `tools/analyze_header.py` | Legacy local only; fixed repo-local firmware path in older copy. |
| `tools/verify_iptime_header.py` | Legacy local only; fixed repo-local firmware path in older copy. |
| `tools/verify_iptime_any.py` | Replaced by `tools/verify_iptime_checksum.py`. |
| `tools/pack_a2004m_openwrt.py` | Exclude from commit; old generated-candidate packing experiment. |

## Local Artifact Location

Unsafe local artifacts stay outside the repository:

```text
../iptime-a2004mu-local-artifacts/
```
