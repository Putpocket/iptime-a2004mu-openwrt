# Tooling

This repository keeps tools separated by safety level. Safe tools may inspect
local artifacts, but they must not copy vendor firmware, extracted rootfs
contents, SDK binaries, `.so`, `.ko`, or generated images into git.

## Tool Categories

| Category | Tools | Status |
| --- | --- | --- |
| safe commit | `tools/inspect_stock_firmware.py`, `tools/inspect_sdk_image.py`, `tools/verify_iptime_checksum.py`, `tools/plan_iptime_wrapper.py`, `tools/make_experimental_iptime_image.py`, `tools/analyze_uart_boot_log.py`, `scripts/check_repo_safety.sh` | Written from scratch, does not require repo-local vendor artifacts. |
| safe after rewrite | none currently | Legacy checksum verifier was moved outside the repo; use `tools/verify_iptime_checksum.py` instead. |
| legacy local only | `tools/analyze_header.py`, `tools/verify_iptime_header.py` | Fixed repo-local firmware paths; useful as local notes, not clean commit candidates. |
| exclude from commit | `tools/pack_a2004m_openwrt.py` | Reads local vendor/rootfs inputs and writes a generated firmware candidate. |

## Existing Legacy Tools

Do not delete these without a separate cleanup decision:

| Tool | Role | Safety note |
| --- | --- | --- |
| `tools/analyze_header.py` | Prints stock header words, known value matches, and CRC32 candidates. | Reads `firmware/a2004m_ml_15_352.bin` directly, so it assumes an unsafe local artifact exists in the repo. |
| `tools/verify_iptime_header.py` | Reproduces observed header checksum behavior for one local stock image. | Reads `firmware/a2004m_ml_15_352.bin` directly. Treat output as local research evidence only. |
| `tools/verify_iptime_any.py` | Similar checksum verifier that can accept a firmware path argument. | Safe after rewrite: remove repo-local default path, add argparse, and label checksum output as observed. |
| `tools/pack_a2004m_openwrt.py` | Combines local stock/header/kernel/rootfs inputs into a candidate image. | Writes `firmware/a2004m_openwrt_candidate_15_999.bin`; unsafe for the current GitHub-safe workflow. |

## Working Tree Classification

| Path | Classification | Reason |
| --- | --- | --- |
| `README.md` | commit possible | GitHub-safe documentation. |
| `.gitignore` | commit possible | Blocks local artifacts and generated files. |
| `docs/hardware.md` | commit possible | GitHub-safe hardware notes. |
| `docs/image-format-notes.md` | commit possible | Documents observations without embedding firmware. |
| `docs/repo-safety.md` | commit possible | Documents safety policy and current local failure mode. |
| `docs/tooling.md` | commit possible | Documents tool roles and safety levels. |
| `scripts/check_repo_safety.sh` | commit possible | GitHub-safe repository scan script. |
| `tools/inspect_stock_firmware.py` | commit possible | Reads local stock firmware by path and prints metadata only. |
| `tools/inspect_sdk_image.py` | commit possible | Reads local SDK image by path and prints metadata only. |
| `tools/verify_iptime_checksum.py` | commit possible | Reads a local stock firmware path and checks observed checksum candidates only; `--json` emits stable machine-readable output for automation. |
| `tools/plan_iptime_wrapper.py` | commit possible | Dry-run planner for wrapper layout sanity checks; emits text or JSON and does not create image output. |
| `tools/make_experimental_iptime_image.py` | commit possible | Experimental writer gated by `--force-experimental`; output must be under `out/`, is not flash-verified, and is checked by observed checksum candidates after creation. |
| `tools/analyze_uart_boot_log.py` | commit possible | Read-only boot log triage tool; emits text or JSON and does not interact with devices. |
| `tools/verify_iptime_any.py` | exclude from commit | Moved outside repo under local artifacts; replaced by `tools/verify_iptime_checksum.py`. |
| `tools/verify_iptime_header.py` | legacy local only | Fixed repo-local firmware path. |
| `tools/analyze_header.py` | legacy local only | Fixed repo-local firmware path. |
| `tools/pack_a2004m_openwrt.py` | exclude from commit | Writes a generated firmware candidate under `firmware/`. |
| `firmware/` | exclude from commit | Moved outside repo; contains stock firmware, generated candidates, SquashFS, and extracted rootfs content. |
| `license-audit/` | exclude from commit for now | Moved outside repo; contains local audit outputs including a large file. |
| `logs/` | judgment pending | May contain raw device data or private identifiers. |

## Local Artifact Location

Unsafe local artifacts have been moved outside the repository:

```text
../iptime-a2004mu-local-artifacts/
```

Before committing or publishing, rerun:

```sh
bash scripts/check_repo_safety.sh
git status --short --branch
```
