#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

status=0

mapfile -d '' candidates < <(
  git ls-files --cached --others --exclude-standard -z
)

echo "Checking for forbidden firmware/binary artifacts..."

for path in "${candidates[@]}"; do
  case "$path" in
    *.bin|*.img|*.fw|*.trx|*.ko|*.so|*.squashfs)
      echo "forbidden file: $path"
      status=1
      ;;
  esac
done

echo "Checking for rootfs/squashfs extraction directories..."

for path in "${candidates[@]}"; do
  case "$path" in
    extracted-rootfs/*|rootfs-*/*|*/rootfs-*/*|squashfs-root/*|*/squashfs-root/*)
      echo "forbidden extraction path: $path"
      status=1
      ;;
  esac
done

echo "Checking for files larger than 10MB..."

for path in "${candidates[@]}"; do
  if [ -f "$path" ] && [ "$(stat -c %s "$path")" -gt 10485760 ]; then
    echo "large file over 10MB: $path"
    status=1
  fi
done

if [ "$status" -ne 0 ]; then
  echo "Repository safety check failed."
  exit "$status"
fi

echo "Repository safety check passed."
