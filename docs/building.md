# Building

## Exact inputs

- OpenWrt repository: `https://git.openwrt.org/openwrt/openwrt.git`
- base commit: `6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2`
- patch: `patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch`
- diffconfig: `configs/a2004mu.config`
- feed revision record: `configs/feeds.buildinfo`

The selected configuration disables external feed packages, so the feed file
is a provenance record for the tested build rather than a requirement for the
minimal image.

## Commands

```sh
git clone https://git.openwrt.org/openwrt/openwrt.git
cd openwrt
git checkout 6e9fd1c3ba6bf486a044ed9d640a77dd50b6cbc2
git apply --check ../iptime-a2004mu-openwrt/patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch
git apply ../iptime-a2004mu-openwrt/patches/openwrt/0001-iptime-a2004mu-rtl8197f-support.patch
cp ../iptime-a2004mu-openwrt/configs/a2004mu.config .config
make defconfig
make -j"$(nproc)"
```

If the host inherits Windows or WSL path entries that break GNU
`find -execdir`, use a restricted build path:

```sh
env PATH="$PWD/staging_dir/host/bin:$PWD/staging_dir/toolchain-mipsel_24kc_gcc-14.3.0_musl/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" \
  make -j"$(nproc)"
```

Expected outputs are under `bin/targets/rtl819x/rtl8197f/`:

- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-factory_15_365.bin`
- `openwrt-rtl819x-rtl8197f-iptime_a2004mu-squashfs-sysupgrade.bin`

## Validation

Run the generated image checks and preserve `sha256sum` output. On the router:

```sh
sysupgrade -n --test /tmp/IMAGE.bin
```

Do not proceed if the test reports an unexpected MTD layout, image size,
product header, Protect2 header, kernel marker, or SquashFS offset.
Configuration-preserving sysupgrade is rejected by design.
