# Hook and audit tests

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

Python 3 stdlib only, no dependencies. From the repo root:

```bash
python3 -m unittest discover -s skills/cleanroom-implementer/tests -v
```

Every test points `CLEANROOM_PROJECT_DIR` at a fresh temp directory, so running
the suite never writes a hook log into a real project or into this repo. One
case instead supplies `workspacePaths` and no variable at all, which is how
Antigravity actually reports the workspace; the legacy `GEMINI_PROJECT_DIR` and
`CLAUDE_PROJECT_DIR` fallbacks have their own case too.

## What is being pinned

These suites exist mostly to protect decisions that look like bugs until you
know why they are there. Five in particular:

- **`test_allow_is_explicit`** — the allow path prints
  `{"decision": "allow"}`, and that is not decoration. Antigravity's PreToolUse
  contract does not accept empty stdout as permission to proceed, so a hook that
  stays silent on the happy path can deny every tool call in the session. An
  enforcement layer that breaks normal work gets deleted by lunchtime, so this
  is as load-bearing as the blocking itself.
- **`test_edit_content_is_not_scanned`** / **`test_code_edit_content_is_not_scanned`**
  — the hook checks tool *targets*, not written *content*. A code comment
  mentioning `trusted-firmware-a`, or a pre-fetch list naming `kernel.org`, must
  not block the edit that adds it. Content-level leaks are `session_audit.py`'s
  job and the pre-merge output scan's, not the hook's. The second case is the
  load-bearing one: unrecognised argument keys *are* scanned for URLs, so
  `CodeEdit` has to stay exempt by name.
- **`test_malformed_input_allows_explicitly`** — bad input exits 0 *and* prints
  the allow object. A hook that blocks on its own parse failure would wedge
  every session in the workspace.
- **`test_deny_speaks_every_harness_dialect`** — one deny emits a
  `decision: deny` object (Antigravity), `hookSpecificOutput` (Claude Code), a
  stderr reason, and exit 2. Drop any one of those and the hook silently fails
  open somewhere.
- **`test_shares_policy_with_the_hook`** — `session_audit.py` imports
  `cleanroom_hook.py` from its own directory so enforcement and detection read
  one policy. The fixture pattern `acme-vendor-blob-sdk` appears in no
  built-in default, so a finding proves the shared loader ran. If that import
  is ever severed, this test goes red rather than the two silently drifting.
- **`TestToolVocabularies`** — nothing keys off a tool-name table.
  `view_file`, `run_command`, `grep_search` and `read_file` are caught by their
  *argument names* — `TargetFile`, `CommandLine`, `Cwd`, `SearchDirectory`,
  `file_path` — case-folded, which is what lets one hook survive Antigravity's
  PascalCase arguments, its renames between releases, and MCP tools nobody
  anticipated.

Also pinned: role scoping allows *and still logs* (the log is the evidentiary
record, so an authorized read that goes unlogged is a failure), matcher `.*`
coverage of unknown MCP-style tools, policy discovery under `.agents/` with no
env var set, and the hook recording `transcriptPath`/`artifactDirectoryPath` so
the pre-merge audit can find what to read instead of guessing.

## Fixtures

Hand-written, not captured sessions, one per record shape the auditor must
read:

- `antigravity_clean_session.jsonl` / `antigravity_dirty_session.jsonl` —
  Antigravity session records: `toolCall` objects with PascalCase args
  (`TargetFile`, `CommandLine`, `Cwd`, `CodeEdit`), the result beside the call
  rather than inside it, and one `toolCalls[]` entry.
- `clean_session.jsonl` / `dirty_session.jsonl` / `custom_policy_session.jsonl`
  — Claude Code's `tool_use`/`tool_result` shape.
- `antigravity_artifacts/` — a task-artifact directory. `walkthrough.md` is
  contaminated; `implementation-plan.md` is clean *and* deliberately dense with
  target-OS Rust, pinning the rule that text artifacts are scanned for license
  markers only. A plan quoting the driver the agent just wrote is not evidence.
- The SQLite case builds its store in a temp dir at runtime — no binary
  fixtures in the repo.

Contaminated fixtures carry license *markers* — `MODULE_LICENSE`, an SPDX GPL
tag, an `EXPORT_SYMBOL_GPL` line — because markers are what the auditor
detects; they hold no real source, and should never be made to.
