# Upgrade Path Research Notes

This document is a high-level research plan for understanding the stock
firmware update path. It is not a flashing guide and does not provide a
procedure for writing an image to a device.

## Current Scope

Safe work in this repository is limited to:

* documenting observed metadata
* inspecting local artifacts without modifying them
* comparing header fields and offsets
* keeping vendor binaries and extracted rootfs contents outside git

No generated image is flash-verified.

## Observed Components

Local rootfs analysis found component names related to firmware handling, such
as a web upload CGI, service layer, firmware service plugin, and platform
library. These observations are useful for understanding validation boundaries,
but the binaries themselves must not be committed.

## Research Questions

Future GitHub-safe research should answer:

* Which header fields are required by stock validation?
* Which checksum fields are required, and over which byte ranges?
* How does rootfs offset vary between firmware versions?
* Does stock validation require product/version metadata beyond the observed
  header fields?
* Which observations can be reproduced by scripts written from scratch?

## Non-Goals

This repository should not contain:

* stock firmware images
* extracted rootfs contents
* vendor shared libraries
* generated firmware candidates
* device-write instructions
* claims that an image is safe to flash
