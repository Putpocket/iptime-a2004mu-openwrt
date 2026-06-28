# Clean-room Policy

This repository targets clean-room OpenWrt support for ipTIME A2004MU.

## SDK Role

The Realtek SDK is reference-only. It may be used to understand observed device
behavior, boot logs, memory layout, image layout, and hardware structure. It
must not be copied into OpenWrt target, driver, DTS, package, or board support
code.

## Allowed Evidence

* UART logs
* Stock boot facts
* Hardware observations
* Public datasheets, if available
* Public Linux and OpenWrt APIs
* Independently written code
* Independently written notes, scripts, metadata, and patch plans

## Disallowed Material

* Copying SDK driver files
* Importing SDK binary blobs
* Committing extracted rootfs contents
* Committing firmware images
* Committing generated candidate firmware
* Committing `.ko`, `.so`, or other vendor binaries
* Treating SDK `AP-fw` as mainline OpenWrt

## Documentation Rule

When a fact comes from an observed log or local image inspection, document it as
evidence. When code is implemented, keep it independently written and grounded
in public Linux/OpenWrt interfaces or directly observed hardware behavior.
