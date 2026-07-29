# Status

Last reviewed: 2026-07-29

## Publication decision

Ready for public source review and an explicitly identified prerelease build,
with the SDK provenance disclosure, GPL source offer, third-party notices, and
Realtek Wi-Fi firmware license retained. The sysupgrade image below passed the
listed hardware tests. The current factory wrapper passed offline structural
checks but has not been installed from stock firmware after the final
late-init change, so it must remain clearly marked unverified.

## Last hardware-tested build

- OpenWrt base: `6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2`
- reported revision: `r35121+23-6e9fd1c3ba`
- kernel: `6.18.36`
- target: `rtl819x/rtl8197f`
- board: `iptime,a2004mu`
- sysupgrade size: `7,864,592` bytes
- sysupgrade SHA-256:
  `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`

## Current source-publication build

- build result: PASS
- clean-base patch apply and `git diff --check`: PASS
- factory offline arithmetic/self-check: PASS
- sysupgrade size: `7,864,592` bytes
- sysupgrade SHA-256:
  `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`
- factory size: `8,126,464` bytes
- factory SHA-256:
  `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`

This build removes mac80211 debugfs and mesh support. It also adds an
A2004MU-only late-init guard that waits for netifd after first-boot JFFS2
initialization and restarts networking only if the LAN ubus object still does
not appear. The sysupgrade hash identifies the installed hardware-tested
image. The factory hash identifies an offline-validated wrapper, not a
hardware-tested installation image.

## Passed on hardware

- bootloader validation and normal boot;
- repeated normal reboot with persistent JFFS2 overlay;
- DHCP and SSH;
- LAN1 through LAN4 and WAN link/communication tests at 1 Gbit/s full duplex;
- interrupt-driven Ethernet receive and transmit;
- five consecutive 10 MiB transfers with matching hashes;
- no observed Ethernet FCS, symbol, or discard errors in the stress test;
- split-MTD `sysupgrade -n`, including full-block pipe handling;
- erased-overlay first boot after `sysupgrade -n`, without UART intervention;
- late-init network guard present and no-op when netifd initializes normally;
- RTL8822BE PCIe discovery, firmware load, NVMEM calibration, and 5 GHz AP
  start.

## Remaining release gates

1. Install the final factory wrapper through the stock web UI with UART
   recovery available; its current validation is offline only.
2. Repeat wired stress and all five physical port tests on the final hash.
3. Test a real 5 GHz client with WPA2/WPA3 and measure throughput.
4. Measure LAN-to-LAN and WAN-to-LAN forwarding with two independent endpoints.
5. Resolve whether all register-init tables may be distributed from their
   documented observation sources; obtain legal review if distributing
   binaries broadly.
6. Keep Wi-Fi disabled by default unless a secure first-boot credential design
   is added.

## Operational warnings

- Always use `sysupgrade -n --test IMAGE` before `sysupgrade -n IMAGE`.
- Configuration-preserving sysupgrade is intentionally unsupported.
- Do not restore KALLSYMS without rechecking the 2,816 KiB kernel partition.
- Do not enable speculative HWNAT code from the vendor SDK.
- The factory image path is device- and stock-version-sensitive. Treat it as
  an unverified installation path that requires recovery capability, not a
  universal installer.
