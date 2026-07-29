# Reference and provenance policy

The historical filename is retained for links, but this project does not claim
a formal two-team clean-room implementation.

## Reference sources

Implementation may be informed by:

- UART and network captures;
- read-only register observations on owned hardware;
- stock firmware behavior and independently produced disassembly notes;
- public Linux and OpenWrt source;
- public datasheets;
- Realtek SDK files that expressly grant redistribution/modification rights,
  with their role and file-level license documented.

## Rules

- Do not copy or publish the Realtek SDK tree.
- Do not copy code from SDK files marked proprietary, confidential, or
  `All Rights Reserved` without an explicit redistribution grant.
- Preserve copyright and license notices when code is derived from a licensed
  source.
- Prefer Linux/OpenWrt interfaces and independently structured drivers over
  vendor APIs.
- Record when a register value, descriptor layout, or sequence came from SDK
  inspection, stock observation, or public upstream source.
- Do not claim independence that the development history cannot demonstrate.

## Material excluded from Git

- stock and generated firmware images;
- SDK binaries and source trees;
- extracted root filesystems;
- device-unique MAC addresses, calibration bytes, keys, and credentials;
- `.ko`, `.so`, and other vendor binaries;
- private UART logs and AI handoff records.

`scripts/check_provenance_boundaries.sh` enforces only basic repository
boundaries. It cannot determine copyrightability, derivation, or license
compatibility.
