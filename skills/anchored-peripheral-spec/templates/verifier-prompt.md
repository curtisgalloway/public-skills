<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the independent verifier subagent; substitute every <angle-bracket> placeholder.
-->

Independently verify the source-anchored spec at <path-to-spec>. You did not write it; do not fix
it. Load `anchored-peripheral-spec` for the anchor grammar, the labels, and the required
structure. The source checkout is at <source checkout>; read it at the spec's `Source pin:`
commit (<repo-name>@<commit>) — verifying against any other revision is verifying the wrong text.
<If a target tree was read: the target checkout is at <target checkout> at the `Target pin:`.>

This is an ACCURACY check. You may open any file and quote source and spec freely. Your quota is
findings, not confirmations: a verdict with zero findings on a spec of this size is itself
suspicious — say what you did to earn it.

1. MECHANICAL: run
     python3 <this-skill>/scripts/anchor_check.py <path-to-spec> --repo <source checkout> \
         [--target-repo <target checkout>] -o docs/spec-reports/<device>-check-<date>.txt
     python3 <this-skill>/scripts/inventory_check.py <path-to-spec> --repo <source checkout> \
         --headers <register header(s)> --all > docs/spec-reports/<device>-inventory-<date>.txt
   Any anchor error, inventory MISMATCH, or CONFLICT is a FAIL. Every warning must be justified in
   the spec or is a finding. Every inventory omission is a finding unless the spec names it as
   out of scope with a reason.
2. CLAIM-BY-CLAIM: run
     python3 <this-skill>/scripts/anchor_check.py <path-to-spec> --repo <source checkout> --show
   and read the review sheet. For EVERY anchored claim, decide whether the cited lines actually
   support it: the offset is the #define's value, the bit is the mask's bit, the step is what the
   statement does, the layout matches the struct, the ordering is the code's ordering. Cheaper
   and more reliable than hundreds of lookups: dump the main source files in full once and check
   the anchors against them. A range that contains the truth but is padded ("the whole function")
   is a finding: anchors must be as tight as the claim. A symbol naming the wrong definition, or
   an anchor at the guard/helper instead of the load-bearing statement or call site, is a finding.
   A claim that is simply wrong about the code is a finding of the highest importance — list
   those first.
3. THE CLASSES THE SHEET CANNOT SETTLE — do these deliberately, they are where errors hide:
   - COUNTS and cardinalities ("eight entry points", "a 9-word hole", "three registers"):
     recompute every one from the code or the DT cell values; never accept.
   - NEGATIVE and global claims ("never written", "no handler anywhere", "not referenced"):
     re-establish each by search over the whole file or tree, and say you did.
   - CROSS-REFERENCES: every §n and gotcha/milestone number in the text points at the item it
     describes (off-by-one after renumbering is common).
   - LABELS: every `[hw-required]` has a `[doc:]` that actually says so; every `[as-implemented]`
     appears on the verify-on-hardware list; steps with no label are findings.
   - DEFINITION DUPLICATES: when a header defines the same register twice (a DP_ and a non-DP_
     typedef), the anchor points at the one the driver uses.
4. COVERAGE: every constant, step, layout, interrupt, and gotcha carries `[src:]`/`[tgt:]` and/or
   `[doc:]`; nothing carries neither (prose claims escape `--strict` — read for them). All twelve
   required sections are present (the spec may number them differently — map them), including
   the verify-on-hardware list and open questions; the register map follows the databook's
   organization, not driver-touch order, and covers untouched registers from documents where a
   document exists.
5. DOCUMENTS: `[doc:]` citations name obtainable documents with section numbers; spot-check that
   a cited section covers what the claim says when the document is available to you; say which
   you could not open.
6. NOTICE + RECORD: the spec opens with the provenance notice (derived from the pin; every fact
   anchored; source is authoritative — fix the spec on disagreement; run `--drift` before trusting
   at a newer commit; verification record at the end) and ends with an empty verification record
   for the orchestrator to fill.

Return exactly: "PASS + <report path>", or "FAIL + <report path>" + a list of
{section, spec line, anchor, one-line reason} entries — wrong claims first, then wrong counts and
unestablished negatives, then padded/misaimed anchors, then label and coverage gaps — and whether
the notice is missing or deficient. Write the full findings list to
docs/spec-reports/<device>-verify-<date>.txt as well. Do not edit the spec.
