# RTL8197F Watchdog Clean-room Plan

## Goal

Define what is needed to implement RTL8197F watchdog handling without importing
SDK/vendor source. Watchdog remains a boot-risk blocker for the A2004MU
OpenWrt path because an incorrect or missing policy can cause reset loops.

## Known Facts

* Stock UART identifies the SoC as RTL8197F and CPU as MIPS 24Kc.
* Stock UART logs collected so far do not show a clear watchdog driver line.
* The stock rootfs contains a watchdog userspace binary.
* The rootfs watchdog binary contains references to `/proc/watchdog_kick` and
  `/proc/watchdog_cmd`.
* Local audit records list an RTL819x watchdog source file and two watchdog
  patches in the SDK-derived artifact set.
* The audit records show a `MODULE_LICENSE("GPL v2")` string for
  `rtl819x_wdt.c`, while licensecheck reports the file and related patches as
  UNKNOWN.
* OpenWrt `REALTEK_OTTO_WDT` is selected by existing RTL83xx/RTL93xx realtek
  subtargets and is described by RTL838x/RTL839x/RTL930x/RTL931x DTS
  compatibles, not by RTL8197F evidence.

## Non-imported Artifacts

These artifacts are reference-only and must not be copied into this repo or
into the OpenWrt tree:

* `target/linux/rtkmipsel/files/drivers/watchdog/rtl819x_wdt.c`
* `target/linux/rtkmipsel/patches-3.10/120-rtk-819x_watchdog.patch`
* `target/linux/rtkmipsel/patches-3.10/990-watchdog_panic_workaround.patch`
* stock rootfs `/bin/watchdog`

Allowed use is limited to high-level facts such as file names, visible license
signals, interface names, driver role, and integration shape.

## License Boundary

Do not reuse code or patch hunks from UNKNOWN-license artifacts. Even where a
GPL module string is visible, treat the SDK tree as reference-only unless the
full file provenance and license are separately cleared.

Clean-room implementation must use public Linux watchdog APIs, observed stock
behavior, and independently written code.

## Why REALTEK_OTTO_WDT Is Not Used

`REALTEK_OTTO_WDT` belongs to the existing OpenWrt realtek switch-SoC support
path. The current tree shows compatibles for RTL83xx/RTL93xx families, and no
RTL8197F watchdog compatible was found. Selecting it for RTL8197F would be a
hardware compatibility guess.

## Required Facts Before Implementation

* RTL8197F watchdog register block location.
* Register layout for enable, stop, ping, timeout, and reset behavior.
* Clock source and timeout unit.
* Whether the watchdog is already active when Linux starts.
* Whether userspace compatibility with `/proc/watchdog_kick` or
  `/proc/watchdog_cmd` is required, or whether standard `/dev/watchdog` is
  enough for first bring-up.
* Whether a panic/reboot workaround is required for this SoC, and whether it
  can be implemented through standard kernel restart/watchdog APIs.
* DTS binding shape and compatible string, if a devicetree driver is used.

## Proposed OpenWrt Implementation Shape

* Add a new RTL8197F-specific watchdog driver or a clearly isolated variant,
  not `REALTEK_OTTO_WDT`.
* Use standard Linux watchdog framework objects such as `watchdog_device` and
  `watchdog_ops`.
* Prefer devicetree probing with a new compatible such as a provisional
  RTL8197F-specific string, only after register facts are known.
* Keep legacy `/proc` compatibility out of the first driver unless stock
  behavior proves it is required for boot stability.
* Keep panic/reboot handling separate from the watchdog driver unless there is
  a public, defensible reason to combine them.

## Unresolved Risks

* Incorrect watchdog handling may cause reset loops.
* Disabling watchdog support may also be unsafe if the bootloader leaves it
  running.
* The existing SDK references may describe behavior but cannot be imported.
* Without confirmed registers and timeout units, implementation should not
  proceed.

## Next Step Checklist

1. Find license-compatible/public RTL8197F watchdog register documentation.
2. Correlate any register names with stock boot behavior without copying SDK
   implementation.
3. Decide whether first bring-up needs early watchdog petting or only a normal
   watchdog driver.
4. Draft a minimal clean-room driver design.
5. Only then add OpenWrt/Linux code.
