#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

status=0

echo "Checking for forbidden firmware/binary artifacts..."

while IFS= read -r path; do
  case "$path" in
    ./.git/*) continue ;;
  esac
  echo "forbidden file: ${path#./}"
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

echo "Checking for rootfs/squashfs extraction directories..."

while IFS= read -r path; do
  case "$path" in
    ./.git/*) continue ;;
  esac
  echo "forbidden directory: ${path#./}"
  status=1
done < <(
  find . -path './.git' -prune -o -type d \( \
    -name 'extracted-rootfs' -o \
    -name 'rootfs-*' -o \
    -name 'squashfs-root' \
  \) -print
)

echo "Checking for files larger than 10MB..."

while IFS= read -r path; do
  case "$path" in
    ./.git/*) continue ;;
  esac
  echo "large file over 10MB: ${path#./}"
  status=1
done < <(find . -path './.git' -prune -o -type f -size +10M -print)

if [ "$status" -ne 0 ]; then
  echo "Repository safety check failed."
  exit "$status"
fi

echo "Repository safety check passed."
