#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$repo_root"

status=0

mapfile -d '' candidates < <(
  git ls-files --cached --others --exclude-standard -z
)

echo "Checking provenance boundaries..."

for path in "${candidates[@]}"; do
  case "$path" in
    firmware/*|extracted-rootfs/*|squashfs-root/*|license-audit/*|\
    rtk_openwrt_sdk/*|openwrt_rtk/*|realtek-sdk/*|sdk/*|rootfs/*|out/*)
      echo "forbidden or local-only path: $path"
      status=1
      ;;
    */rootfs-*/*|rootfs-*/*|*squashfs*/*)
      echo "forbidden extraction path: $path"
      status=1
      ;;
    *.bin|*.img|*.fw|*.trx|*.ko|*.so|*.squashfs)
      echo "forbidden generated/vendor artifact: $path"
      status=1
      ;;
  esac
done

if [ "$status" -ne 0 ]; then
  echo "Provenance boundary check failed."
  echo "This script is a defensive repository check, not a legal review."
  exit "$status"
fi

echo "Provenance boundary check passed."
echo "This script is a defensive repository check, not a legal review."
