# ipTIME A2004MU support for OpenWrt

This is an unofficial port of OpenWrt to the ipTIME A2004MU (Realtek
RTL8197F). It is not affiliated with or endorsed by OpenWrt, ipTIME, or
Realtek.

The repository contains one source patch, the exact OpenWrt base revision and
build configuration, research notes, and independently written analysis tools.
It intentionally does not contain firmware images, stock firmware, extracted
filesystems, Realtek SDK source, or device calibration data.

## Download

- **First install from ipTIME stock firmware:**
  [download `a2004mu-openwrt-factory.bin`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-factory.bin)
- **Upgrade an existing OpenWrt installation:**
  [download `a2004mu-openwrt-sysupgrade.bin`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-sysupgrade.bin)
- **Verify downloads:**
  [download `SHA256SUMS`](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/SHA256SUMS)

Read the installation warnings below before flashing. The factory image is for
the stock web upgrader; the sysupgrade image is only for a router already
running OpenWrt.

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

## First install from stock firmware

This path is only for an ipTIME A2004MU running stock firmware. The exact final
factory image passed offline structural checks but has not yet been
reinstalled through the stock web UI. Compatibility with every stock version
and hardware revision is not guaranteed, so keep a serial/recovery path
available.

1. Download
   `a2004mu-openwrt-factory.bin`
   from the prerelease.
2. Verify its SHA-256:
   `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`.
3. Connect the computer to a LAN port by cable and open the current ipTIME
   administration page.
4. Open the manual firmware-upgrade page and select the factory file. Do not
   select the sysupgrade file.
5. Start the upgrade and do not disconnect power. The page may appear
   unchanged and UART may remain quiet while the stock firmware validates and
   writes the image. Wait for the router to reboot; do not assume that silence
   means the process has stopped.
6. After reboot, renew the computer's DHCP lease. OpenWrt uses
   `192.168.1.1`; if DHCP does not return promptly, temporarily use
   `192.168.1.2/24` on the wired adapter and test `ping 192.168.1.1`.
7. Connect with `ssh root@192.168.1.1` and set a root password immediately
   with `passwd`.

The image does not include LuCI. Wi-Fi is disabled by default, so first access
must be through a wired LAN port. For later OpenWrt updates, use the sysupgrade
image with `sysupgrade -n --test` followed by `sysupgrade -n`; do not upload
the factory file from OpenWrt.

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

## 다운로드

- **ipTIME 정품 펌웨어에서 처음 설치:**
  [`a2004mu-openwrt-factory.bin` 다운로드](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-factory.bin)
- **이미 설치된 OpenWrt 업데이트:**
  [`a2004mu-openwrt-sysupgrade.bin` 다운로드](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/a2004mu-openwrt-sysupgrade.bin)
- **다운로드 파일 검증:**
  [`SHA256SUMS` 다운로드](https://github.com/Putpocket/iptime-a2004mu-openwrt/releases/download/v0.1.0/SHA256SUMS)

플래시하기 전에 아래 설치 주의사항을 읽으십시오. factory 이미지는 정품
웹 업그레이드 전용이고, sysupgrade 이미지는 이미 OpenWrt가 설치된
공유기에서만 사용합니다.

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
해시와 일치하는지 확인하십시오. factory wrapper는 현재 오프라인 구조
검사만 통과한 미검증 이미지이며 범용 설치 이미지가 아닙니다.
현재 릴리스의 영문·한국어 안내, 정확한 파일명, 체크섬과 복구 주의사항은
[docs/release-v0.1.0-prerelease.md](docs/release-v0.1.0-prerelease.md)에
있습니다.

## 정품 펌웨어에서 처음 설치

이 방법은 정품 펌웨어를 사용하는 ipTIME A2004MU 전용입니다. 현재 최종
factory 이미지는 오프라인 구조 검사는 통과했지만, 이 정확한 파일을 정품
웹 UI에서 다시 설치하는 최종 시험은 아직 하지 않았습니다. 모든 정품 버전과
하드웨어 리비전의 호환성을 보장하지 않으므로 UART 또는 복구 수단을
준비하십시오.

1. 사전 공개 릴리스에서
   `a2004mu-openwrt-factory.bin`을
   내려받습니다.
2. SHA-256이
   `b6eb5c150ff7bf8c35e9f918ed3ded520aacd321edc1ff13e50b409f0ad5ff55`인지
   확인합니다.
3. PC를 공유기 LAN 포트에 유선으로 연결하고 현재 ipTIME 관리 페이지에
   접속합니다.
4. 수동 펌웨어 업그레이드 메뉴에서 factory 파일을 선택합니다.
   sysupgrade 파일을 선택하면 안 됩니다.
5. 업그레이드를 시작한 뒤 전원을 끊지 마십시오. 정품 펌웨어가 이미지를
   검증하고 기록하는 동안 화면이 그대로이거나 UART 출력이 없을 수
   있습니다. 아무 출력이 없다는 이유로 중단하지 말고 공유기가 스스로
   재부팅할 때까지 기다립니다.
6. 재부팅 후 PC의 DHCP 주소를 갱신합니다. OpenWrt 주소는
   `192.168.1.1`입니다. DHCP가 바로 잡히지 않으면 유선 어댑터에
   `192.168.1.2/24`를 임시로 설정하고 `ping 192.168.1.1`을 확인합니다.
7. `ssh root@192.168.1.1`로 접속하고 `passwd`로 root 비밀번호를 즉시
   설정합니다.

이 이미지에는 LuCI가 포함되지 않습니다. Wi-Fi도 기본적으로 꺼져 있으므로
최초 접속은 반드시 유선 LAN으로 해야 합니다. 이후 OpenWrt 업데이트에는
sysupgrade 이미지를 사용해 `sysupgrade -n --test`를 먼저 실행한 뒤
`sysupgrade -n`으로 설치하십시오. OpenWrt에서 factory 파일을 올리면
안 됩니다.

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
