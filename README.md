# ipTIME A2004MU support for OpenWrt

[한국어 README](README.ko.md)

This is an unofficial, experimental port of OpenWrt to the ipTIME A2004MU
(Realtek RTL8197F). It is not affiliated with or endorsed by OpenWrt, ipTIME,
or Realtek.

The repository contains one source patch, the exact OpenWrt base revision and
build configuration, research notes, and independently written analysis tools.
It intentionally does not contain firmware images, stock firmware, extracted
filesystems, Realtek SDK source, or device calibration data.

## Verified hardware state

The pre-publication test build has booted on an A2004MU with:

- Linux 6.18.36 and a SquashFS/JFFS2 overlay;
- working DHCP, SSH, sysupgrade, and normal reboot;
- all four LAN ports and the WAN port linked and tested at 1 Gbit/s full
  duplex;
- interrupt-driven RTL8197F Ethernet with repeated bidirectional transfers and
  no observed FCS, symbol, or discard errors;
- a working RTL8822BE 5 GHz radio using board calibration from NVMEM.

Limitations:

- the RTL8197F integrated 2.4 GHz radio is unsupported;
- a separate 5 GHz client throughput test is still required;
- router-local Ethernet throughput is CPU-bound at roughly 195 Mbit/s;
- LAN-to-LAN switch throughput and WAN forwarding throughput require separate
  two-endpoint measurements;
- hardware NAT is not implemented;
- configuration-preserving sysupgrade is rejected; use `sysupgrade -n`;
- the source default keeps Wi-Fi disabled. Never ship an open access point as a
  default configuration.

See [STATUS.md](STATUS.md) for the tested image record and remaining release
gates.

## Build

The patch is based on OpenWrt commit:

```text
6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2
```

Apply `patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch`, copy
`configs/a2004mu.config` to `.config`, run `make defconfig`, then build.
Full commands and output names are in [docs/building.md](docs/building.md).

Do not flash an image merely because it builds. Keep UART recovery available,
run the image self-checks, and run `sysupgrade -n --test` before any
sysupgrade.

Binary release assets, when provided, are separate from Git history. The
hardware-tested sysupgrade image and the offline-only factory-wrapper status
are recorded in [STATUS.md](STATUS.md). Do not treat the factory wrapper as a
universal installer.

The current bilingual release notes, exact filenames, checksums, and recovery
warnings are in
[docs/release-v0.1.0-experimental.md](docs/release-v0.1.0-experimental.md).

## Source and licensing

The repository's original material is offered under GPL-2.0-only unless a file
states otherwise. The OpenWrt patch retains the licenses and notices of the
files it modifies or derives from. The firmware build also selects separately
licensed packages and redistributable Realtek Wi-Fi firmware.

The Realtek RTL819x SDK was used as hardware reference material. No original
SDK source file is shipped here: the platform and driver code was written for
current Linux/OpenWrt interfaces using SDK hardware facts and observed device
behavior. The SDK also contains proprietary components, which are not copied
into this repository. This project does not claim a strict two-team clean-room
process. The provenance audit, file-level SDK license findings, and comparison
with public SDK-based projects are in
[docs/provenance-and-licensing.md](docs/provenance-and-licensing.md).

OpenWrt is a registered trademark owned by Software Freedom Conservancy (SFC).
This project is not affiliated with, sponsored by, or endorsed by OpenWrt.

## Repository safety

Before any publication:

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_provenance_boundaries.sh
git diff --check
```

The checks are defensive filters, not legal review. Local binaries and private
handoff records are ignored and must remain outside Git history.
