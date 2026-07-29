# v0.1.0 experimental / v0.1.0 실험판

## English

This is an unofficial experimental build for the ipTIME A2004MU only. Keep
UART recovery available. Back up the stock firmware and device-specific data
before writing flash. This project is not affiliated with or endorsed by
OpenWrt, ipTIME, or Realtek.

### Assets

- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-sysupgrade.bin`
  - size: 7,864,592 bytes
  - SHA-256:
    `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`
  - hardware-tested with erased-overlay first boot and a subsequent normal
    reboot
- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-factory_15_365.bin`
  - size: 8,126,464 bytes
  - SHA-256:
    `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`
  - wrapper for stock firmware 15.365; passed offline structural checks but
    this exact final image has not been installed from stock firmware

For sysupgrade, first run:

```sh
sysupgrade -n --test /tmp/openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-sysupgrade.bin
```

Proceed only if the test passes, and use `sysupgrade -n`. Preserving settings
is intentionally unsupported. Wi-Fi is disabled by default. The integrated
2.4 GHz radio is unsupported; only the separate RTL8822BE 5 GHz radio has been
brought up.

The factory wrapper is specific to the A2004MU stock 15.365 format. It is not a
universal installer. Do not use it without serial recovery and a verified stock
recovery path.

Source for these images is the release tag: the OpenWrt base commit, complete
patch, build configuration, instructions, third-party notices, and Realtek
Wi-Fi firmware redistribution license are all included in the repository.

## 한국어

이 릴리스는 ipTIME A2004MU 전용 비공식 실험 빌드입니다. 플래시를 쓰기
전에 UART 복구 수단을 준비하고 정품 펌웨어 및 기기별 데이터를
백업하십시오. 이 프로젝트는 OpenWrt, ipTIME 또는 Realtek이 보증하거나
후원하지 않습니다.

### 첨부 파일

- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-sysupgrade.bin`
  - 크기: 7,864,592바이트
  - SHA-256:
    `f13cf20f0f8f89b898a610f12adc305f10dde89709f623a6805b01849f11b8f4`
  - overlay를 지운 첫 부팅과 이후 일반 재부팅까지 하드웨어 시험 완료
- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-factory_15_365.bin`
  - 크기: 8,126,464바이트
  - SHA-256:
    `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`
  - 정품 펌웨어 15.365용 wrapper로 오프라인 구조 검사는 통과했지만,
    이 최종 이미지를 정품 펌웨어에서 직접 설치하는 시험은 아직 하지 않음

sysupgrade 전에는 먼저 다음 명령을 실행하십시오.

```sh
sysupgrade -n --test /tmp/openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-sysupgrade.bin
```

검사가 통과한 경우에만 `sysupgrade -n`으로 진행하십시오. 설정 보존
업그레이드는 의도적으로 지원하지 않습니다. Wi-Fi는 기본적으로 꺼져
있습니다. 내장 2.4GHz 무선랜은 지원하지 않으며, 별도 RTL8822BE 5GHz
무선랜만 구동을 확인했습니다.

factory wrapper는 A2004MU 정품 15.365 형식 전용이며 범용 설치 이미지가
아닙니다. 시리얼 복구 수단과 검증된 정품 복구 경로가 없다면 사용하지
마십시오.

이 이미지의 대응 소스는 릴리스 태그에 있습니다. OpenWrt 기준 커밋, 전체
패치, 빌드 설정과 절차, 제3자 고지 및 Realtek Wi-Fi 펌웨어 재배포
라이선스를 저장소에서 함께 제공합니다.
