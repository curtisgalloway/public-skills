<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# M02a source-export preparation

## Terms

- **Export** — a new archive derived from the pinned upstream source, with declared removals.
- **Inventory** — a list of every supplied file or symbolic link, its mode, size and digest.
- **Tree identity** — Git's recursive digest of paths, executable modes and file/link bytes.

See the [glossary](../../../../../GLOSSARY.md).

## Boundary

`export_kernel.py` is an evaluator-side preparation tool, not an isolation mechanism or an
approved implementation packet. Python 3.10 or later with its standard library is sufficient.
It reads only the exact compressed archive retained in M02a, also checks the complete upstream
Git tree, and writes a new uncompressed tar without extracting the original onto the host.
The observed compressed digest is deliberately strict: a regenerated upstream download with
different compressed bytes requires separate verification and a reviewed pin change.

The current export removes the target driver, register header and device-tree binding;
removes the original Kconfig options, Makefile registration and one board-config selection;
and removes top-level `MAINTAINERS` and `.mailmap` metadata. Other upstream sources remain.
No fixture facts, candidate spec, API packet, build configuration or replacement driver is added.
The eight path changes are individually recorded with before/after digests. This record itself
is evaluator-only and must not be supplied to an implementer.

Case-insensitive scans reject remaining `enc28j60`, the upstream spelling `en28j60`, and
`framethrower` in file contents, paths or symlink targets. All `microchip` matches are inventoried
by path for later semantic review; they are **not automatically approved**. Neither a zero
device-name count nor exact tree identity proves freedom from unnamed device information.
Audit these remaining sources and future generated files before calling the packet sanitized.

## Commands

From the repository root, substitute retained archive and new output locations:

```sh
python3 plugins/driver-porting/evals/enc28j60/export_kernel.py export \
  <upstream-archive.tar.gz> <new-export-directory>
```

The output directory must not already exist. `source.tar` contains a `source/` tree;
`manifest.json` is written after export validation. A failed attempt may leave a partial tar
or manifest; retain it as failed and use a new directory. Do not treat file existence as a pass:
require a successful command, parseable manifest and matching archive digest. The manifest
always labels this stage `preparation-only-not-approved-for-implementation`.

Transfer `source.tar` as an archive to a fresh Linux filesystem, along with the retained
manifest and a separately pinned copy of the verifier. Check the archive SHA-256 against the
evaluator's retained value **before extraction**. Extract only into an empty destination on
case-sensitive storage. Then run in that guest:

```sh
python3 export_kernel.py verify <extracted-source-directory> <retained-manifest.json>
```

This compares every regular file and symlink, including unexpected additions, missing paths,
executable-mode changes, content changes and altered link targets. Empty directories and
ownership/timestamps are not part of Git tree identity or this inventory. Verify immutable,
quiescent inputs: the tool does not defend against concurrent writers or a forged manifest.
Keep the trusted manifest outside any future implementer's writable paths. Never use a
host-extracted tree from the invalid M02a attempt as the input to this procedure.

The archive writer normalizes ownership/timestamps and regular-file permissions, preserving
executable status and link targets. It rejects ambiguous or duplicate paths, special files,
hard links, escaping/dangling links, and links traversing another link. The pinned tree's
ordinary file links and directory links remain present. No network operation is performed.

## Remaining gates

This named unit supplies export machinery and transfer evidence. M02a still requires semantic
source review, fixture-specific configuration and outside-spec fact dispositions, complete
API documentation including transitive kernel-doc content, minimal neutral scaffolding,
and a fresh offline placeholder build. Reference outputs must never supply that build.
M02b separately qualifies harness filesystem, provider transport, tool-network and state/log
boundaries. All M01 tests and blockers remain binding; this tool closes none by itself.
