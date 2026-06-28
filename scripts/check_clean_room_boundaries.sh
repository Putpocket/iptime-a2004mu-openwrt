#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

status=0

echo "Checking clean-room boundaries..."

for dir in \
  firmware \
  extracted-rootfs \
  squashfs-root \
  license-audit \
  rtk_openwrt_sdk \
  openwrt_rtk \
  realtek-sdk \
  sdk \
  rootfs; do
  if [ -e "$dir" ]; then
    echo "forbidden or local-only path present: $dir"
    status=1
  fi
done

if [ -d out ] && find out -type f | grep -q .; then
  echo "forbidden generated output files under: out"
  status=1
fi

while IFS= read -r path; do
  echo "forbidden generated/vendor artifact: ${path#./}"
  status=1
done < <(
  find . -path './.git' -prune -o -type f \( \
    -name '*.bin' -o \
    -name '*.img' -o \
    -name '*.fw' -o \
    -name '*.trx' -o \
    -name '*.ko' -o \
    -name '*.so' -o \
    -name '*.squashfs' \
  \) -print
)

while IFS= read -r path; do
  echo "forbidden extraction directory: ${path#./}"
  status=1
done < <(
  find . -path './.git' -prune -o -type d \( \
    -name 'rootfs-*' -o \
    -name '*squashfs*' \
  \) -print
)

if [ "$status" -ne 0 ]; then
  echo "Clean-room boundary check failed."
  echo "This script is a defensive repository check, not a legal review."
  exit "$status"
fi

echo "Clean-room boundary check passed."
echo "This script is a defensive repository check, not a legal review."
