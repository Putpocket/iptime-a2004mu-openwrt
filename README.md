# ipTIME A2004MU OpenWrt Port Research

This repository contains GitHub-safe notes and tooling for researching an
OpenWrt port workflow for the ipTIME A2004MU, board alias `a2004m`, based on
the Realtek RTL8197F platform.

The goal is to document the hardware, inspect locally available firmware
artifacts, and eventually prepare an experimental ipTIME web-update style image
from locally built SDK outputs.

This repository does not provide a flash-verified image.

## Safety Status

This work is experimental and not flash-verified.

Do not flash images produced from this research unless you have independently
validated the image layout, checksums, boot behavior, and recovery path. This
repository must not claim that a generated image is safe to flash.

Do not commit any of the following:

* Realtek SDK source files
* ipTIME stock firmware
* extracted root filesystems
* kernel modules or shared libraries
* license-unclear vendor binaries
* generated firmware images

Only GitHub-safe material belongs here: documentation, scripts written from
scratch, metadata, checksums, patch instructions, and build workflow notes.

## Known Hardware

* Device: ipTIME A2004MU
* Board alias: `a2004m`
* SoC: Realtek RTL8197F
* DRAM: 64 MB DDR2 533 MHz
* Flash: xmc25qh64, 8 MB SPI NOR
* Flash erase size: 64 KB
* Bootloader prompt: `<RealTek>`
* UART: 38400 8N1

Observed stock flash layout:

| Region | Range |
| --- | --- |
| boot | `0x00000-0x1ffff` |
| factory | `0x20000-0x2ffff` |
| config/data | `0x30000-0x3ffff` |
| firmware | `0x40000-0x7fffff` |

The firmware region starts at `0x40000`. Do not overwrite below `0x40000`.

## Current Status

* Realtek OpenWrt SDK build succeeded locally.
* SDK ramfs image was generated locally.
* Bootloader RAM upload path is not currently available: `XMOD` and TFTP upload
  were not usable in testing, although Ethernet initialization was observed.
* SDK generated `AP-fw.bin` is a Realtek `cvimg`/raw image, not an ipTIME web
  update format image.
* Earlier notes indicated an SDK image using `linuxpart=0x60000`, which would
  conflict with the A2004MU firmware region start at `0x40000`.
* The current locally inspected `AP-fw.bin` reports `linuxpart=0x40000`; keep
  verifying this on each generated image before serious wrapping work.
* Next work is image layout and header tooling.

## Local Paths

Expected local research inputs are outside this repository:

```text
~/rtl8197f-research/openwrt_rtk/rtk_openwrt_sdk
~/rtl8197f-research/openwrt_rtk/rtk_openwrt_sdk/bin/rtkmipsel
~/rtl8197f-research/openwrt_rtk/rtk_openwrt_sdk/firmware
```

Do not copy stock firmware or SDK outputs into this repository.

Local artifacts that are not safe for git are kept outside this repository:

```text
../iptime-a2004mu-local-artifacts/
```

The repository is considered GitHub-safe only when this passes:

```sh
bash scripts/check_repo_safety.sh
```

## Tools

Inspect a stock firmware file without modifying it:

```sh
python3 tools/inspect_stock_firmware.py /path/to/stock-firmware.bin
```

Inspect a Realtek SDK output image without modifying it:

```sh
python3 tools/inspect_sdk_image.py /path/to/openwrt-rtkmipsel-rtl8197f-AP-fw.bin
```

Verify observed checksum candidates against a local stock firmware file without
modifying it:

```sh
python3 tools/verify_iptime_checksum.py /path/to/local/stock-firmware.bin
```

For automation, emit JSON only:

```sh
python3 tools/verify_iptime_checksum.py --json /path/to/local/stock-firmware.bin
```

Plan an experimental wrapper layout without creating any output image:

```sh
python3 tools/plan_iptime_wrapper.py --stock /path/to/local/stock-firmware.bin --sdk-image /path/to/local/openwrt-rtkmipsel-rtl8197f-AP-fw.bin
```

Check the repository for accidentally committed unsafe files:

```sh
bash scripts/check_repo_safety.sh
```

See `docs/repo-safety.md` for local artifact handling and safety checks.

See `docs/tooling.md` for the current tool roles and safety classification.

The experimental image wrapper skeleton intentionally refuses to write output
unless `--force-experimental` is passed. It is not complete image-generation
tooling.
