# OpenWrt Gap Analysis

## Local OpenWrt Tree

No local latest OpenWrt source tree was found during this pass.

Searched paths:

* `../openwrt`
* `/home/user/openwrt`
* `../openwrt-mainline`
* `/home/user/openwrt-mainline`

Next step: clone or provide the path to a latest OpenWrt source tree, then
repeat this analysis read-only before writing patches.

## Found Target Candidates

No target candidates were confirmed locally because no OpenWrt source tree was
available.

Potential areas to inspect once a tree is available:

* `target/linux/realtek`
* Other MIPS targets with similar DTS and image recipe structure
* Existing SPI NOR partition patterns
* Existing board.d network and LED examples

## Missing Support Summary

Support remains unimplemented until verified against a current OpenWrt tree.
Expected gaps for A2004MU/RTL8197F include:

* Target/subtarget placement
* RTL8197F platform support
* A2004MU DTS
* SPI NOR flash partition map
* Image recipe
* Ethernet MAC support
* Switch/PHY support for the observed `0x6367-0020` switch chip id
* Network defaults for wired LAN
* LED/button definitions
* Initramfs-first bring-up strategy
* Later factory/sysupgrade strategy

## Likely Required New Files

Exact target names are not confirmed. Candidate files may include:

* `target/linux/<target>/dts/rtl8197f_iptime_a2004mu.dts`
* `target/linux/<target>/image/*.mk`
* `target/linux/<target>/base-files/etc/board.d/02_network`
* `target/linux/<target>/base-files/etc/board.d/01_leds`
* `target/linux/<target>/config-*`

## Likely Required Patch Areas

Exact patch scope depends on what the latest OpenWrt tree already contains.
Candidate patch areas:

* Kernel platform support for RTL8197F if missing
* Clock, timer, interrupt, and UART support if missing
* SPI NOR controller or binding support if missing
* Ethernet MAC driver support if missing
* Switch/PHY support if not covered by existing upstream drivers
* OpenWrt image recipe and board defaults
* Device tree bindings if no existing compatible binding applies

## Current Mainline Deliverables

The mainline port deliverables are not present yet. The expected deliverables
are:

* Clean-room DTS for A2004MU
* Target/subtarget integration decision
* Image recipe suitable for first bring-up
* Network defaults for wired LAN
* LED/button definitions
* Minimal Ethernet/switch/PHY support path
* Initramfs-first build and boot log analysis plan

No actual OpenWrt source patches exist in this repository yet.
