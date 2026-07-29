# Provenance and licensing review

This is an engineering audit, not legal advice.

## Repository license

Original documentation and tools in this repository are GPL-2.0-only unless a
file says otherwise. The consolidated patch targets OpenWrt, whose buildsystem
is GPL-2.0-only with additional file-level licenses. Notices already present in
upstream or derived files must remain intact.

## Realtek SDK findings

The reference SDK has a GPLv2 license at its root, but that does not override
different terms inside individual files. Relevant files were reviewed
individually:

- the RTL819x new-descriptor `swNic` C and header files grant GPL version 2 or
  later and carry Realtek's 2015 copyright;
- the Sheipa SPI controller and common header grant GPL version 2 and carry
  Realtek's 2015 copyright;
- older NIC and BSP headers include copyright notices without a clear
  file-level redistribution grant;
- RTL8367 switch API files explicitly identify themselves as proprietary.

Therefore the complete SDK must not be treated as uniformly GPL-licensed.
This repository ships none of it.

The Ethernet and SPI drivers are independently structured Linux drivers but
use hardware facts learned from the GPL-licensed SDK files. A whitespace- and
comment-normalized exact-line audit found:

- no 30-character-or-longer identical code line between the new Ethernet
  driver and the GPL `rtl819x_swNic.c`;
- only the generic `#include <linux/platform_device.h>` line shared by the new
  SPI driver and the GPL Sheipa driver;
- no substantive exact line copied from the older SDK NIC driver.

Exact-line comparison cannot prove non-derivation. The source itself accurately
records where descriptor ordering and register behavior follow SDK facts.

The RTL8367 data path uses Linux's DSA/`rtl8365mb` support. Register values
recovered from live hardware and stock execution are documented as observations.
No proprietary RTL8367 SDK source may be added to this repository.

## OpenWrt and loader sources

The LZMA loader material used by the active image recipe is copied at build
time from OpenWrt's generic loader and modified in the build directory. The
unused experimental loader copies were removed from the publication patch.
The original OpenWrt, MIPS, MontaVista, U-Boot, and LZMA notices remain in
their source files.

## Wi-Fi firmware

The build selects `rtl8822be-firmware` from linux-firmware. The binary is not
stored in this repository. Linux-firmware's `WHENCE` marks
`rtw88/rtw8822b_fw.bin` redistributable under
`LICENCE.rtlwifi_firmware.txt`; redistribution must keep its copyright,
disclaimer, non-endorsement, and no-reverse-engineering terms.

## Comparable public projects

Two public RTL819x projects illustrate different disclosure models:

- [`Alexey-Tsarev/openwrt-rtl819x`](https://github.com/Alexey-Tsarev/openwrt-rtl819x)
  publishes an SDK-derived OpenWrt tree, identifies
  `rtk_openwrtSDK_v2.5.tar.gz` as its source, and uses GPL-2.0;
- [`hackpascal/lede-rtl8196c`](https://github.com/hackpascal/lede-rtl8196c)
  states that it used no original Realtek SDK code, rewrote its arch and
  drivers based on the SDK for Linux/LEDE interfaces, and uses GPL-2.0.

Those repositories are useful precedent, not proof that every SDK file is
redistributable or that this project has met its obligations.

## Publication conclusion

The Git repository follows the second disclosure model and is suitable for
public code review under GPL-2.0-only:

- it says plainly that the Realtek SDK was used as a reference;
- it includes no SDK tree or original SDK source file;
- it includes no code identified by the audit as copied from a proprietary
  RTL8367 SDK file;
- its new Linux drivers have GPL SPDX identifiers and retain notices in
  patched upstream files;
- exact normalized-line comparisons found no substantive SDK source line in
  the new Ethernet or SPI implementations.

An experimental firmware image may be published separately from Git history
when its exact corresponding patch, OpenWrt base revision, build configuration,
build instructions, checksums, and applicable notices are published together.
The redistributable Realtek Wi-Fi firmware license must remain available with
that distribution. The current sysupgrade image has hardware regression
coverage; the factory wrapper has only offline structural validation and must
be identified as unverified.

This is an engineering publication decision, not a legal opinion. If future
review identifies copied expression from an SDK file without a redistribution
grant, that material must be removed or relicensed.

## Before public release

- Retain this provenance disclosure and all file-level notices.
- Keep the SDK, stock images, firmware binaries, and device calibration out of
  Git history.
- Obtain legal review before broad binary distribution or if any implementation
  is later found to derive from a proprietary SDK file.
- Include the Realtek firmware license with any redistributed image/package as
  required by its terms.
- State clearly that the project is unofficial and not endorsed by OpenWrt.
