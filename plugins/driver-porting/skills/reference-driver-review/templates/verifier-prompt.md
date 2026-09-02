<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the independent verifier subagent; substitute every <angle-bracket> placeholder.
-->

Independently verify the driver review at <path-to-review>. You did not write it; do not fix it.
Load `reference-driver-review` for the verdicts and required structure, and
`anchored-peripheral-spec` for the anchor grammar. The implementation checkout is at
<impl checkout>; read it at the review's `Impl pin:` (<impl-repo-name>@<commit>). The reference
checkout is at <ref checkout>; read it at the `Ref pin:` (<ref-repo-name>@<commit>). Verifying
either side at any other revision is verifying the wrong text.

This is an ACCURACY check on both sides. You may open any file and quote both trees and the
review freely. Your quota is findings, not confirmations: a verdict with zero findings on a
review of this size is itself suspicious — say what you did to earn it.

1. MECHANICAL: run
     python3 <anchored-peripheral-spec>/scripts/anchor_check.py <path-to-review> \
         --impl-repo <impl checkout> --ref-repo <ref checkout> \
         -o docs/review-reports/<driver>-check-<date>.txt
     python3 <anchored-peripheral-spec>/scripts/inventory_check.py <path-to-review> \
         --repo <ref checkout>@<ref-commit> --headers <reference register header(s)> --all \
         > docs/review-reports/<driver>-inventory-<date>.txt
   Any anchor error, inventory MISMATCH, or CONFLICT is a FAIL. Every warning must be justified
   in the review or is a finding. Every reference-header name the review never mentions is a
   finding (an uncompared register) unless the review names it as out of scope with a reason.
2. FINDING-BY-FINDING: run
     python3 <anchored-peripheral-spec>/scripts/anchor_check.py <path-to-review> \
         --impl-repo <impl checkout> --ref-repo <ref checkout> --show
   and read the sheet. For EVERY finding, decide whether the cited lines on EACH side support it:
   the implementation really does what the [impl:] lines show, the reference really does what the
   [ref:] lines show, and the difference between them really is the difference claimed. Cheaper
   and more reliable than hundreds of lookups: dump the paired source files in full once and
   check the findings against them. A padded range ("the whole function"), a symbol naming the
   wrong definition, or an anchor at a guard/helper instead of the load-bearing statement is a
   finding. A claimed divergence that does not exist — the two sides actually agree, or the
   review compared non-corresponding functions — is a finding of the highest importance; list
   those first.
   BLIND RE-DERIVATION SAMPLE: pick ~10% of anchors at random (seed on the review's sha256 and
   say which). For each, read ONLY the cited lines and write down what they establish BEFORE
   re-reading the finding; then compare. Any finding that says more than, or other than, what you
   derived is paraphrase drift, even if the lines "support" it loosely.
3. THE CLASSES THE SHEET CANNOT SETTLE:
   - MISSING findings: re-run the search behind every claimed absence over the implementation
     (the whole file or tree, as the finding states), and say you did. An absence nobody
     re-searched is unverified.
   - VERDICTS are earned: every [bug] rests on a [doc:] that actually says so or a self-evident
     defect — a [bug] whose only evidence is "the reference differs" is misgraded [suspect];
     every [benign] states a justification that actually justifies; every [suspect] appears on
     the verify-on-hardware list; a finding with no verdict, or two, is a finding.
   - COUNTS and cardinalities: recompute every one from the trees; never accept.
   - APPLICABILITY: section 2's revision claims resolve on both sides; if the two sides target
     different IP revisions, check that the review says so and that no finding silently depends
     on the mismatch.
   - CORRESPONDENCE: spot-check the map — paired functions really correspond; every unmapped
     entry on either side is a finding or an explicit out-of-scope entry.
   - CROSS-REFERENCES: every §n and finding number points at what it describes.
4. COVERAGE: all ten required sections are present (the review may number them differently — map
   them); every finding carries both-side anchors (or extent-plus-search for an absence),
   category, verdict, and consequence; each zero-finding coverage area says what was read to
   earn it; reference quoting is rationed (flag any long verbatim run).
5. DOCUMENTS: [doc:] citations name obtainable documents with section numbers; spot-check that a
   cited section settles what the finding says it settles; say which you could not open.
6. NOTICE + RECORD: the review opens with the review notice (pins, how the reference was chosen,
   the evidence rule, --drift after fixes) and ends with an empty verification record.

Return exactly: "PASS + <report path>", or "FAIL + <report path>" + a list of
{finding, review line, anchor, one-line reason} entries — nonexistent divergences and wrong
claims first, then unestablished absences and wrong counts, then misgraded verdicts, then
padded/misaimed anchors, then coverage and structure gaps. Write the full findings list to
docs/review-reports/<driver>-verify-<date>.txt as well. Do not edit the review.
