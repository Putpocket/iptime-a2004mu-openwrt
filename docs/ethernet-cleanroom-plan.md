# RTL8197F Ethernet Clean-room Plan

## Goal

Define what is needed to implement enough RTL8197F Ethernet support for the
A2004MU first milestone: wired LAN and SSH after installation through the stock
web firmware upgrade path.

## Known Facts

* Stock boot logs show `eth0` and `eth1`.
* Stock boot logs show `[peth0]` mapped to `[eth1]`.
* Stock boot logs show switch API version `v1.2.12`.
* Stock boot logs show switch chip id `0x6367-0020`.
* Current OpenWrt and upstream Linux inventories did not find RTL8197F MAC or
  switch support.
* Existing OpenWrt `target/linux/realtek` Ethernet, PCS, MDIO, and DSA paths
  are RTL83xx/RTL93xx/Otto-oriented.

## Non-imported Artifacts

Local audit records contain RTL819x Ethernet and switch-related SDK paths,
including:

* `drivers/net/rtl819x/`
* `drivers/net/rtl819x/RTL8370_RTL8367_API/`
* `rtl865x_*` L2/L3/VLAN/netif-related files
* `smi.c` / `smi.h`
* stock rootfs `plugin_switch.so`

These artifacts are reference-only. Do not copy SDK/vendor source into this
repo or into the OpenWrt tree.

## License Boundary

Do not reuse UNKNOWN-license SDK code, binary plugin behavior, or patch hunks.
Allowed use is limited to high-level facts such as file names, visible module
roles, interface names, stock log behavior, and independently verified runtime
facts.

Clean-room implementation must use public Linux/OpenWrt networking APIs,
observed behavior, and independently written code.

## Why RTL838X/Otto Ethernet Is Not Used

The existing OpenWrt realtek Ethernet path matches RTL83xx/RTL93xx/Otto
families. No RTL8197F compatible string or direct MAC support was found. Stock
logs prove that Ethernet works in the vendor firmware, but they do not prove
that RTL8197F is compatible with `NET_RTL838X`, `PCS_RTL_OTTO`, or the Otto
MDIO/DSA path.

## Likely Architecture Hypotheses

These are hypotheses, not implementation facts:

* RTL8197F internal Ethernet MAC connected to a Realtek switch.
* The observed switch chip id `0x6367-0020` may identify the switching block or
  an attached Realtek switch/PHY component.
* `eth0`, `eth1`, and `peth0 -> eth1` suggest multiple logical interfaces or a
  vendor abstraction over a physical MAC/switch topology.
* LAN/WAN VLAN separation may be configured by vendor switch initialization
  rather than simple netdev defaults.

## Existing OpenWrt Framework Candidates

* A clean-room netdev driver for the RTL8197F MAC.
* MDIO bus support if the switch/PHY is MDIO-accessible.
* Linux PHYLIB/phylink if the MAC-to-switch link can be described cleanly.
* DSA if the switch maps to a supported Realtek switch family.
* Existing `rtl8365mb`, `rtl8366rb`, or swconfig-style Realtek switch code only
  if the actual switch model is proven compatible.

## Required Facts Before Implementation

* RTL8197F Ethernet MAC register block.
* DMA descriptor model and interrupt behavior.
* MDIO or SMI access method.
* Actual switch chip/model behind id `0x6367-0020`.
* CPU port and PHY interface mode.
* LAN/WAN port mapping.
* VLAN defaults needed for first LAN access.
* MAC address source.
* Required initialization order from boot log or clean-room observation.

## LAN/SSH Status

Wired LAN and SSH remain blocked until a defensible RTL8197F MAC and switch/PHY
path is defined. A kernel that compiles without Ethernet is only a platform
scaffold and does not meet the first milestone.

## Next Step Checklist

1. Map stock boot network lines into a timeline: MAC init, switch init, netdev
   creation, link events, and bridge/VLAN setup.
2. Identify the real switch model corresponding to `0x6367-0020`.
3. Find license-compatible/public evidence for RTL8197F MAC registers and DMA.
4. Decide whether the switch path should be DSA, PHYLIB-only, or a minimal
   target-local driver.
5. Draft a minimal netdev/MDIO design without SDK source reuse.
6. Only then add OpenWrt/Linux Ethernet code.
