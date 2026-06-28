# Status

This repository is for GitHub-safe ipTIME A2004MU / Realtek RTL8197F OpenWrt
porting research. The primary path is now a latest/official-style OpenWrt port
implemented clean-room.

It does not provide a flash-verified OpenWrt image.

## Current Direction

* Mainline OpenWrt port: not completed.
* Current priority: latest OpenWrt clean-room porting work.
* First target: kernel boot, rootfs mount, wired LAN, and SSH.
* Wi-Fi: out of the first bring-up unless a clean driver path is confirmed.
* SDK wrapper candidate: experimental side path only.
* No flash-verified OpenWrt image exists yet.

## Confirmed Evidence

* Device: ipTIME A2004MU
* Board alias: `a2004m`
* SoC: Realtek RTL8197F
* DRAM: 64 MB DDR2
* Flash: 8 MB SPI NOR
* UART: 38400 8N1
* Bootloader prompt: `<RealTek>`
* Stock firmware version 15.352 model field: `a2004m`
* Stock firmware version 15.352 rootfs offset: `0x2c0000`
* Stock boot log collected.
* Stock boot analyzer status: `booted`
* Stock boot analyzer fatal hints: `0`
* Stock rootfs mount seen: yes
* Stock Ethernet evidence seen: yes
* Stock panic seen: no
* Stock boot log shows `rtkxxpart` partitions on `m25p80`.
* Stock boot log shows SquashFS root mounted read-only.
* Stock boot log shows switch API version `v1.2.12`.
* Stock boot log shows switch chip id `0x6367-0020`.
* Stock boot log shows `eth0`, `eth1`, and `peth0` mapped to `eth1`.
* Local SDK `AP-fw.bin` starts with `cs6c`.
* Local SDK `AP-fw.bin` SquashFS offset: `0x19c000`.
* Local SDK `AP-fw.bin` reports `linuxpart=0x40000` and `hwpart=0x20000`.

## Partially Known

* Hardware facts are partially known from stock firmware, stock boot logs, and
  board observations.
* Exact clean-room kernel platform requirements for RTL8197F are not known yet.
* Ethernet MAC, switch, and PHY support path still needs mainline gap analysis.
* DTS, image recipe, and OpenWrt board defaults have not been implemented.

## Repository Safety

The repository should contain only documentation, scripts written from scratch,
metadata, and workflow notes. Local stock firmware, SDK outputs, extracted
rootfs contents, generated candidates, and binary blobs stay outside this
repository under:

```text
../iptime-a2004mu-local-artifacts/
```

Run these before publishing or committing:

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_clean_room_boundaries.sh
```

## Current Safe Next Work

* Inventory a latest OpenWrt source tree for existing RTL8197F/Realtek support.
* Decide target/subtarget strategy.
* Draft an A2004MU DTS from observed hardware facts.
* Define flash partitions from stock evidence.
* Identify a clean Ethernet/switch/PHY support path.
* Build toward an initramfs-first bring-up with UART logging.
