# A2004MU OpenWrt Bring-up Plan

This document defines a conservative bring-up plan for ipTIME A2004MU clean-room
OpenWrt research. It is not a device-write procedure.

## Current Goals

* Confirm OpenWrt kernel boot.
* Confirm rootfs mount.
* Confirm wired LAN.
* Confirm SSH access.

## Verified So Far

* Stock model field: `a2004m`
* Stock rootfs offset: `0x2c0000`
* Stock boot log collected and analyzed as `booted`
* Stock boot log shows SquashFS root mounted read-only
* Stock boot log shows Ethernet devices and switch evidence
* Side-path SDK image evidence: `AP-fw` starts with `cs6c`
* Side-path SDK image evidence: SquashFS offset `0x19c000`
* Side-path checksum candidate research: `MATCH`

The SDK and wrapper observations are evidence only. They are not the primary
OpenWrt porting path.

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

## Analyzer Heuristics

`tools/analyze_uart_boot_log.py` is a triage helper. Its status is heuristic,
not a final boot verdict. Stock firmware logs may contain benign warning or
error strings such as SquashFS xattr warnings, iptables rule warnings, or LED
probe errors. Prioritize panic, rootfs mount failure, bootloader rejection, and
reboot-loop evidence when deciding whether a boot log indicates a critical
failure.

## Next Decisions

* Bootloader rejection indicates an image wrapper/header problem.
* Kernel panic indicates a likely DTS or kernel config problem.
* Rootfs mount failure indicates an offset, partition, or rootfs problem.
* Missing LAN indicates a likely switch, PHY, DTS, or network config problem.
* Missing SSH indicates a likely network, dropbear, or default config problem.
