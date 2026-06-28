# Repository Safety

This repository should contain only GitHub-safe research material:

* documentation
* scripts written from scratch
* metadata and checksums
* patch instructions
* build workflow notes

Do not commit stock firmware, Realtek SDK outputs, extracted root filesystems,
kernel modules, shared libraries, or other license-unclear vendor binaries.

## Safety Check

Run:

```sh
bash scripts/check_repo_safety.sh
```

The script fails if it finds:

* `*.bin`
* `*.img`
* `*.fw`
* `*.trx`
* `*.ko`
* `*.so`
* rootfs or SquashFS extraction directories
* files larger than 10 MB

## Current Local Failure

The current working tree may fail this check because existing local research
artifacts are present under paths such as:

```text
firmware/*.bin
firmware/rootfs-*/
license-audit/realtek-code-hits.txt
```

Those files are local analysis artifacts and are not GitHub-safe commit
contents. They are intentionally not deleted by the safety script. Move them
outside the repository before publishing or committing.
