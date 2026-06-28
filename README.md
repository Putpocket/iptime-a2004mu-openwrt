# ipTIME A2004MU OpenWrt Port Research

This repository contains GitHub-safe research notes and clean-room tooling for
bringing ipTIME A2004MU support to a latest/official-style OpenWrt source tree.

It does not provide a flash-verified OpenWrt image.

## Main Goal

* Add clean-room OpenWrt support for ipTIME A2004MU.
* Fill missing RTL8197F/A2004MU support without copying proprietary SDK code.
* First bring-up target: kernel boot, rootfs mount, wired LAN, and SSH.

## Not The Main Goal

* Deploying an old SDK-generated OpenWrt `AP-fw.bin` as the final solution.
* Relying on proprietary Realtek SDK source code.
* Treating the experimental wrapper candidate as the final porting path.
* Producing device-write instructions from this repository.

The SDK wrapper and checksum work remains as image-format research only. It is
an experimental side path, not the mainline OpenWrt deliverable.

## Current Evidence

Known device facts:

* Device: ipTIME A2004MU
* Board alias: `a2004m`
* SoC: Realtek RTL8197F
* DRAM: 64 MB DDR2
* Flash: 8 MB SPI NOR
* UART: 38400 8N1
* Bootloader prompt: `<RealTek>`

Collected evidence:

* Stock firmware version 15.352 model field: `a2004m`
* Stock rootfs offset: `0x2c0000`
* Stock boot log collected and analyzed
* Stock boot analyzer status: `booted`
* Stock boot analyzer fatal hints: `0`
* Stock rootfs mount seen: yes
* Stock Ethernet evidence seen: yes
* Stock panic seen: no
* Stock boot log shows `rtkxxpart` partitions on `m25p80`
* Stock boot log shows SquashFS root mounted read-only
* Stock boot log shows switch API version `v1.2.12`
* Stock boot log shows switch chip id `0x6367-0020`
* Stock boot log shows `eth0`, `eth1`, and `peth0` mapped to `eth1`
* SDK `AP-fw.bin` starts with `cs6c`
* SDK `AP-fw.bin` SquashFS offset: `0x19c000`
* SDK `AP-fw.bin` reports `linuxpart=0x40000` and `hwpart=0x20000`

The SDK image evidence is used to understand flash layout, boot arguments, image
structure, and rootfs placement. It is not a plan to ship SDK output.

## Current Primary Next Step

* Mainline OpenWrt porting gap analysis
* DTS, target, and image recipe plan
* Clean-room driver/support plan for the first wired LAN + SSH bring-up

See:

* `docs/mainline-porting-plan.md`
* `docs/openwrt-gap-analysis.md`
* `docs/clean-room-policy.md`
* `docs/sdk-wrapper-side-path.md`

## Repository Safety

Do not commit any of the following:

* Realtek SDK source files
* ipTIME stock firmware
* SDK output images
* generated candidate firmware
* extracted root filesystems
* kernel modules or shared libraries
* license-unclear vendor binaries

Only GitHub-safe material belongs here: documentation, scripts written from
scratch, metadata, checksums, patch plans, and workflow notes.

Local artifacts that are not safe for git are kept outside this repository:

```text
../iptime-a2004mu-local-artifacts/
```

Run these before committing or publishing:

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_clean_room_boundaries.sh
```

## Tools

Evidence tools:

```sh
python3 tools/inspect_stock_firmware.py /path/to/local/stock-firmware.bin
python3 tools/inspect_sdk_image.py /path/to/local/openwrt-rtkmipsel-rtl8197f-AP-fw.bin
python3 tools/analyze_uart_boot_log.py /path/to/uart-boot.log
```

Experimental side-path tools:

```sh
python3 tools/verify_iptime_checksum.py /path/to/local/stock-firmware.bin
python3 tools/plan_iptime_wrapper.py --stock /path/to/local/stock-firmware.bin --sdk-image /path/to/local/openwrt-rtkmipsel-rtl8197f-AP-fw.bin
python3 tools/make_experimental_iptime_image.py --stock /path/to/local/stock-firmware.bin --sdk-image /path/to/local/openwrt-rtkmipsel-rtl8197f-AP-fw.bin --output out/a2004m_experimental_candidate.bin --force-experimental
```

The experimental side-path tools are not mainline OpenWrt deliverables, and
their outputs are not flash-verified.
