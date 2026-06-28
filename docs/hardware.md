# Hardware Notes

These notes describe observed ipTIME A2004MU hardware and bootloader behavior.
They are research notes, not flashing instructions.

## Device

* Device: ipTIME A2004MU
* Board alias: `a2004m`
* SoC: Realtek RTL8197F
* DRAM: 64 MB DDR2 533 MHz
* Flash: xmc25qh64, 8 MB SPI NOR
* Flash erase size: 64 KB
* Bootloader prompt: `<RealTek>`
* UART: 38400 8N1

## UART

J1 header, counted top to bottom with the LAN ports oriented at 9 o'clock:

| Pin | Function |
| --- | --- |
| J1-1 | VCC candidate, do not connect |
| J1-2 | Router TX |
| J1-3 | Router RX |
| J1-4 | GND |

Observed working USB-UART wiring:

```text
USB-UART GND -> J1-4
USB-UART RXD -> J1-2
USB-UART TXD -> J1-3
USB-UART VCC -> do not connect
```

## Bootloader

The bootloader prompt is:

```text
<RealTek>
```

UART settings:

```text
38400 8N1
```

Observed behavior:

* `ESC` during early boot enters the bootloader prompt.
* Ethernet initialization was observed.
* RAM upload boot path is not currently available.
* `XMOD` appears in help but was not usable during testing.
* TFTP upload was not usable during testing.

## Forbidden Bootloader Commands

Do not generate or run commands using any of the following:

```text
FLW
ERASECHIP
ERASESECTOR
SPICLB
E8
AUTOBURN 1
```

These commands can write to or erase flash. This repository does not provide
flashing instructions.

## Flash Layout

Observed stock firmware flash layout:

| Region | Range | Notes |
| --- | --- | --- |
| boot | `0x00000-0x1ffff` | bootloader area |
| factory | `0x20000-0x2ffff` | calibration/factory data |
| config/data | `0x30000-0x3ffff` | device configuration/data |
| firmware | `0x40000-0x7fffff` | firmware region |

The firmware region starts at `0x40000`. Do not overwrite below `0x40000`.

Known rootfs observations:

* Stock firmware version 15.352 had rootfs at absolute offset `0x2c0000`.
* An older bootlog showed rootfs offset `0x270000`.

The rootfs offset must be read from the image metadata or detected from the
image. Do not hardcode it.
