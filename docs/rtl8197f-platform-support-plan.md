# RTL8197F Minimal Platform Support Plan

## Goal

* Define the minimum clean-room Linux/OpenWrt platform support needed before
  DTS-first work.
* First milestone remains wired LAN + SSH on A2004MU.

## Evidence Base

This plan is based on clean-room evidence only:

* Stock UART boot log.
* Stock firmware layout.
* OpenWrt target inventory.
* Upstream Linux inventory.
* Existing upstream Realtek RTL83xx/RTL93xx/Otto code as reference only.
* No SDK code copy.

## Current Decision

No direct RTL8197F platform base was found in the inspected OpenWrt or upstream
Linux trees.

Existing Realtek RTL83xx/RTL93xx support is a structural reference, not a
confirmed base for RTL8197F. A DTS skeleton alone is insufficient until the
platform assumptions are resolved.

## Existing Reference Components

The following upstream Linux components are useful reference material. None is
confirmed usable for RTL8197F without register-level and boot-path verification.

* `MACH_REALTEK_RTL`
  * Provides the existing MIPS Kconfig entry for Realtek RTL838x/RTL839x based
    machines.
  * Not confirmed usable for RTL8197F.
  * Verify CPU ISA, endianness, boot entry, memory map, and whether the generic
    MIPS platform path can support RTL8197F.
* `arch/mips/generic/board-realtek.c`
  * Provides a generic Realtek MIPS machine path and current match data for
    RTL930x-style SoCs.
  * Not confirmed usable for RTL8197F.
  * Verify whether RTL8197F needs a new compatible, machine fixups, or a
    separate platform path.
* Realtek DTS examples
  * `arch/mips/boot/dts/realtek/rtl838x.dtsi` and `rtl930x.dtsi` show existing
    Realtek MIPS device tree structure.
  * Not confirmed usable for RTL8197F.
  * Verify register maps, interrupt routing, clocks, UART, SPI, MDIO, and switch
    topology before reusing patterns.
* `drivers/clocksource/timer-rtl-otto.c`
  * Provides Realtek Otto timer support.
  * Not confirmed usable for RTL8197F.
  * Verify RTL8197F timer block, clock rate, clock source, and interrupt wiring.
* `drivers/irqchip/irq-realtek-rtl.c`
  * Provides a Realtek interrupt controller driver for existing compatible
    strings.
  * Not confirmed usable for RTL8197F.
  * Verify register layout, interrupt mapping, CPU IRQ routing, and ack/mask
    semantics.
* `drivers/gpio/gpio-realtek-otto.c`
  * Provides GPIO and GPIO interrupt support for Realtek Otto-family hardware.
  * Not confirmed usable for RTL8197F.
  * Verify GPIO bank layout, polarity, interrupt support, and pin control needs.
* `drivers/spi/spi-realtek-rtl.c`
  * Provides SPI controller support for several RTL838x/RTL839x compatibles.
  * Not confirmed usable for RTL8197F.
  * Verify controller registers, chip-select behavior, clocking, and SPI NOR
    access.
* Realtek MDIO / PHY / DSA references
  * Upstream Linux includes Realtek MDIO, PHY, and DSA-related code such as
    RTL930x MDIO and external switch support families.
  * Not confirmed usable for A2004MU.
  * Verify the A2004MU Ethernet MAC path and stock switch chip id `0x6367-0020`
    before claiming support.

## RTL8197F Required Components

| Component | Current evidence | Reuse candidate | Gap | First action |
| --- | --- | --- | --- | --- |
| CPU/platform | A2004MU uses RTL8197F; no direct upstream support found | Existing Realtek MIPS platform structure | CPU ISA, endian mode, boot entry, and platform init path are unconfirmed | Verify CPU/platform compatibility before writing DTS |
| Machine compatible | No RTL8197F compatible found | New RTL8197F-class compatible, if platform path is viable | Compatible naming and machine match are undefined | Define only after platform entry is plausible |
| Memory | Stock hardware evidence says 64 MB DDR2 | DTS memory node | Memory base, reserved regions, and bootloader handoff need confirmation | Extract from boot log and platform behavior |
| UART | UART is observed at 38400 8N1 | Standard serial binding if registers match | UART base, IRQ, clock, and early console path are unknown | Identify UART block and clock source |
| Interrupt controller | No RTL8197F-specific support found | `irq-realtek-rtl` as reference | Register layout and IRQ routing are unknown | Compare interrupt controller behavior before reuse |
| Timer/clock | No RTL8197F-specific timer support found | R4K timer and `timer-rtl-otto` as references | Clock source, clockevent, and fixed clock assumptions are unknown | Confirm timer path required for kernel start |
| GPIO/pinctrl | LED probe warnings in stock log imply GPIO use, but mapping is incomplete | `gpio-realtek-otto`, `gpio-leds`, `gpio-keys` patterns | GPIO bank layout and pinmux are unknown | Inventory GPIO registers and board wiring |
| SPI NOR | Stock flash is 8 MB SPI NOR | `spi-realtek-rtl` as reference plus SPI NOR framework | Controller compatibility is unknown | Verify SPI controller register map and flash access |
| MTD partitions | Stock layout and firmware region are documented | Fixed-partitions in DTS/OpenWrt image plan | Final OpenWrt partition policy is not decided | Preserve known layout in first design notes |
| Ethernet MAC | Stock log shows `eth0`, `eth1`, and `peth0` mapping | Existing Realtek network code as reference | RTL8197F MAC driver path is unconfirmed | Identify MAC registers and Linux driver strategy |
| Switch/PHY/MDIO | Stock switch chip id `0x6367-0020`; Ethernet comes up in stock boot | Realtek MDIO, PHY, DSA references | Switch identity, bus, and PHY mapping are unconfirmed | Map switch/MDIO topology from logs and clean-room observation |
| Reset/watchdog | Stock log can show reboot/watchdog hints, but support is not mapped | Generic watchdog/reset frameworks | Register block and reset lines are unknown | Identify watchdog/reset blocks before relying on them |
| LED/button | Board likely has GPIO LEDs/buttons, but mapping is incomplete | `gpio-leds`, `gpio-keys`, board.d LED patterns | GPIO numbers and active levels are unknown | Defer until GPIO path is understood |
| Image recipe | No mainline A2004MU image exists | OpenWrt image recipe patterns | Target/subtarget and image/header strategy are undecided | Wait for platform and target decision |
| board.d network defaults | First milestone is wired LAN + SSH | OpenWrt `board.d` network defaults | Interface naming and switch topology are unknown | Add only after Ethernet path is known |

## Proposed Implementation Order

1. Confirm CPU/platform and machine entry path.
2. Confirm timer/interrupt/early UART path.
3. Define minimal DTS only after platform entry is plausible.
4. Add SPI NOR and partition map.
5. Add initramfs/image recipe.
6. Bring up kernel with UART log.
7. Add Ethernet MAC/switch/PHY path.
8. Add board.d network defaults.
9. Only then test wired LAN + SSH.
10. Defer Wi-Fi and LuCI.

## Target/Subtarget Options

* Extend existing `target/linux/realtek` with a new RTL8197F-class subtarget.
* Create a separate RTL8197F/`rtkmipsel`-style target.
* Implement kernel platform patches first before final target decision.

The provisional recommendation is:

1. Decide the platform support path first.
2. Decide target/subtarget placement after the platform path is plausible.
3. Draft DTS and image recipe only after those decisions.

## Clean-room Constraints

* Do not copy SDK driver code.
* Use observed logs, public Linux/OpenWrt APIs, and independently written code.
* Keep local firmware/SDK artifacts outside this repository.
* Document the source of each hardware or software fact.

## Stop Conditions

* If no compatible CPU/platform entry can be established, stop before DTS.
* If timer/IRQ/UART path is unknown, stop before image recipe.
* If SPI NOR path is unknown, stop before flash layout implementation.
* If Ethernet/switch path is unknown, wired LAN + SSH cannot be claimed.
