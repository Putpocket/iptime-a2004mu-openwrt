# OpenWrt Gap Analysis

## Local OpenWrt Tree

OpenWrt source tree was prepared outside this repository and inspected
read-only.

* Path: `/home/user/openwrt`
* Status after inspection: clean
* HEAD: `6e9fd1c3ba elfutils: update to 0.195`

Searched candidate paths:

* `../openwrt`
* `/home/user/openwrt`
* `../openwrt-mainline`
* `/home/user/openwrt-mainline`

## Target/Linux Inventory

`target/linux` exists and includes many targets, including:

* `ath79`
* `bmips`
* `lantiq`
* `ramips`
* `realtek`

The `target/linux/realtek` target exists. Its top-level metadata says:

* `ARCH:=mips`
* `BOARD:=realtek`
* `BOARDNAME:=Realtek MIPS`
* `SUBTARGETS:=rtl838x rtl839x rtl930x rtl930x_nand rtl931x rtl931x_nand`
* Target description: Realtek RTL83xx/RTL93xx based boards

This is useful as a Realtek MIPS target structure reference, but it is not
evidence of RTL8197F support.

## Search Results

Search files were written under `/tmp` during investigation:

* `/tmp/a2004mu-openwrt-realtek-search.txt`
* `/tmp/a2004mu-openwrt-target-dirs.txt`
* `/tmp/a2004mu-openwrt-dts-files.txt`
* `/tmp/a2004mu-openwrt-image-files.txt`
* `/tmp/a2004mu-openwrt-board-d-files.txt`
* `/tmp/a2004mu-realtek-files.txt`
* `/tmp/a2004mu-realtek-key-files.txt`
* `/tmp/a2004mu-realtek-keyword-search.txt`
* `/tmp/a2004mu-mips-target-comparison.txt`
* `/tmp/a2004mu-board-d-examples.txt`
* `/tmp/a2004mu-direct-support-search.txt`

Direct support search for the following terms returned no target/linux matches:

* `a2004`
* `a2004m`
* `A2004`
* `iptime.*a2004`
* `rtl8197f`
* `RTL8197F`
* `rtl8197`
* `RTL8197`
* `rtkmipsel`

Therefore, A2004MU direct support was not found, and RTL8197F direct support was
not found in this OpenWrt tree.

The broader Realtek search returned many matches, mostly in:

* `target/linux/realtek`
* `target/linux/generic` Realtek PHY, DSA, and patch areas
* Other targets referencing Realtek PHYs or USB/Ethernet devices

## Found Target Candidates

Potential reference targets:

* `target/linux/realtek`: Realtek MIPS switch SoC target. Contains useful MIPS
  target layout, DTS, image recipe, DSA, MDIO, Ethernet, and board.d examples,
  but currently targets rtl838x/rtl839x/rtl930x/rtl931x families rather than
  RTL8197F.
* `target/linux/ramips`: MIPS router target with many SPI NOR router boards,
  ipTIME examples, DTS conventions, image recipes, and board.d defaults.
* `target/linux/ath79`: MIPS router target with extensive SPI NOR image recipe,
  DTS, and board.d examples.
* `target/linux/lantiq`: MIPS target with many DTS and board.d examples.

No target/subtarget is confirmed for RTL8197F yet. The most plausible next
decision is whether to extend `target/linux/realtek` with a new RTL8197F-class
subtarget or create another target/subtarget after checking kernel support,
SoC ancestry, and boot requirements.

## DTS Example Candidates

Useful references found:

* `target/linux/realtek/dts/rtl838x.dtsi`
* `target/linux/realtek/dts/rtl839x.dtsi`
* `target/linux/realtek/dts/rtl930x.dtsi`
* `target/linux/realtek/dts/rtl931x.dtsi`
* `target/linux/realtek/dts/rtl8380_*.dts`
* `target/linux/realtek/dts/rtl8382_*.dts`
* `target/linux/ramips/dts/mt7620a_iptime.dtsi`
* `target/linux/ramips/dts/mt7620a_iptime_a1004ns.dts`
* `target/linux/ramips/dts/mt7620a_iptime_a104ns.dts`

The ramips ipTIME DTS files are vendor/board-style examples only; they do not
imply hardware similarity to RTL8197F.

## Image Recipe Example Candidates

Useful references found:

* `target/linux/realtek/image/common.mk`
* `target/linux/realtek/image/rtl838x.mk`
* `target/linux/realtek/image/rtl839x.mk`
* `target/linux/realtek/image/rtl930x.mk`
* `target/linux/realtek/image/rtl931x.mk`
* `target/linux/ramips/image/*.mk`
* `target/linux/ath79/image/*.mk`

The realtek image recipes are useful for target-local image recipe structure.
They are not proof that the existing realtek image pipeline fits A2004MU.

## board.d Example Candidates

Useful references found:

* `target/linux/realtek/base-files/etc/board.d/01_leds`
* `target/linux/realtek/base-files/etc/board.d/02_network`
* `target/linux/ramips/*/base-files/etc/board.d/01_leds`
* `target/linux/ramips/*/base-files/etc/board.d/02_network`
* `target/linux/ath79/*/base-files/etc/board.d/01_leds`
* `target/linux/ath79/*/base-files/etc/board.d/02_network`

The board.d examples show patterns for `board_name`, LED defaults, label MAC
handling, and LAN/WAN defaults.

## Missing Support Summary

Support remains unimplemented in this repository. Expected gaps for
A2004MU/RTL8197F include:

* Target/subtarget placement
* RTL8197F platform support
* A2004MU DTS
* UART, clock, interrupt, timer, and memory mapping support if not already in
  upstream Linux/OpenWrt
* SPI NOR controller or binding support if needed
* Flash partition map from stock evidence
* Image recipe for first bring-up
* Ethernet MAC support
* Switch/PHY support for the observed `0x6367-0020` switch chip id
* Network defaults for wired LAN
* LED/button definitions
* Initramfs-first bring-up strategy
* Later factory/sysupgrade strategy

## Kernel Platform Inventory

Kernel/platform inventory was completed against `/home/user/openwrt` at
`6e9fd1c3ba`. See [kernel-platform-inventory.md](kernel-platform-inventory.md).

Direct RTL8197F platform support is still not confirmed. The existing
`target/linux/realtek` target is useful as a Realtek MIPS structural reference,
but it should not be treated as a confirmed base for A2004MU until platform,
clock, interrupt, timer, UART, SPI, Ethernet, and switch support are verified.

## Likely Required New Files

Exact target names are not confirmed. Candidate files may include:

* `target/linux/<target>/dts/rtl8197f_iptime_a2004mu.dts`
* `target/linux/<target>/dts/rtl8197f.dtsi`
* `target/linux/<target>/image/*.mk`
* `target/linux/<target>/base-files/etc/board.d/02_network`
* `target/linux/<target>/base-files/etc/board.d/01_leds`
* `target/linux/<target>/config-*`
* `target/linux/<target>/<subtarget>/target.mk`
* `target/linux/<target>/<subtarget>/config-*`

## Likely Required Patch Areas

Exact patch scope depends on what kernel support already exists outside the
OpenWrt target tree. Candidate patch areas:

* Kernel platform support for RTL8197F if missing
* Clock, timer, interrupt, and UART support if missing
* SPI NOR controller or binding support if missing
* Ethernet MAC driver support if missing
* Switch/PHY support if not covered by existing upstream drivers
* OpenWrt image recipe and board defaults
* Device tree bindings if no existing compatible binding applies

## Still Unconfirmed

* Whether RTL8197F is close enough to the existing OpenWrt `realtek` target to
  justify a new subtarget there.
* Whether upstream Linux already has usable RTL8197F platform support.
* Exact UART, SPI, interrupt, clock, Ethernet MAC, switch, PHY, GPIO, LED, and
  button bindings for A2004MU.
* Whether the observed switch chip id `0x6367-0020` maps to an existing Linux
  DSA/switch/PHY path.
* Whether first bring-up should use a new realtek subtarget or a separate target
  after kernel inventory.

## Next Work Units

1. Inspect upstream Linux and OpenWrt target patches for RTL8197F platform
   support.
2. Decide target/subtarget placement based on actual SoC support, not target
   name similarity.
3. Draft a minimal A2004MU DTS skeleton from observed hardware facts.
4. Define the stock-derived flash partitions in DTS.
5. Identify the minimal Ethernet MAC and switch/PHY path for wired LAN.
6. Add image recipe skeleton for initramfs-first bring-up.
7. Add board.d network defaults after the interface naming path is understood.
8. Keep SDK wrapper tooling as side-path evidence only.

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
