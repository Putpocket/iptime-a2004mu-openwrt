\# Status / 진행 상태



\## Confirmed / 확인된 내용



\* UART console works at 38400 8N1.



\* UART 콘솔은 38400 8N1에서 동작합니다.



\* Bootloader prompt is accessible with `ESC`.



\* `ESC` 키로 부트로더 프롬프트에 진입할 수 있습니다.



\* Bootloader prompt: `<RealTek>`



\* 부트로더 프롬프트: `<RealTek>`



\* SoC: Realtek RTL8197F



\* SoC: Realtek RTL8197F



\* CPU Clock: 999MHz



\* CPU 클럭: 999MHz



\* RAM: 64MB DDR2



\* 메모리: 64MB DDR2



\* Flash: 8MB SPI NOR xmc25qh64



\* 플래시: 8MB SPI NOR xmc25qh64



\* Stock kernel: Linux 3.10.90 Realtek MSDK



\* 정펌 커널: Linux 3.10.90 Realtek MSDK



\## UART Pinout / UART 핀맵



| Pin  | Function                                      |

| ---- | --------------------------------------------- |

| J1-1 | VCC candidate, do not connect / VCC 후보, 연결 금지 |

| J1-2 | Router TX / 공유기 TX                            |

| J1-3 | Router RX / 공유기 RX                            |

| J1-4 | GND / 그라운드                                    |



\## Bootloader Commands / 부트로더 명령어



Observed command help:



확인된 명령어 도움말:



```text

HELP (?)                                    : Print this help message

AUTOBURN: 0/1

LOADADDR: <Load Address>

J: Jump to <TargetAddress>

FLI: Flash init

FLR: FLR <dst><src><length>

FLW <dst\_ROM\_offset><src\_RAM\_addr><length\_Byte> <SPI cnt#>: Write to SPI

XMOD <addr>  \[jump]

TI : timer init

T : test

ETH : startup Ethernet

CPUClk:

CP0

ERASECHIP

ERASESECTOR

SPICLB (<flash ID>) : SPI Flash Calibration

D8 <Address>

E8 <Address> <Value>

```



\## Dangerous Commands / 위험한 명령어



Do not use these commands yet.



아직 아래 명령어는 사용하지 마세요.



```text

FLW

ERASECHIP

ERASESECTOR

SPICLB

AUTOBURN

E8

```



These commands may write to flash, erase flash, or modify memory.



위 명령어들은 플래시에 쓰기, 플래시 삭제, 메모리 수정과 관련될 수 있습니다.



\## Stock Firmware Notes / 정펌 펌웨어 메모



Observed from stock bootlog:



정펌 부트로그에서 확인된 내용:



```text

Kernel command line: console=ttyS0,38400 root=/dev/mtdblock1

Check Firmware(00040000)

```



Known flash-related observations:



플래시 관련 확인 내용:



```text

Flash: xmc25qh64

Flash size: 8MB

Rootfs: squashfs

```



Estimated layout is not final.



아직 플래시 레이아웃은 확정된 것이 아닙니다.



Do not flash any custom image until the firmware layout and recovery method are understood.



펌웨어 레이아웃과 복구 방법이 확정되기 전까지 커스텀 이미지를 플래시에 쓰지 마세요.



\## Next Steps / 다음 단계



1\. Redact stock bootlog.



2\. 정펌 부트로그에서 MAC 주소 등 민감 정보를 제거합니다.



3\. Analyze official firmware image format.



4\. 공식 펌웨어 이미지 포맷을 분석합니다.



5\. Identify firmware header, kernel, and rootfs offsets.



6\. 펌웨어 헤더, 커널, rootfs 위치를 확인합니다.



7\. Research RTL8197F OpenWrt or Realtek SDK-based build options.



8\. RTL8197F OpenWrt 또는 Realtek SDK 기반 빌드 가능성을 조사합니다.



9\. Try minimal wired-only initramfs image first.



10\. 먼저 유선 LAN 전용 최소 initramfs 이미지를 목표로 합니다.



