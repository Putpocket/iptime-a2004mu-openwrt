# Implementation Log

## RTL8197F Scaffold Branch

* OpenWrt source tree: `/home/user/openwrt`
* Branch: `a2004mu-rtl8197f-scaffold`
* Purpose: first clean-room scaffold for RTL8197F platform investigation
* Status: not build-validated, not hardware-validated
* Defconfig metadata check passed; no firmware/image build performed.
* Added provisional RTL8197F compatible scaffold patch; not build-validated, not hardware-validated, no firmware/image build performed.
* Kernel prepare patch apply check passed; no firmware/image build performed, no hardware validation.
* Added unlinked A2004MU DTS skeleton; not build-linked, not build-validated, not hardware-validated, no firmware/image build.
* Added minimal A2004MU device profile; no flash layout guessed, not build-validated, not hardware-validated, no firmware/image build.
* Explicit A2004MU device profile defconfig check passed; no firmware/image build performed, no hardware validation.
* `target/linux/compile` attempted; failed on missing toolchain/host tools, no firmware/sysupgrade/factory image build, no hardware validation.
* No flashing or device-write instructions included
* Patch export:

  * `patches/openwrt/rtl8197f-platform-scaffold.patch`

## OpenWrt Tree Changes

Files changed in the OpenWrt working tree:

* `target/linux/realtek/Makefile`
* `target/linux/realtek/rtl8197f/target.mk`
* `target/linux/realtek/rtl8197f/config-6.18`
* `target/linux/realtek/rtl8197f/README.md`
* `target/linux/realtek/image/rtl8197f.mk`

## Scaffold Summary

The scaffold adds a provisional `rtl8197f` subtarget entry under the existing
OpenWrt `realtek` target. It also adds a minimal subtarget directory and an
empty image include file so the structure is explicit.

No DTS, device image recipe, register map, IRQ number, clock value, Ethernet
driver path, or switch/PHY mapping is claimed by this scaffold.

## Remaining TODO

* Confirm RTL8197F CPU/platform compatibility.
* Confirm the machine compatible path.
* Confirm timer, interrupt, and early UART support.
* Confirm SPI NOR controller support.
* Confirm Ethernet MAC support.
* Confirm switch/PHY/MDIO topology.
* Decide whether `target/linux/realtek` is the correct final target placement.
* Add DTS and image recipes only after platform assumptions are defensible.

## Why DTS-First Is Still Blocked

A DTS can describe known board facts, but it cannot make the kernel boot if the
RTL8197F platform entry, timer, interrupt, UART, SPI, and network paths are not
available. The next implementation step is to validate or create the minimal
platform base before connecting a board DTS or image recipe.

## Compile Checks

* Host tools and toolchain were prepared; `target/linux/compile` still fails at
  kernel Kconfig because the scaffold must not guess an RTL838x/RTL839x family
  selection for RTL8197F. No firmware, sysupgrade, or factory image build was
  performed; no hardware validation was performed.
* Added RTL8197F Kconfig scaffold without selecting RTL838x/RTL839x/RTL930x/RTL931x.
  `target/linux/compile` now stops at unresolved MIPS32 CPU type selection; no
  firmware, sysupgrade, or factory image build was performed; no hardware
  validation was performed.
* CPU type evidence found in the stock UART log: `CPU revision is: 00019385
  (MIPS 24Kc)`. Selected `CONFIG_CPU_MIPS32_R2`; `target/linux/compile` now
  stops at unresolved appended-DTB kernel config selection. No firmware,
  sysupgrade, or factory image build was performed; no hardware validation was
  performed.
* Selected appended-DTB policy from existing `target/linux/realtek` configs:
  `CONFIG_MIPS_RAW_APPENDED_DTB`. `target/linux/compile` now stops at unresolved
  kernel command line policy selection. No firmware, sysupgrade, or factory
  image build was performed; no hardware validation was performed.
