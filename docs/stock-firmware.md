# Stock Firmware Analysis / 정펌 펌웨어 분석

## Firmware / 펌웨어

- Model string / 모델 문자열: `a2004m`
- Firmware check offset / 펌웨어 검사 오프셋: `0x40000`
- Root filesystem / 루트 파일시스템: SquashFS
- Flash size / 플래시 크기: 8MB

## Notes / 메모

The stock bootloader checks firmware from offset `0x40000`.

정펌 부트로더는 `0x40000` 오프셋부터 펌웨어를 검사합니다.

The bootlog shows the kernel command line:

부트로그에서 확인된 커널 커맨드라인:

```text
console=ttyS0,38400 root=/dev/mtdblock1

The currently observed MTD layout is not final and needs further verification.

현재 관측된 MTD 레이아웃은 확정이 아니며 추가 검증이 필요합니다.

Do Not Flash Yet / 아직 플래시 금지

Do not flash any custom image until the firmware header, checksum, and recovery method are understood.

펌웨어 헤더, 체크섬, 복구 방법이 확인되기 전까지 커스텀 이미지를 플래시에 쓰지 마세요.
