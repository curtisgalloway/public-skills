<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# M02a named unit: source export and transfer verification

## Terms

- **Export** — an archive derived from the pinned source with explicit removals.
- **Transfer verification** — comparing every extracted file/link to the retained inventory.
- **Semantic review** — reading content to decide whether it supplies forbidden device facts.

See the [glossary](../../../GLOSSARY.md) and
[export procedure](../evals/enc28j60/reconstruction/M02a-EXPORT.md).

## Scope

Started from clean `main` at `d392553`, after verifying PR 71 merged and its CI passed.
Work branch: `driver-porting/m02a-export`. This session-sized unit implements source-export
machinery and transfer checks. It does not complete M02a: fixture configuration, semantic
audit, API packaging, minimal scaffolding and offline placeholder compilation remain pending.
No candidate was implemented, no experiment was launched and no hardware was accessed.

The prior case-collision defect motivates a direct archive-to-archive transform and complete
post-transfer identity checks. No host-extracted kernel tree or reference build output is used.
The exporter checks both the retained compressed SHA-256 and the complete upstream Git tree.
It creates a new destination exclusively, preserves failed attempts, and labels every successful
manifest as preparation-only. It cannot prove semantic isolation or validate a forged inventory.

## Observed export

Input commit and tree remain `adc218676eef25575469234709c2d87185ca223a` and
`ac4266ccaf1cf79e8fb22ad3e0d86deac358ffb9`. The upstream archive digest remains
`8787cc90ca7740ab7c955b6fad83010dc600f14a6d94511b548703e4f0f40caa`.
Export attempt 01 exited successfully with these identities:

| Item | Observed value |
| --- | --- |
| Exported Git tree | `e13f8920ab915d52ef2ce3722cc584e540ee52f5` |
| `source.tar` SHA-256 | `cbf40c85a2a06b364d79a7bffdc228414f6c7ba467f3d1b3f3689dd695afa6fc` |
| Archive bytes | 1,542,338,560 |
| Regular files | 86,613 (1,017 executable) |
| Symbolic links | 62 |
| Declared changes | Five files removed, three edited |
| Remaining manufacturer-name paths | 1,015, pending semantic disposition |

The full case-insensitive scan of the original archive found six paths containing `enc28j60`.
The exporter also checks `en28j60` (the upstream Kconfig spelling) and `framethrower`.
No remaining match passed the export gate. Removed: driver, register header, device-tree
binding, top-level `MAINTAINERS` and `.mailmap`. Edited: Microchip Kconfig and Makefile plus
`arch/arm/configs/mxs_defconfig`. Every other file/link retains its byte and executable identity.
The manifest records the entire file inventory and each changed path's input/output digests.
It remains evaluator-only because it names removed reference paths and records audit work.

This first export intentionally preserves unrelated kernel sources. Manufacturer-name matches
are not a whitelist or a completed content audit. Other spellings, unnamed target information,
general driver examples, generated files and later API exports require separate review.
The artifact is not approved for an implementer or evidence that B02/B03/B04 are closed.

## Verification and review

Host tests ran 15 cases with one case-sensitive transfer test skipped on the Mac filesystem.
The positive archive test separately constructs a filesystem fixture whose case-distinct
entries collide on the Mac, and confirms verifier rejection; this is not a tar extraction test.
A disconnected Linux guest is used for the complete
positive transfer and independent corruption controls. The full archive digest and extracted
inventory/tree matched in the first guest: 86,675 entries, tree
`e13f8920ab915d52ef2ce3722cc584e540ee52f5`.

The first guest test run found one test-expectation defect: deleting `Foo.h` also made the
fixture's link dangling, so the verifier correctly rejected it earlier than the test expected.
The missing-file test now deletes the other case-distinct file to isolate inventory comparison.
The failed log is retained. A fresh disconnected guest then passed all 15 tests with no skips.
Both guests used the retained toolchain image with `--network none`; only export/check inputs
were mounted read-only. This is evaluator-side transfer testing, not harness qualification.

Tests cover archive hash/tree mismatch, duplicate and traversal paths, hard links, escaping
and chained symlinks, removed-source aliases, missing removals, changed registration anchors,
unexpected device references, preserved existing destinations, and file/mode/content loss.
The transfer mutations restore and verify the valid fixture between failures, so earlier
damage cannot make a later negative case pass spuriously.

The affected corpus suite initially passed 103 tests (one Mac case-sensitive skip), including
all 15 initial exporter tests. Registration, private-path and explicit changed-file privacy
checks, local Markdown links, author-manifest consistency and the frozen ledger check passed.
The protected M01 preparation records and frozen ledger files remain unchanged. Pyink and
pylint passed after the review fixes. Final test counts are recorded below. Agent-review cost
and operator active time are unmeasured.

## Next boundary

Finish semantic dispositions and the outside-spec fact inventory before approving source inputs.
Then export complete audited API documents and neutral scaffolding, freeze the fixture-specific
configuration, and build the placeholder from fresh outputs offline. M02b retains every M01
harness-isolation test. Models, caps and experimental reviewers remain unselected.

## Independent implementation review

Review scope: the five working-tree files against `d392553`, including new files. The four
reviewers ran in two waves because only three worker slots were available; each received only
its own mandate. All four completed, the mechanical quote check passed all three submitted
findings, and a separate referee merged the duplicate enumeration finding. Locations in the
table refer to the retained initial review snapshot, before fixes. No findings were dropped.

## Review swarm: 2 finding(s)

All 4 arms delivered.

| # | ID | Severity | Arms | Location | Claim | Suggested fix |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | F2 | medium | security, correctness | `plugins/driver-porting/evals/enc28j60/export_kernel.py:260` | os.walk silently ignores directory enumeration errors because no onerror callback is supplied. If all expected files are intact but an extra directory containing unexpected files is unreadable (for example, because of inherited permissions), lines 272-273 skip its directory entry (`elif stat.S_ISDIR(info.st_mode):` followed by `continue`), the walk silently skips its contents, and verification returns match=True despite those additional files; no concurrent writer or attacker is required. | Supply an onerror callback that re-raises directory enumeration failures so an incomplete walk cannot pass verification. Add a regression test that injects an… |
| 2 | F3 | low | docs | `plugins/driver-porting/evidence/M02a-export.md:64-65` | The evidence describes an extraction check, but the positive test constructs a filesystem fixture directly instead of extracting the exported archive. In plugins/driver-porting/evals/enc28j60/tests/test_export_kernel.py:112 it calls `root = self.extract_fixture()`, whose implementation explicitly says `"""Write a controlled fixture, independent of tar extraction semantics."""` at line 78 and writes `item.write_bytes(data)` at line 91; this confirms rejection of simulated case loss, not Mac tar-extraction behavior. | Describe the test as constructing a case-colliding filesystem fixture and confirming verifier rejection. Reserve claims about actual archive extraction for a s… |

Dropped before this table: checker dropped 0; referee dropped 0; merged 1.

### Resolutions

- **F2 (medium, security/correctness): fixed.** Directory enumeration errors now propagate;
  incomplete traversal cannot yield a passing inventory. Added an injected enumeration-error
  test and a real unreadable-directory test, preserving a valid inventory as the positive
  control. The latter must run as a non-root user.
- **F3 (low, docs): fixed.** The evidence now describes a directly constructed case-colliding
  filesystem fixture. Actual archive extraction is claimed only for the logged Linux guest.

No surviving finding is deferred. The review covers export/verification machinery, not the
semantic admissibility of the complete kernel tree or the unimplemented M02b boundaries.
The referee's bounded follow-up confirmed both F2 and F3 addressed, with no remaining concern
within either finding; it did not rerun tests or repeat the entire review.

## Final checks and custody

After the fixes, the full affected corpus suite passed 105 tests with one Mac case-sensitive
skip. A fresh disconnected guest running as an unprivileged user passed all 17 exporter tests,
with no skips, including real directory-permission denial. The final verifier also matched
the archive digest and all 86,675 extracted entries against the retained manifest. This is
the final code's positive whole-tree transfer check; it does not compile the kernel.

Private preparation record: `enc28j60-m02a-export-20260920`. Retain the archive, full manifest,
initial and final tool copies, failed and successful guest logs, corpus-test logs, exact review
snapshot, all four reviewer results, mechanical check, referee decision and fix verification.
The retained inventory records artifact hashes. No off-host backup is established. The new
evaluator guests exit after their checks and remain retained; prior reference guests are
unchanged. Nothing here qualifies an implementer harness or permits a hardware launch.
