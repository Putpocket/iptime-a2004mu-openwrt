# A2004MU Mainline OpenWrt Porting Plan

## Goal

* Latest/official-style OpenWrt support for ipTIME A2004MU.
* Clean-room implementation of missing support.
* First milestone: kernel boot, rootfs mount, wired LAN, and SSH.

## Non-Goals

* Do not deploy old SDK `AP-fw` as the final solution.
* Do not copy proprietary SDK driver code.
* Do not focus on Wi-Fi for the first milestone.
* Do not produce device-write instructions here.

## Known Hardware

* SoC: RTL8197F
* Board alias: `a2004m`
* RAM: 64 MB DDR2
* Flash: 8 MB SPI NOR
* UART: 38400 8N1
* Switch evidence: chip id `0x6367-0020`
* Ethernet evidence: `eth0`, `eth1`, `peth0 -> eth1` mapping

## Evidence From Stock Boot

* `rtkxxpart` partitions on `m25p80`
* SquashFS root mounted
* VFS mounted root read-only
* Switch API version `v1.2.12`
* Ethernet devices added
* No kernel panic in the captured stock boot log

## Evidence From Firmware/Image Research

* Stock rootfs offset `0x2c0000`
* SDK `AP-fw` `cs6c` header
* SDK `AP-fw` SquashFS offset `0x19c000`
* `linuxpart=0x40000`
* `hwpart=0x20000`
* Checksum and wrapper research is side-path evidence only

## Mainline OpenWrt Missing Pieces

Expected missing pieces:

* Target/subtarget decision for RTL8197F
* Kernel platform support
* Clock, timer, and interrupt support if missing
* UART binding
* SPI NOR controller support or binding
* Flash partition map
* DTS for A2004MU
* Image recipe
* Network defaults
* Ethernet MAC support
* Switch/PHY support
* LED/button definitions
* Initramfs, factory, and sysupgrade strategy

## First Bring-up Scope

* Kernel starts
* Kernel command line is correct
* MTD partitions are visible
* Rootfs mounts
* Ethernet interface appears
* LAN link comes up
* SSH/dropbear is reachable

## Clean-room Rules

* Do not copy SDK driver code.
* Use stock logs, observed behavior, public kernel/OpenWrt APIs, and
  independently written code.
* SDK may be used only as reference to understand behavior.
* Document what facts came from logs versus what was implemented directly.

## Work Breakdown

1. Inventory latest OpenWrt tree for existing RTL8197F/Realtek support.
   Completed for local tree `/home/user/openwrt`; no direct A2004MU/RTL8197F
   support was found in `target/linux`.
2. Decide target/subtarget strategy.
3. Draft A2004MU DTS.
4. Define flash partitions from stock evidence.
5. Add image recipe skeleton.
6. Add network defaults.
7. Identify Ethernet/switch path.
8. Implement or wire minimal Ethernet support.
9. Build initramfs image first.
10. Boot with UART logging.
11. Debug rootfs, network, and SSH.
12. Only later consider factory/sysupgrade and Wi-Fi.

The next concrete step is target/subtarget decision and DTS skeleton design.

## Stop Conditions

* If bootloader rejects image: image/header problem.
* If Linux does not start: kernel load/platform problem.
* If panic: kernel, DTS, or config problem.
* If VFS mount fails: partition or rootfs problem.
* If LAN is missing: Ethernet, switch, or PHY problem.
* If SSH is missing: network, dropbear, or default config problem.
