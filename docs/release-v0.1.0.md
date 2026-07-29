# A2004MU OpenWrt v0.1.0

## Downloads / 다운로드

- **First install from stock firmware / 정품 펌웨어에서 처음 설치:**
  [`a2004mu-openwrt-factory.bin`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-factory.bin)
- **Upgrade from OpenWrt / OpenWrt에서 업데이트:**
  [`a2004mu-openwrt-sysupgrade.bin`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-sysupgrade.bin)
- **Checksums / 체크섬:**
  [`SHA256SUMS`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/SHA256SUMS)

## English

This is an unofficial build for the ipTIME A2004MU only. Keep UART
recovery available. Back up the stock firmware and device-specific data before
writing flash. This project is not affiliated with or endorsed by OpenWrt,
ipTIME, or Realtek.

### Assets

- `a2004mu-openwrt-sysupgrade.bin`
  - size: 7,864,592 bytes
  - SHA-256:
    `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`
  - hardware-tested with erased-overlay first boot and a subsequent normal
    reboot
- `a2004mu-openwrt-factory.bin`
  - size: 8,126,464 bytes
  - SHA-256:
    `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`
  - factory wrapper for stock web installation; passed offline structural
    checks but this exact final image has not been installed from stock
    firmware

For sysupgrade, first run:

```sh
sysupgrade -n --test /tmp/a2004mu-openwrt-sysupgrade.bin
```

Proceed only if the test passes, and use `sysupgrade -n`. Preserving settings
is intentionally unsupported. Wi-Fi is disabled by default. The integrated
2.4 GHz radio is unsupported; only the separate RTL8822BE 5 GHz radio has been
brought up.

The factory wrapper is specific to the A2004MU stock web-upgrade format. It is
not a universal installer, and compatibility with every stock version and
hardware revision is not guaranteed. Do not use it without serial recovery and
a verified stock recovery path.

### First install from stock firmware

1. Verify that the device is an ipTIME A2004MU running stock firmware.
2. Download the `factory.bin` asset above and verify its SHA-256.
3. Use a wired LAN connection and open the stock firmware's manual
   firmware-upgrade page.
4. Select the factory image, start the upgrade, and do not disconnect power.
   The page or UART may remain quiet during validation and writing; wait for
   the router to reboot by itself.
5. Renew DHCP after reboot and connect to OpenWrt at `192.168.1.1`. If needed,
   temporarily set the wired computer to `192.168.1.2/24`.
6. Run `ssh root@192.168.1.1`, then set a password with `passwd`.

LuCI is not included and Wi-Fi is disabled by default. Use the sysupgrade
asset—not the factory asset—for all later OpenWrt upgrades.

Source for these images is the release tag: the OpenWrt base commit, complete
patch, build configuration, instructions, third-party notices, and Realtek
Wi-Fi firmware redistribution license are all included in the repository.

## 한국어

이 릴리스는 ipTIME A2004MU 전용 비공식 빌드입니다. 플래시를
쓰기 전에 UART 복구 수단을 준비하고 정품 펌웨어 및 기기별 데이터를
백업하십시오. 이 프로젝트는 OpenWrt, ipTIME 또는 Realtek이 보증하거나
후원하지 않습니다.

### 첨부 파일

- `a2004mu-openwrt-sysupgrade.bin`
  - 크기: 7,864,592바이트
  - SHA-256:
    `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`
  - overlay를 지운 첫 부팅과 이후 일반 재부팅까지 하드웨어 시험 완료
- `a2004mu-openwrt-factory.bin`
  - 크기: 8,126,464바이트
  - SHA-256:
    `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`
  - 정품 웹 설치용 factory wrapper로 오프라인 구조 검사는 통과했지만,
    이 최종 이미지를 정품 펌웨어에서 직접 설치하는 시험은 아직 하지 않음

sysupgrade 전에는 먼저 다음 명령을 실행하십시오.

```sh
sysupgrade -n --test /tmp/a2004mu-openwrt-sysupgrade.bin
```

검사가 통과한 경우에만 `sysupgrade -n`으로 진행하십시오. 설정 보존
업그레이드는 의도적으로 지원하지 않습니다. Wi-Fi는 기본적으로 꺼져
있습니다. 내장 2.4GHz 무선랜은 지원하지 않으며, 별도 RTL8822BE 5GHz
무선랜만 구동을 확인했습니다.

factory wrapper는 A2004MU 정품 웹 업그레이드 형식 전용이며 범용 설치
이미지가 아닙니다. 모든 정품 버전과 하드웨어 리비전의 호환성을 보장하지
않습니다. 시리얼 복구 수단과 검증된 정품 복구 경로가 없다면 사용하지
마십시오.

### 정품 펌웨어에서 처음 설치

1. 기기가 ipTIME A2004MU이며 정품 펌웨어로 동작 중인지 확인합니다.
2. 위의 `factory.bin` 파일을 내려받고 SHA-256을 확인합니다.
3. 유선 LAN으로 연결한 뒤 정품 펌웨어의 수동 펌웨어 업그레이드 메뉴를
   엽니다.
4. factory 이미지를 선택해 업그레이드를 시작하고 전원을 끊지 마십시오.
   검증과 기록 중에는 화면이나 UART 출력이 없을 수 있으므로 공유기가
   스스로 재부팅할 때까지 기다립니다.
5. 재부팅 후 DHCP를 갱신하고 `192.168.1.1`에 접속합니다. 필요하면 PC의
   유선 주소를 `192.168.1.2/24`로 임시 설정합니다.
6. `ssh root@192.168.1.1`로 접속하고 `passwd`로 비밀번호를 설정합니다.

LuCI는 포함되어 있지 않고 Wi-Fi는 기본적으로 꺼져 있습니다. 이후
OpenWrt 업데이트에는 factory 파일이 아니라 sysupgrade 파일을 사용해야
합니다.

이 이미지의 대응 소스는 릴리스 태그에 있습니다. OpenWrt 기준 커밋, 전체
패치, 빌드 설정과 절차, 제3자 고지 및 Realtek Wi-Fi 펌웨어 재배포
라이선스를 저장소에서 함께 제공합니다.
