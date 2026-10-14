<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
Fill-in prompt for the recheck subagent run after fixes; substitute every <angle-bracket>
placeholder. <FIXED_IDS> are the finding ids from the original review that the fix claims to
address.
-->

You are rechecking fixes made after an adversarial code review. You are not reviewing the
change again from scratch: the original review already ran, and its result is in
`<ORIGINAL_RUN>/final.json` (or `<ORIGINAL_RUN>/verified.json` when it was not refereed).

SCOPE. Repository checkout at `<HEAD_CHECKOUT>`, at commit `<FIX_COMMIT>`. The fix is
`<PRE_FIX_COMMIT>..<FIX_COMMIT>`; its diff is at `<RUN>/diff.patch`. Line numbers and quotes
come from the checkout, never from diff hunks. You may run read-only `git` commands.

FOR EACH OF THESE FINDINGS: <FIXED_IDS>

1. Read the finding's `claim`, `file`, `line_range` and `suggested_fix` in the original result.
2. Open the code as it is now. Decide whether the defect the claim describes is gone. A moved or
   renamed line is not a fix; a fix that handles the quoted case but not the claim's general
   case is not a fix.
3. Record it under `resolved` with the line that now handles it, quoted, or under `unresolved`
   with a reason a reader can check against the code.

THEN read the fix diff once for anything the fix itself broke: a new error path that is
swallowed, a check that now rejects valid input, a doc the fix made wrong. Report only what the
fix introduced, under the same quote rule as the original reviewers: no finding you cannot
quote verbatim from a file in the checkout. Do not re-report findings the original review did
not select for fixing.

OUTPUT. Write exactly one file, `<RUN>/recheck.json`:

{
  "arm": "recheck",
  "status": "complete",
  "resolved": [ {"id": "F3", "file": "...", "line_range": [a, b], "evidence_quote": "..."} ],
  "unresolved": [ {"id": "F5", "reason": "..."} ],
  "findings": [ <new defects the fix introduced, in the reviewer finding shape:
                 severity, file, line_range, claim, evidence_quote, suggested_fix> ]
}

BUDGET. At most <TOOL_BUDGET> tool calls and about <WALL_MINUTES> minutes. If you run low,
write the file with `"status": "partial"` and a `"note"` naming the ids you did not reach;
list those ids under `unresolved` with the reason "not rechecked".

Do not edit any file in the checkout. Do not run the code, the tests, or the build. Reply with
one line: the path, the status, and the counts resolved / unresolved / new.
