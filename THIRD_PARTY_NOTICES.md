# Third-party notices

Git history contains a patch against OpenWrt and build metadata, not a complete
OpenWrt source tree, stock firmware, SDK tree, or built firmware image.
Prerelease images may be distributed separately as GitHub release assets. Such
a release must point to the corresponding source revision and retain the
notices below.

- OpenWrt is GPL-2.0-only at the buildsystem level; additional licenses apply
  to individual components.
- The active image recipe reuses OpenWrt's generic MIPS LZMA loader at build
  time. Source-file copyright and license notices are retained.
- LZMA SDK decoder files present in upstream OpenWrt retain Igor Pavlov's
  notices and license terms.
- The selected RTL8822B firmware comes from linux-firmware and is
  redistributable only under `LICENCE.rtlwifi_firmware.txt`; its text is
  included as `LICENSES/Realtek-rtlwifi-firmware`.
- Realtek RTL819x GPL SDK files were used as documented hardware references but
  are not included.

The project release is a convenience distribution, not an assertion that every
binary component is GPL-licensed. See `docs/provenance-and-licensing.md` for
the detailed audit and source/publication boundary.
