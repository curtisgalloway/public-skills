<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the independent verifier subagent; substitute every <angle-bracket> placeholder.
-->

Independently verify the source-anchored spec at <path-to-spec>. You did not write it; do not fix
it. Load `anchored-peripheral-spec` for the anchor grammar and the required structure. The source
checkout is at <source checkout>; check out or otherwise read it at the spec's `Source pin:`
commit (<repo-name>@<commit>) — verifying against any other revision is verifying the wrong text.
<If a target tree was read: the target checkout is at <target checkout> at the `Target pin:`.>

This is an ACCURACY check. You may open any file and quote source and spec freely.

1. MECHANICAL: run
     python3 <this-skill>/scripts/anchor_check.py <path-to-spec> --repo <source checkout> \
         [--target-repo <target checkout>] -o docs/spec-reports/<device>-check-<date>.txt
   Any error is a FAIL. Every warning must be justified in the spec or is a finding.
2. CLAIM-BY-CLAIM: run
     python3 <this-skill>/scripts/anchor_check.py <path-to-spec> --repo <source checkout> --show
   and read the review sheet. For EVERY anchored claim, decide whether the cited lines actually
   support it: the offset is the #define's value, the bit is the mask's bit, the step is what the
   statement does, the layout matches the struct, the ordering is the code's ordering. A range
   that contains the truth but is padded ("the whole function") is a finding: anchors must be as
   tight as the claim. A symbol that names the wrong definition is a finding.
3. COVERAGE: every constant, step, layout, interrupt, and gotcha carries `[src:]`/`[tgt:]` and/or
   `[doc:]`; nothing carries neither. All twelve required sections are present; the register map
   follows the databook's organization, not driver-touch order; orderings are labelled required
   (datasheet) vs driver habit vs explained-by-comment/commit vs reason-not-known.
4. DOCUMENTS: `[doc:]` citations name obtainable documents with section numbers; spot-check that
   a cited section covers what the claim says when the document is available to you.
5. NOTICE + RECORD: the spec opens with the provenance notice (derived from the pin; every fact
   anchored; source is authoritative — fix the spec on disagreement; run `--drift` before trusting
   at a newer commit; verification record at the end) and ends with an empty verification record
   for the orchestrator to fill.

Return exactly: "PASS + <report path>", or "FAIL + <report path>" + a list of
{section, spec line, anchor, one-line reason} entries, and whether the notice is missing or
deficient. Do not edit the spec.
