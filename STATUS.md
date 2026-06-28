# Status

This repository is for GitHub-safe ipTIME A2004MU / Realtek RTL8197F OpenWrt
porting research. It does not provide a flash-verified image.

## Confirmed

* Device: ipTIME A2004MU
* Board alias: `a2004m`
* SoC: Realtek RTL8197F
* DRAM: 64 MB DDR2
* Flash: xmc25qh64, 8 MB SPI NOR
* UART: 38400 8N1
* Bootloader prompt: `<RealTek>`
* Bootloader prompt can be reached with `ESC`
* Stock firmware version 15.352 model field: `a2004m`
* Stock firmware version 15.352 rootfs offset: `0x2c0000`
* Current local SDK `AP-fw.bin` starts with `cs6c`
* Current local SDK `AP-fw.bin` reports `linuxpart=0x40000`

## Repository Safety

The repository should contain only documentation, scripts written from scratch,
metadata, and workflow notes. Local stock firmware, SDK outputs, extracted
rootfs contents, and binary blobs are stored outside this repository under:

```text
../iptime-a2004mu-local-artifacts/
```

Run this before publishing or committing:

```sh
bash scripts/check_repo_safety.sh
```

## Not Verified

* No OpenWrt image from this repository is flash-verified.
* The ipTIME web-update image wrapper is not complete.
* Header/checksum observations are research notes, not a final format spec.
* RAM boot path is not available in current testing.
* Ethernet, switch, Wi-Fi, LuCI, and SSH operation on a generated image are not
  verified.

## Current Safe Next Work

* Keep comparing local stock firmware headers with `tools/inspect_stock_firmware.py`.
* Keep checking SDK outputs with `tools/inspect_sdk_image.py`.
* Rewrite or exclude legacy local scripts that assume repo-local firmware files.
* Keep generated images and vendor artifacts outside the repository.
