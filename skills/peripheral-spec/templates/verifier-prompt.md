<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the independent verifier subagent; substitute every <angle-bracket> placeholder.
-->

Independently verify the clean-room spec at <path-to-spec>. You did not write it; do not fix it.
Load `os-investigator` — it is the canonical statement of allowed/forbidden and ships the scanner.
Obtain the source at the exact pinned commit (<repo>@<commit>) using the file map in the sidecar
docs/provenance/<device>-map.txt; verifying against any other revision is verifying against the
wrong text. You are a designated clean-room reader; run with CLEANROOM_ROLE=verifier if hooks are
installed.

1. MECHANICAL: run
     python3 <os-investigator>/scripts/leak_scan.py <path-to-spec> \
         --against <files from the sidecar map> [--whitelist <databook nomenclature file>]
   Save the full report to docs/provenance/<device>-scan-<date>.txt. Review every finding:
   ALL-CAPS identifier hits that are genuine databook nomenclature go into the whitelist file
   (record that you did), everything else is a failure.
2. LEAK JUDGMENT: confirm the spec contains NO source code from <repo(s)>: no verbatim or
   near-verbatim code in any language, no struct/enum/#define/macro/function bodies or initializer
   tables, no copied code comments, no prose that tracks a function statement-by-statement. You may
   open the sidecar-map files at the pinned commit to compare. NEVER quote source code or the
   offending spec text — cite spec section + line range only.
3. STRUCTURE: registers are grouped per the databook's organization and sections follow hardware
   function — the spec does not mirror the source driver's file/function decomposition. Constants
   and sequence steps carry provenance tags; [source-observed] orderings/constants carry their
   required caveats ("order not known to be required" / "re-derive on hardware").
4. ATTRACTANTS: the spec body contains NO source-tree file paths and no "<source OS> does X in
   file Y" narration — facts read as hardware facts; the sidecar map exists at
   docs/provenance/<device>-map.txt and the spec's attestation carries only <repo>@<commit>.
5. NOTICE: the spec opens with the clean-room usage notice instructing consumers (human or agent)
   NOT to read the original source, naming the spec + its cited public references as the only
   implementation inputs, routing gaps through the spec-gap protocol (docs/spec-gaps/), forbidding
   verification of [source-observed] facts against the source and the opening of
   docs/provenance/, and containing the pre-merge-gate and hash-match clauses.

Return exactly: "PASS + <scan-report path>", or "FAIL + <scan-report path>" + a list of
{section, line range, one-line reason} + whether the usage notice is missing or deficient.
