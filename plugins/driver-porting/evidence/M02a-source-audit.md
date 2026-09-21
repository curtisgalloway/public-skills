<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# M02a source audit: related-controller finding

## Terms

- **Semantic audit** — reading content to decide whether it supplies excluded hardware facts.
- **Disposition** — a reasoned decision to remove, retain, or continue investigating content.
- **Scan control** — known matching or nonmatching input used to check a search expression.

See the [glossary](../../../GLOSSARY.md), [export evidence](M02a-export.md), and
[implementation-input contract](../evals/enc28j60/reconstruction/M01-PREPARATION-v1.md).

## Status and scope

**Reviewed audit finding checkpoint; full M02a remains incomplete.** This is evaluator-only evidence, not an implementer
input or approval of the exported tree. Started from clean `driver-porting/m02a-export` at
`e74a4c0`. A fresh fetch left `origin/main` at `d392553`; the branch had no open PR.
The source archive and exporter remain unchanged. No candidate, build, hardware test, or
experimental review was launched. The frozen preparation contract and documentary ledger remain
unchanged.
The evaluator-only boundary is the M01 contract's exclusion of this entire repository from
implementer access, not secrecy or filesystem isolation supplied by this document.

This bounded audit reads the three ENCx24J600 source files and their two registration files,
compares specific hardware content to the pinned ENC28J60 reference, and searches the complete
export for selected aliases and hardware identifiers. It does not complete the remaining
manufacturer-path audit or establish absence of unnamed device information.

## Input and search coverage

Read the archive directly; do not use the invalid earlier host extraction. Its SHA-256 matched
`cbf40c85a2a06b364d79a7bffdc228414f6c7ba467f3d1b3f3689dd695afa6fc` before the scan.
All 86,613 regular files (1,475,616,203 content bytes) and 62 symbolic links were searched,
including paths and link-target bytes. The five selected files' SHA-256 values also matched
the export manifest. This is a byte search, with no result cap, not content approval.

The case-insensitive expressions were:

| Search | Expression | Matching paths |
| --- | --- | --- |
| Target aliases | `enc[^a-z0-9]{0,3}28[^a-z0-9]{0,3}j[^a-z0-9]{0,3}60\|en28j60\|framethrower\|28j60` | 0 |
| Related controllers | `enc[0-9x]{1,3}j600\|encx24j600\|enc424\|enc624` | 5 |
| Selected distinctive registers | `\b(?:ERXRDPTL\|ERXRDPTH\|ETXSTL\|ETXNDL\|EPKTCNT\|PHLCON\|PKTCTRL_PCRCEN\|MAX_TX_RETRYCOUNT)\b` | 0 |
| Selected shared hardware identifiers | `\b(?:MABBIPG\|MIREGADR\|RSV_RXLONGEVDROPEV\|RSV_RXOK\|PHCON1\|MICMD_MIIRD)\b` | 3 |

Table pipes are escaped for Markdown; the retained search script contains ordinary regex
alternation. The five related-controller hits are exactly the five files below. The three
shared-hardware hits are the three C/header files. These finite patterns miss other spellings,
renamed algorithms, numerical-only information, encodings and compressed payloads.

After review, a second complete scan broadened the related-controller expression to
`enc[^a-z0-9]{0,3}[0-9x]{1,3}[^a-z0-9]{0,3}j[^a-z0-9]{0,3}600|enc[^a-z0-9]{0,3}(?:424|624)`.
It again returned exactly the same five paths, with unchanged counts in every category.
The second script also rejects every unexpected archive member type rather than skipping it;
none was encountered. The pinned exporter already rejects input hard links. This resolves
the reviewer's concern about an unsearched hard-link path for this artifact, without claiming
the scratch scanner is a general archive validator. Construction is also explicit in
`export_kernel.py`: it skips directories, rejects unsupported types, and writes only regular
files or symbolic links. Search-result entries without matching individual lines still require
inspection: a path-only or cross-line match can produce an empty line list.

Both original reference files served as positive controls for the target-alias, distinctive-
register and shared-hardware searches. Neither matched the related-controller search, whose
positive controls are the selected related-device files. A neutral placeholder string matched
none. These results are retained in `controls-complete.json`; separator variants have separate
positive and negative controls in `expanded-controls.json`. Controls demonstrate that these
expressions detect these examples, not general recall.
Reference bytes were read from the pinned upstream archive; their hashes matched the existing
corpus pins: driver `9fb940a540749bb10d662792af4e1babb2f0cdc7bd6ceff08811b0fcd245c5f0`
and header `2a90e04f93d2099ad8c67942c3564184594865dee322e050c912cddc5957fa62`.

## Findings and proposed dispositions

All paths in this section are under `drivers/net/ethernet/microchip/` at upstream commit
`adc218676eef25575469234709c2d87185ca223a`. Registration-file line numbers refer to the
exported versions, which already omit the original target registration.

| File | Content read and reason | Proposed disposition |
| --- | --- | --- |
| `encx24j600_hw.h` | Lines 62–71 specify register-command encodings; 397–409 repeat the target header's receive-status bit positions; 418 specifies a different status-vector size. This supplies hardware information, including overlap and potentially misleading differences. | Remove the entire file. |
| `encx24j600-regmap.c` | Lines 345–380 implement a PHY read through address selection, command start, busy polling, command clearing and data retrieval. In particular, both it and the target's `enc28j60_phy_read` at lines 438–457 clear `MICMD` before reading the result. This is hardware access logic, not merely a generic API call. | Remove the entire file. |
| `encx24j600.c` | Lines 250–257 choose `MABBIPG` values `0x15` and `0x12` by duplex, also present in the target at lines 697–713. Lines 359–399 show receive-status processing and buffer reclamation for the related controller. | Remove the entire file. |
| `Kconfig` | Exported lines 19–26 expose the related model names and configuration option. | Remove only the `ENCX24J600` stanza; preserve unrelated registration. |
| `Makefile` | Exported line 6 registers both related-device objects. | Remove only the `CONFIG_ENCX24J600` object line. |

The receive-status overlap is more than a shared name: the related header's positions 16, 18,
and 20–30 agree with the target header at lines 264–276. The four register-command opcodes
also agree with the target's named commands at lines 284–289. These are source observations,
not new hardware measurements or proof that every related-device procedure applies to the target.
For example, the related header uses an eight-byte receive-status vector while the target uses
six bytes; its SRAM layout also differs. Neither file is an authoritative substitute for a spec.
The related driver's reclamation at lines 391–393 subtracts two and wraps to `SRAM_SIZE - 2`;
the target's `erxrdpt_workaround` at lines 562–573 subtracts one and clamps to the buffer end.
That concrete difference could complicate attribution if an implementer followed the example;
no such candidate behavior has been observed.

Additional overlap confirmed during consultation: `encx24j600_hw.h:362` defines `TSV_SIZE 7`,
matching the target header at line 258; lines 249–250 give the two bytes of the target driver's
`0x0C12` interpacket gap at line 711. The receive-status accessor macros at lines 419–420 match
the target at lines 279–280. The errata comment at line 428 matches the target's line 300,
despite the related header's nonzero receive-buffer start. These textual correspondences do
not establish historical derivation; source provenance was not investigated. They also show
why the selected search tokens cannot serve as an exhaustive inventory of overlapping facts.

The proposed exclusion is a discretionary evaluator tightening of input preparation:
these files offer a concentrated hardware example with demonstrated target overlap and are not
needed as general OS API documentation. The frozen contract does not explicitly exclude every
related-device driver; this is not a finding that retaining these files already violated it.
Allowing overlapping examples could complicate later source-overlap and failure attribution,
but no candidate effect or scanner discrimination was measured here.
This decision does not classify every same-manufacturer driver
as an alternate target implementation. Generic networking APIs and unrelated drivers need
their own content/dependency dispositions; a manufacturer-name match alone is insufficient.

Identities of the reviewed exported bytes:

| File | SHA-256 |
| --- | --- |
| `encx24j600_hw.h` | `0227b4ca92d0836723e2fd3c6056f5a26e085f3617cab805a13e4bfe6464b905` |
| `encx24j600-regmap.c` | `7ea7e3bdde4418e2d888201962bb5a5e00581c0ae2b4a88969b047685bc9686c` |
| `encx24j600.c` | `8281f1b23ec7f512c2f1860f99a3683e10367ab59d62cddd99bfab4d41828a2b` |
| `Kconfig` | `aab64430ea1616652946d217531bccf31170c2205269849304279df76896a5c4` |
| `Makefile` | `0edbd92f7386339d344c0d053c81075d7ae9cb26eb81ca9c79739257ca5c803d` |

The retained queue has one entry and input hash for each of the 1,015 exported paths whose
name or content matches `microchip`: five proposed exclusions/edits, 1,010 pending semantic
review. None is approved
for supply by this record. Registration-file proposals concern only the named stanza/line;
remaining content still needs disposition. Files without manufacturer matches also remain
within the full source-audit obligation.

## Review and continuation

The implementation plan requires Claude consultation for documentation-only units. The first
consultation produced no stdout or stderr and was canceled; the helper confirmed it closed.
An attempt to launch with provider access was initially rejected by automatic approval review because
the prepared brief included private project details and filesystem paths for an external
provider. The user then explicitly approved that disclosure and read-only Claude review.
The subsequent consultation returned an independent assessment supporting the five exclusions
and confirming the cited source anchors. It identified additional overlap, the distinction
between discretionary exclusions and explicit contract requirements, and search-coverage limits.
The added overlap and rationale above address those findings. A comparison round also corrected
control-record gaps, archive-member completeness, and the definition of manufacturer matches.
The final confirmation explicitly accepted the exact recommendation, amended audit text and
plan update with no remaining objections. The rejected launch is not evidence that the earlier
attempt transmitted nothing.
Operator active time is unmeasured; user approval is not a human technical review.
This is one Claude agent's documentation review, not a code-review swarm or an experimental
attribution review. The peer checked source content, anchors, recorded counts and script logic;
it did not execute scans, recompute hashes, or verify remote Git state. Both preparation and
review contexts read reference source and are ineligible for clean-side implementation.

The successful consultation used `claude-opus-5[1m]` for an initial assessment, one comparison
and final confirmation. CLI-reported `total_cost_usd` values were 1.4562315, 2.440799 and
2.961426 respectively; these reported values are not summed across the resumed session.
The canceled attempt's cost is unknown. Registration, tracked-file and explicit changed-file
privacy, local link targets, control-character and whitespace checks passed. No production code
changed, so kernel compilation and code test suites were not rerun for this documentation unit.

If the current experimental plan continues, implement the accepted exclusions
with regression tests and the plan's code-review procedure. Create a new export attempt and
retain the old one. Verify its complete inventory in a fresh case-sensitive guest; disabling
a Kconfig option alone cannot remove readable source. Continue all other semantic dispositions,
fixture facts/configuration, complete API exports, scaffolding and offline placeholder build.
M02b harness qualification and M05 launch remain blocked on their existing gates.

For the broader audit, prioritize other SPI Ethernet implementations as well as manufacturer
matches. Consider systematic reference-identifier/value searches and the frozen overlap scanner;
neither has run in this unit. Do not tune frozen scanner settings or approve entire driver
classes by analogy. Each supplied hardware fact still needs its own disposition. Generic OS
API usage alone is not evidence of forbidden exposure.

Private audit scratch record: `driver-m02a-audit`. It contains the exact scan script/results,
control results, selected source copies and hashes, the 1,015-path queue and consultation state.
These are temporary local artifacts; durable/off-host retention is not established. Keep raw
source excerpts and consultation payloads outside this repository and outside implementer inputs.
