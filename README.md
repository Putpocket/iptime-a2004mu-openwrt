# ipTIME A2004MU support for OpenWrt

This is an unofficial port of OpenWrt to the ipTIME A2004MU (Realtek
RTL8197F). It is not affiliated with or endorsed by OpenWrt, ipTIME, or
Realtek.

The repository contains one source patch, the exact OpenWrt base revision and
build configuration, research notes, and independently written analysis tools.
It intentionally does not contain firmware images, stock firmware, extracted
filesystems, Realtek SDK source, or device calibration data.

## Verified hardware state

The pre-publication test build has booted on an A2004MU with:

- Linux 6.18.36 and a SquashFS/JFFS2 overlay;
- working DHCP, SSH, sysupgrade, and normal reboot;
- all four LAN ports and the WAN port linked and tested at 1 Gbit/s full
  duplex;
- interrupt-driven RTL8197F Ethernet with repeated bidirectional transfers and
  no observed FCS, symbol, or discard errors;
- a working RTL8822BE 5 GHz radio using board calibration from NVMEM.

Limitations:

- the RTL8197F integrated 2.4 GHz radio is unsupported;
- a separate 5 GHz client throughput test is still required;
- router-local Ethernet throughput is CPU-bound at roughly 195 Mbit/s;
- LAN-to-LAN switch throughput and WAN forwarding throughput require separate
  two-endpoint measurements;
- hardware NAT is not implemented;
- configuration-preserving sysupgrade is rejected; use `sysupgrade -n`;
- the source default keeps Wi-Fi disabled. Never ship an open access point as a
  default configuration.

See [STATUS.md](STATUS.md) for the tested image record and remaining release
gates.

## Build

The patch is based on OpenWrt commit:

```text
6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2
```

Apply `patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch`, copy
`configs/a2004mu.config` to `.config`, run `make defconfig`, then build.
Full commands and output names are in [docs/building.md](docs/building.md).

Do not flash an image merely because it builds. Keep UART recovery available,
run the image self-checks, and run `sysupgrade -n --test` before any
sysupgrade.

Binary release assets, when provided, are separate from Git history. The
hardware-tested sysupgrade image and the offline-only factory-wrapper status
are recorded in [STATUS.md](STATUS.md). Do not treat the factory wrapper as a
universal installer.

The current bilingual release notes, exact filenames, checksums, and recovery
warnings are in
[docs/release-v0.1.0-prerelease.md](docs/release-v0.1.0-prerelease.md).

## Source and licensing

The repository's original material is offered under GPL-2.0-only unless a file
states otherwise. The OpenWrt patch retains the licenses and notices of the
files it modifies or derives from. The firmware build also selects separately
licensed packages and redistributable Realtek Wi-Fi firmware.

The Realtek RTL819x SDK was used as hardware reference material. No original
SDK source file is shipped here: the platform and driver code was written for
current Linux/OpenWrt interfaces using SDK hardware facts and observed device
behavior. The SDK also contains proprietary components, which are not copied
into this repository. This project does not claim a strict two-team clean-room
process. The provenance audit, file-level SDK license findings, and comparison
with public SDK-based projects are in
[docs/provenance-and-licensing.md](docs/provenance-and-licensing.md).

OpenWrt is a registered trademark owned by Software Freedom Conservancy (SFC).
This project is not affiliated with, sponsored by, or endorsed by OpenWrt.

## Repository safety

Before any publication:

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_provenance_boundaries.sh
git diff --check
```

The checks are defensive filters, not legal review. Local binaries and private
handoff records are ignored and must remain outside Git history.

---

# ipTIME A2004MU OpenWrt 지원

이 저장소는 Realtek RTL8197F 기반 ipTIME A2004MU를 위한 비공식 OpenWrt
포트입니다. OpenWrt, ipTIME 또는 Realtek이 보증하거나 후원하는 프로젝트가
아닙니다.

저장소에는 OpenWrt 기준 리비전, 단일 통합 패치, 빌드 설정, 조사 문서와
독립적으로 작성된 분석 도구가 들어 있습니다. 정품 펌웨어, 추출된
파일시스템, Realtek SDK 원본 소스, 기기별 보정 데이터와 빌드된 펌웨어
이미지는 Git 이력에 포함하지 않습니다. 릴리스 바이너리는 제공하는 경우
Git 이력과 분리된 릴리스 첨부 파일로 배포합니다.

## 확인된 하드웨어 상태

현재 하드웨어 시험에서 다음 항목을 확인했습니다.

- Linux 6.18.36과 SquashFS/JFFS2 overlay
- DHCP, SSH, `sysupgrade -n`, 일반 재부팅
- LAN 4포트와 WAN 포트의 1Gbps full-duplex 링크 및 통신
- 인터럽트 기반 RTL8197F Ethernet 송수신
- NVMEM 보정값과 linux-firmware를 사용하는 RTL8822BE 5GHz 무선랜
- overlay를 지우는 sysupgrade 직후 첫 부팅에서 LAN 자동 복구

현재 제한사항은 다음과 같습니다.

- RTL8197F 내장 2.4GHz 무선랜은 지원하지 않습니다.
- 5GHz 실제 클라이언트 처리량 시험이 더 필요합니다.
- 라우터 자체 Ethernet 처리량은 CPU 병목으로 약 195Mbps입니다.
- LAN 스위칭 및 WAN 라우팅 처리량은 독립된 두 단말로 추가 측정해야 합니다.
- 하드웨어 NAT는 구현하지 않았습니다.
- 설정을 보존하는 sysupgrade는 지원하지 않습니다. 반드시
  `sysupgrade -n`을 사용해야 합니다.
- 기본 설정에서는 Wi-Fi가 꺼져 있습니다.

정확한 시험 이미지 해시와 남은 검증 항목은 [STATUS.md](STATUS.md)를
참조하십시오.

## 빌드

기준 OpenWrt 커밋은 다음과 같습니다.

```text
6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2
```

`patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch`를 적용하고
`configs/a2004mu.config`를 `.config`로 복사한 다음 `make defconfig`과
빌드를 실행합니다. 전체 명령은 [docs/building.md](docs/building.md)에
있습니다.

빌드 성공만으로 펌웨어가 안전하다고 판단하면 안 됩니다. UART 복구 수단을
준비하고 이미지 자체 검사를 거친 다음, sysupgrade 전에 반드시 다음 검사를
통과해야 합니다.

```sh
sysupgrade -n --test /tmp/IMAGE.bin
```

릴리스에 sysupgrade 이미지가 첨부된다면 [STATUS.md](STATUS.md)에 기록된
해시와 일치하는지 확인하십시오. 정품 15.365용 factory wrapper는 현재
오프라인 구조 검사만 통과한 미검증 이미지이며 범용 설치 이미지가 아닙니다.
현재 릴리스의 영문·한국어 안내, 정확한 파일명, 체크섬과 복구 주의사항은
[docs/release-v0.1.0-prerelease.md](docs/release-v0.1.0-prerelease.md)에
있습니다.

## 소스와 라이선스

별도 표시가 없는 저장소 원본 자료는 GPL-2.0-only로 제공합니다. OpenWrt
패치가 수정하거나 파생하는 파일에는 각 파일의 기존 라이선스와 고지문이
적용됩니다. 빌드에는 별도 라이선스의 OpenWrt 패키지와 재배포 가능한
Realtek Wi-Fi 펌웨어도 포함됩니다.

Realtek RTL819x SDK는 하드웨어 참고 자료로 사용했습니다. SDK 원본 소스
파일과 독점 RTL8367 switch API는 이 저장소에 포함하지 않습니다. 새
플랫폼 및 드라이버 코드는 현재 Linux/OpenWrt 인터페이스에 맞춰 작성했으며,
참고 출처와 한계는
[docs/provenance-and-licensing.md](docs/provenance-and-licensing.md)에
공개합니다.

바이너리를 재배포할 때는 GPL 구성요소의 대응 소스와
`LICENSES/Realtek-rtlwifi-firmware`를 포함한 제3자 고지를 함께 제공해야
합니다. 이 문서는 법률 자문이 아니며 광범위한 배포 전에는 별도 법률 검토가
권장됩니다.

## 공개 전 검사

```sh
bash scripts/check_repo_safety.sh
bash scripts/check_provenance_boundaries.sh
git diff --check
```

이 검사는 SDK·정품 이미지·추출 파일·생성 바이너리가 Git 이력에 섞이는
실수를 막기 위한 방어적 검사이며 법률 검토를 대신하지 않습니다.
