# Firmware Header Notes

Detailed stock header observations now live in:

```text
docs/image-format-notes.md
```

This file is kept as a compatibility note for older local research references.
Do not treat the header layout or checksum behavior as a final public format
specification.

Current safe tooling:

```sh
python3 tools/inspect_stock_firmware.py /path/to/local/stock-firmware.bin
```

The stock firmware file must remain outside git. Local artifacts are expected
under:

```text
../iptime-a2004mu-local-artifacts/
```

Status:

* Header fields are observed from local stock firmware version 15.352.
* Rootfs offset varies between observations and must not be hardcoded.
* Checksum behavior is research evidence only until validated across more
  images.
* No generated image is flash-verified.
