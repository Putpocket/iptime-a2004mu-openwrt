# ipTIME A2004MU OpenWrt Porting Research

ipTIME A2004MU / Realtek RTL8197F router OpenWrt porting research notes.

ipTIME A2004MU / Realtek RTL8197F 공유기의 OpenWrt 포팅 연구 기록입니다.

## Device / 장치 정보

* Model / 모델: ipTIME A2004MU / a2004m
* SoC / SoC: Realtek RTL8197F
* CPU Clock / CPU 클럭: 999MHz
* RAM / 메모리: 64MB DDR2
* Flash / 플래시: 8MB SPI NOR, xmc25qh64
* Serial / 시리얼: 38400 8N1
* Bootloader / 부트로더: Realtek boot code
* Bootloader prompt / 부트로더 프롬프트: `<RealTek>`

## Current Status / 현재 상태

| Item                          | Status |
| ----------------------------- | ------ |
| UART TX / UART 출력             | OK     |
| UART RX / UART 입력             | OK     |
| Bootloader access / 부트로더 진입   | OK     |
| Stock bootlog / 정펌 부트로그       | OK     |
| Firmware analysis / 펌웨어 분석    | WIP    |
| Ethernet / 유선 LAN             | TODO   |
| SSH / SSH                     | TODO   |
| Wi-Fi / 무선랜                   | TODO   |
| Installable image / 설치 가능 이미지 | TODO   |

## UART Pinout / UART 핀맵

J1 header, counted from top to bottom.

J1 헤더를 랜포트 9시 방향 기준 위에서 아래 방향으로 1~4번으로 세었습니다.

| Pin  | Function                                      |
| ---- | --------------------------------------------- |
| J1-1 | VCC candidate, do not connect / VCC 후보, 연결 금지 |
| J1-2 | Router TX / 공유기 TX                            |
| J1-3 | Router RX / 공유기 RX                            |
| J1-4 | GND / 그라운드                                    |

## UART Connection / UART 연결

```text
CP2102 GND  -> J1-4
CP2102 RXD  -> J1-2
CP2102 TXD  -> J1-3
CP2102 VCC  -> Do not connect
CP2102 3.3V -> Do not connect
CP2102 5V   -> Do not connect
```

```text
CP2102 GND  -> J1-4
CP2102 RXD  -> J1-2
CP2102 TXD  -> J1-3
CP2102 VCC  -> 연결 금지
CP2102 3.3V -> 연결 금지
CP2102 5V   -> 연결 금지
```

## Bootloader Access / 부트로더 진입

Press `ESC` during early boot to interrupt booting.

부팅 초기에 `ESC`를 누르면 부트로더 진입이 가능합니다.

Observed prompt:

확인된 프롬프트:

```text
<RealTek>
```

## Goal / 목표

The first goal is a minimal wired-only OpenWrt image.

1차 목표는 유선 LAN과 SSH만 가능한 최소 OpenWrt 이미지입니다.

Initial target:

초기 목표:

* Ethernet LAN / 유선 LAN
* SSH access / SSH 접속
* No LuCI at first / 초기에는 LuCI 제외
* No Wi-Fi at first / 초기에는 무선랜 제외

## Warning / 주의

This project is experimental. Do not flash any image unless you have a recovery plan.

이 프로젝트는 실험 단계입니다. 복구 방법이 확보되지 않은 상태에서 이미지를 플래시에 쓰지 마세요.

Do not run dangerous bootloader commands unless you know exactly what they do.

정확히 이해하지 못한 상태에서 위험한 부트로더 명령을 실행하지 마세요.
