# Stock Firmware Analysis / 정펌 펌웨어 분석

## Firmware / 펌웨어

* File / 파일: `a2004m_ml_15_352.bin`
* Model string / 모델 문자열: `a2004m`
* Version string / 버전 문자열: `15.352`
* Firmware check offset / 펌웨어 검사 오프셋: `0x40000`
* LZMA kernel offset / LZMA 커널 오프셋: `0x42860`
* SquashFS rootfs offset / SquashFS 루트 파일시스템 오프셋: `0x2C0000`
* Root filesystem / 루트 파일시스템: SquashFS 4.0, xz compression
* Flash size / 플래시 크기: 8MB

## Binwalk Result / binwalk 결과

```text
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
31000         0x7918          CRC32 polynomial table, little endian
32096         0x7D60          gzip compressed data, maximum compression, from Unix, last modified: 2021-05-27 05:32:09
272480        0x42860         LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 8481020 bytes
2883584       0x2C0000        Squashfs filesystem, little endian, version 4.0, compression:xz, size: 4817692 bytes, 840 inodes, blocksize: 131072 bytes, created: 2026-06-16 10:11:04
```

## Firmware Header / 펌웨어 헤더

The stock firmware header starts at offset `0x40000`.

정펌 펌웨어 헤더는 `0x40000` 오프셋에서 시작합니다.

```text
00040000: 61 32 30 30 34 6d 00 00 31 35 2e 33 35 32 00 00  a2004m..15.352..
```

This contains the model string `a2004m` and version string `15.352`.

이 영역에는 모델 문자열 `a2004m`과 버전 문자열 `15.352`가 포함되어 있습니다.

The bootloader also checks firmware from offset `0x40000`.

부트로더도 `0x40000` 오프셋부터 펌웨어를 검사합니다.

```text
Check Firmware(00040000)
```

## Kernel Command Line / 커널 커맨드라인

Observed from stock bootlog:

정펌 부트로그에서 확인된 커널 커맨드라인:

```text
console=ttyS0,38400 root=/dev/mtdblock1
```

This confirms that the serial console uses `38400 8N1`.

이를 통해 시리얼 콘솔이 `38400 8N1`을 사용한다는 것을 확인했습니다.

## Observed Firmware Layout / 확인된 펌웨어 구조

```text
0x000000 ~ 0x03ffff : boot / factory / config area
0x040000            : firmware header
0x042860            : LZMA compressed kernel area
0x2c0000            : SquashFS rootfs
```

This layout is based on the official firmware image and bootlog observations.

이 구조는 공식 펌웨어 이미지 분석과 부트로그에서 확인한 내용을 기준으로 작성했습니다.

## Extracted Rootfs Notes / 추출한 rootfs 메모

The SquashFS root filesystem was extracted from offset `0x2C0000`.

SquashFS 루트 파일시스템은 `0x2C0000` 오프셋에서 추출했습니다.

`unsquashfs` produced warnings for device nodes because it was run as a normal user, but regular files and configuration files were extracted.

일반 사용자 권한으로 `unsquashfs`를 실행했기 때문에 `/dev` 장치 파일 생성 경고가 발생했지만, 일반 파일과 설정 파일은 추출되었습니다.

## Hardware Information from rootfs / rootfs에서 확인한 하드웨어 정보

From `default/var/run/si/hw`:

```text
chipset.soc.name=rtl8197f
chipset.eswitch.name=rtl8367r
chipset.eswitch.max_speed=1000
chipset.wl[2g].name=rtl8197f
chipset.wl[5g].name=rtl8812br
board.flash[0].type=spi
board.flash[0].size=8
```

Summary:

```text
SoC: Realtek RTL8197F
External switch: Realtek RTL8367R
2.4GHz Wi-Fi: RTL8197F
5GHz Wi-Fi: RTL8812BR
Flash: 8MB SPI NOR
```

## MTD Layout from rootfs / rootfs에서 확인한 MTD 레이아웃

From `default/var/run/si/sw`:

```text
mtd.all.name=all
mtd.all.offset=0
mtd.all.size=0x800000

mtd.boot.name=boot
mtd.boot.offset=0
mtd.boot.size=0x20000

mtd.factory.name=factory
mtd.factory.offset=0x20000
mtd.factory.size=0x10000

mtd.data.name=config
mtd.data.offset=0x30000
mtd.data.size=0x10000

mtd.firmware[0].name=firmware
mtd.firmware[0].offset=0x40000
mtd.firmware[0].size=0x7c0000
```

Estimated flash layout:

```text
0x000000 ~ 0x01ffff : boot
0x020000 ~ 0x02ffff : factory
0x030000 ~ 0x03ffff : config/data
0x040000 ~ 0x7fffff : firmware
```

This matches the bootloader firmware check offset:

```text
Check Firmware(00040000)
```

## Kernel Modules / 커널 모듈

No `.ko` kernel module files were found in the extracted rootfs.

추출한 rootfs 안에서는 `.ko` 커널 모듈 파일이 발견되지 않았습니다.

This suggests that the Ethernet, switch, and WLAN drivers are likely built into the stock kernel.

이는 유선 LAN, 스위치, 무선 드라이버가 정펌 커널에 내장되어 있을 가능성이 높다는 뜻입니다.

## Important Files / 주요 파일

The extracted rootfs contains several files that may be useful for further analysis.

추출한 rootfs에는 추가 분석에 유용할 수 있는 파일들이 있습니다.

```text
default/var/run/si/hw
default/var/run/si/sw
default/sbin/prepare_upgrade.sh
default/sbin/prepare_auto_upgrade.sh
sbin/firmup
sbin/iwpriv
sbin/83xxreg
sbin/gpioctl
default/etc/econf/interface.lan.conf
default/etc/econf/interface.wan1.conf
default/etc/econf/wireless/bss_2g.1.conf
default/etc/econf/wireless/bss_5g.1.conf
```

## Current Interpretation / 현재 해석

The stock firmware appears to use a Realtek vendor SDK-based kernel and userspace.

정펌은 Realtek 벤더 SDK 기반 커널과 사용자 공간을 사용하는 것으로 보입니다.

The Ethernet, switch, and wireless drivers are probably built into the kernel rather than provided as separate `.ko` modules.

유선 LAN, 스위치, 무선 드라이버는 별도 `.ko` 모듈이 아니라 커널에 내장되어 있을 가능성이 높습니다.

The firmware area starts at `0x40000`, while `boot`, `factory`, and `config/data` occupy the lower flash area.

펌웨어 영역은 `0x40000`에서 시작하며, 그 앞쪽 영역은 `boot`, `factory`, `config/data`로 사용되는 것으로 보입니다.

## Do Not Flash Yet / 아직 플래시 금지

Do not flash any custom image until the firmware header, checksum, and recovery method are understood.

펌웨어 헤더, 체크섬, 복구 방법이 확인되기 전까지 커스텀 이미지를 플래시에 쓰지 마세요.

Do not overwrite the lower flash regions.

하위 플래시 영역을 덮어쓰지 마세요.

```text
0x000000 ~ 0x01ffff : boot
0x020000 ~ 0x02ffff : factory
0x030000 ~ 0x03ffff : config/data
```

These areas may contain the bootloader, factory data, MAC addresses, calibration data, or device-specific configuration.

이 영역에는 부트로더, 공장 설정, MAC 주소, 보정값, 장치별 설정이 포함되어 있을 수 있습니다.

