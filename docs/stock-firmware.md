# Stock Firmware Notes

This document records GitHub-safe observations about local ipTIME A2004MU stock
firmware. Do not commit the stock firmware image, extracted rootfs, binaries,
shared libraries, or generated firmware outputs.

Local stock firmware and extraction artifacts should stay outside this
repository, currently under:

```text
../iptime-a2004mu-local-artifacts/
```

## Safe Inspection

Inspect a local stock firmware file without modifying it:

```sh
python3 tools/inspect_stock_firmware.py /path/to/local/a2004m_ml_15_352.bin
```

The inspector prints:

* file size
* SHA256
* model and version fields
* Protect2 magic and checksum fields
* rootfs absolute offset
* check length
* primary checksum field
* kernel descriptor string
* firmware offset field bytes near `0x40050`
* detected SquashFS magic offsets

## Observed Version 15.352 Facts

Observed from local analysis of stock firmware version 15.352:

| Item | Observation |
| --- | --- |
| model field | `a2004m` |
| version field | `15.352` |
| firmware check offset | `0x40000` |
| rootfs offset | `0x2c0000` |
| root filesystem | SquashFS |
| flash size | 8 MB |

These are observations from one stock version. The rootfs offset is known to
vary between observations, so tooling must detect or read it rather than
hardcode it.

## Layout Summary

Observed stock flash layout:

```text
0x00000-0x1ffff  boot
0x20000-0x2ffff  factory
0x30000-0x3ffff  config/data
0x40000-0x7fffff firmware
```

The lower regions may contain bootloader, factory data, calibration data, MAC
addresses, or device-specific configuration.

## Current Interpretation

The stock firmware appears to use a Realtek vendor SDK-based kernel and
userspace. Hardware observations derived from local rootfs analysis are
summarized in `docs/hardware.md`; raw extracted rootfs contents must remain out
of git.

No generated image from this repository is flash-verified.
