# Kernel Platform Inventory

## Goal

* Determine whether latest OpenWrt/Linux has enough RTL8197F platform support to
  start with DTS/image work.
* Decide whether kernel platform support is a blocker before DTS skeleton work.

## OpenWrt Tree

* Path: `/home/user/openwrt`
* HEAD: `6e9fd1c3ba elfutils: update to 0.195`
* Status: clean

## OpenWrt Target Findings

`target/linux/realtek` exists in the inspected OpenWrt tree.

Observed target metadata:

* `ARCH:=mips`
* `BOARD:=realtek`
* `BOARDNAME:=Realtek MIPS`
* `KERNEL_PATCHVER:=6.18`
* `SUBTARGETS:=rtl838x rtl839x rtl930x rtl930x_nand rtl931x rtl931x_nand`

Observed subtargets:

* `rtl838x`
* `rtl839x`
* `rtl930x`
* `rtl930x_nand`
* `rtl931x`
* `rtl931x_nand`

The existing realtek target appears focused on RTL83xx/RTL93xx switch SoCs. It
has useful OpenWrt target structure, DTS, image recipe, Ethernet, DSA, MDIO, and
board.d examples, but no direct RTL8197F support was found in `target/linux`.

The inspected realtek subtargets use `CPU_TYPE:=24kc`. That does not prove
compatibility with RTL8197F.

## Keyword Search Summary

Searches were run read-only against `/home/user/openwrt` under `target/linux`,
`package/kernel`, and `include`.

Direct platform keywords:

* `rtl8197`, `RTL8197`, `8197F`, `RTL8197F`: no direct RTL8197F platform support
  found.
* `rtkmipsel`: no matches found.
* `Lexra`, `lexra`, `lx5280`, `lx4189`: no platform support found.
* `rlx`, `RLX`: only unrelated text matches were found.

Broad `8197` matches included unrelated numeric constants, such as Realtek PHY
tables, and should not be treated as RTL8197F platform support.

The phrase `Realtek MIPS` appears in the existing realtek target metadata, but
that target is currently centered on RTL83xx/RTL93xx families.

## Network Driver Findings

Realtek-related network support exists in OpenWrt/Linux areas, including:

* Realtek PHY support and patches.
* Realtek DSA and switch-related patches.
* Existing `target/linux/realtek` Ethernet and switch support for RTL83xx/RTL93xx
  families.
* Generic or legacy Realtek switch/PHY code paths in `target/linux/generic` and
  `package/kernel`.

This is evidence that useful reference code and APIs exist. It is not evidence
that A2004MU Ethernet MAC or the observed stock switch chip id `0x6367-0020` is
supported. The A2004MU MAC, switch, and PHY path remains unconfirmed.

## Upstream Linux Source

No local upstream Linux source tree was found at:

* `/home/user/linux`
* `/home/user/linux-stable`
* `../linux`
* `../linux-stable`

Upstream Linux platform support still requires a separate source inventory.

## Preliminary Decision

Direct RTL8197F platform support was not found in the current OpenWrt target
tree.

Existing `target/linux/realtek` may be a structural reference, but it is not a
confirmed base for A2004MU. DTS skeleton work should not be treated as
sufficient until platform, clock, interrupt, timer, UART, SPI, Ethernet, and
switch assumptions are confirmed.

The next decision is whether to add a new realtek subtarget, create a separate
target, or first create kernel support patches for missing RTL8197F platform
pieces.

## Blockers Before DTS

* CPU/platform compatibility
* Interrupt controller
* Timer/clock
* UART binding
* SPI NOR controller
* Ethernet MAC
* Switch/PHY path
* Memory map
* Flash partition map

## Next Work

1. Obtain or inspect upstream Linux source for RTL8197F, Lexra, or RLX support.
2. Compare RTL8197F with existing OpenWrt realtek target SoCs.
3. Decide target/subtarget placement.
4. Only then draft DTS skeleton and image recipe.
