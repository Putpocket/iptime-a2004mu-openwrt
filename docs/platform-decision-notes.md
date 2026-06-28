# Platform Decision Notes

## Goal

Record the current target/subtarget decision options before writing OpenWrt
source patches. This is provisional and based only on clean-room evidence from
stock logs, firmware metadata, OpenWrt inventory, and upstream Linux inventory.

## Current Evidence

* A2004MU uses RTL8197F.
* OpenWrt tree `/home/user/openwrt` has no direct A2004MU or RTL8197F support.
* Upstream Linux tree `/home/user/linux` has no direct RTL8197F or `rtkmipsel`
  support found in the searched areas.
* Upstream Linux has a Realtek MIPS platform path for RTL838x/RTL839x-style
  machines and DTS examples for RTL838x/RTL930x.
* Upstream Linux has Realtek Otto timer, interrupt, GPIO, SPI, MDIO, PHY, and
  DSA-related code paths, but these are not confirmed for RTL8197F or A2004MU.
* The observed A2004MU stock switch chip id `0x6367-0020` is not mapped to a
  confirmed Linux driver path yet.

## Option 1: Extend Existing `target/linux/realtek`

Add an RTL8197F-class subtarget under the existing OpenWrt realtek target.

Pros:

* Reuses existing Realtek MIPS target structure.
* Keeps Realtek-specific image, DTS, board.d, and config work in one target
  family.
* Existing upstream Linux Realtek platform files provide useful structure.

Cons:

* Existing target appears focused on RTL83xx/RTL93xx switch SoCs.
* CPU, clock, interrupt, timer, SPI, Ethernet, and switch compatibility with
  RTL8197F is not confirmed.
* Reusing the target too early may hide platform incompatibilities.

## Option 2: Create A Separate RTL8197F/`rtkmipsel` Target

Create a new OpenWrt target or target family if RTL8197F is sufficiently
different from the existing Realtek RTL83xx/RTL93xx path.

Pros:

* Avoids forcing RTL8197F into an unrelated switch-SoC target.
* Makes unsupported platform pieces explicit.
* Allows a minimal first-bring-up path focused on A2004MU-style router hardware.

Cons:

* More OpenWrt target scaffolding is required.
* More kernel config and image recipe work is needed.
* It may duplicate patterns that could have been reused from `target/linux/realtek`
  if the platform turns out to be close enough.

## Option 3: Implement Kernel Platform Patches First

Defer OpenWrt target placement until the minimum Linux platform support path is
understood or implemented.

Pros:

* Addresses the current blocker directly.
* Reduces the risk of writing a DTS that cannot boot because required platform
  support is absent.
* Makes target/subtarget placement a consequence of actual platform support,
  not naming similarity.

Cons:

* Requires deeper kernel/platform investigation before visible OpenWrt target
  progress.
* The minimum patch scope is still unknown.
* Ethernet and switch support may require separate investigation even after
  basic CPU/platform boot support exists.

## Provisional Recommendation

Treat kernel platform support as the next decision point before DTS-first work.
The supporting design document is
[`rtl8197f-platform-support-plan.md`](rtl8197f-platform-support-plan.md).

The current evidence does not justify assuming that existing OpenWrt
`target/linux/realtek` support is directly usable for RTL8197F. It should remain
a structural reference until CPU/platform, clock, interrupt, timer, UART, SPI,
Ethernet, and switch compatibility are confirmed.

The first implementation step should be platform support investigation and
design. DTS, target/subtarget placement, and image recipe work should follow
only after the CPU/platform, timer, interrupt, and early UART paths are plausible.

## Why DTS-First Is Risky

Writing an A2004MU DTS first can document known hardware facts, but it is not
enough for a bootable mainline-style port if the kernel lacks the required
platform base. The current blockers include:

* CPU/platform compatibility.
* Interrupt controller support.
* Timer and clock support.
* UART binding and early console path.
* SPI NOR controller support.
* Ethernet MAC support.
* Switch/PHY support.
* Memory map and flash partition confirmation.
