# A2004MU OpenWrt Bring-up Plan

This document defines a conservative bring-up plan for ipTIME A2004MU OpenWrt
research. It is not a device-write procedure.

## Current Goals

* Confirm OpenWrt kernel boot.
* Confirm rootfs mount.
* Confirm wired LAN.
* Confirm SSH access.

## Verified So Far

* Stock model field: `a2004m`
* Stock rootfs offset: `0x2c0000`
* SDK `AP-fw` starts with `cs6c`
* SDK SquashFS offset: `0x19c000`
* Candidate payload start: `0x40038`
* Candidate rootfs offset: `0x1dc038`
* Candidate rootfs calculation: `0x40038 + 0x19c000 = 0x1dc038`
* Observed checksum candidates: `MATCH`

## Not Yet Verified

* Bootloader acceptance
* Kernel boot
* MTD partition correctness
* Rootfs mount
* Ethernet switch / PHY
* LAN IP assignment
* SSH availability
* Recovery path under failure

## Required Preparation Before Testing

* UART connected at 38400 8N1.
* Stock boot log saved.
* Candidate boot log capture plan prepared.
* Stable power available.
* Recovery means prepared and understood before any device-risk work.
* Prohibited bootloader command names for this project: `FLW`, `ERASECHIP`,
  `ERASESECTOR`, `SPICLB`, `E8`, `AUTOBURN 1`.

Do not document usage syntax for prohibited write, erase, or update operations
in this repository.

## Success Criteria

* UART shows Linux kernel start.
* OpenWrt banner or init logs appear.
* Rootfs mount succeeds.
* Network interfaces are created.
* LAN link comes up.
* SSH daemon starts.

## Failure Criteria

* Bootloader rejection.
* Kernel decompress/load failure.
* Panic.
* Rootfs mount failure.
* Watchdog reboot loop.
* No Ethernet.

## First Boot Log Keywords

Look for:

```text
Linux version
Kernel command line
mtd
SquashFS
VFS
init
eth
switch
PHY
dropbear
procd
panic
reboot
watchdog
```

## Next Decisions

* Bootloader rejection indicates an image wrapper/header problem.
* Kernel panic indicates a likely DTS or kernel config problem.
* Rootfs mount failure indicates an offset, partition, or rootfs problem.
* Missing LAN indicates a likely switch, PHY, DTS, or network config problem.
* Missing SSH indicates a likely network, dropbear, or default config problem.
