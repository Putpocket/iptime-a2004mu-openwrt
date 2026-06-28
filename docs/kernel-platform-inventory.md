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

An upstream Linux source tree was prepared outside this repository and inspected
read-only.

* Path: `/home/user/linux`
* HEAD: `0716f9b9338a Merge tag 'ntb-7.2' of https://github.com/jonmason/ntb`
* Status: clean

## Upstream Linux Inventory

Searches were run read-only against `/home/user/linux`, mainly under
`arch/mips`, `drivers`, and `include`.

Direct platform keywords:

* `rtl8197`, `RTL8197`, `8197F`, `RTL8197F`: no matches found in the relevant
  platform, DTS, or driver areas searched.
* `rtkmipsel`: no matches found.
* `Lexra`, `lexra`, `lx5280`, `lx4189`: no RTL8197F platform support found.
  The relevant matches were the existing Realtek RTL838x/Otto clock references,
  such as `clock-lexra` in `arch/mips/boot/dts/realtek/rtl838x.dtsi` and a
  Lexra bus clock comment in `drivers/clocksource/timer-rtl-otto.c`.
* `rlx`, `RLX`: no relevant MIPS platform support found; matches were unrelated
  display/encoding text outside this SoC area.

MIPS platform findings:

* `CONFIG_MACH_REALTEK_RTL` exists in `arch/mips/Kconfig`.
* Its prompt is `Realtek RTL838x/RTL839x based machines`.
* It selects the generic MIPS platform path, MIPS CPU IRQ, R4K clocksource/event
  timer, device tree support, and `REALTEK_OTTO_TIMER`.
* `arch/mips/generic/board-realtek.c` exists, but its current machine match is
  `realtek,rtl9302-soc`.

MIPS DTS findings:

* `arch/mips/boot/dts/realtek` exists.
* DTS files found there are for `rtl838x` and `rtl930x` style platforms:
  `rtl838x.dtsi`, `rtl930x.dtsi`, `rtl9302c.dtsi`, `cisco_sg220-26.dts`, and
  `cameo-rtl9302c-2x-rtl8224-2xge.dts`.
* No RTL8197F or A2004MU DTS was found.

Realtek driver findings:

* SPI NOR-style support exists for several RTL838x/RTL839x compatibles in
  `drivers/spi/spi-realtek-rtl.c`.
* SPI-NAND support exists for RTL930x-compatible strings in
  `drivers/spi/spi-realtek-rtl-snand.c`.
* Realtek Otto GPIO and interrupt controller support exists in
  `drivers/gpio/gpio-realtek-otto.c` and `drivers/irqchip/irq-realtek-rtl.c`.
* Realtek Otto timer support exists in `drivers/clocksource/timer-rtl-otto.c`.
* Realtek MDIO, PHY, and DSA-related code exists, including RTL930x MDIO and
  external switch families such as `rtl8365mb` and `rtl8366rb`.

These drivers may be useful references. They do not prove support for the
A2004MU Ethernet MAC, the observed stock switch chip id `0x6367-0020`, or the
RTL8197F platform.

A bring-up-ready RTL8197F platform base was not found in the inspected upstream
Linux tree.

## Preliminary Decision

Direct RTL8197F platform support was not found in the current OpenWrt target
tree or the inspected upstream Linux tree.

Existing `target/linux/realtek` may be a structural reference, but it is not a
confirmed base for A2004MU. DTS skeleton work should not be treated as
sufficient until platform, clock, interrupt, timer, UART, SPI, Ethernet, and
switch assumptions are confirmed.

The next decision is whether an RTL8197F-class platform can be based on existing
Realtek RTL infrastructure, whether it needs a separate target/subtarget, or
whether kernel support patches must come first.

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

1. Compare RTL8197F with existing upstream Realtek RTL83xx/RTL93xx platform
   support at the register and boot-architecture level.
2. Decide whether the first code step is kernel platform support or OpenWrt
   target/subtarget scaffolding.
3. Decide target/subtarget placement.
4. Only then draft DTS skeleton and image recipe.
