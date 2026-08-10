# Hook and audit tests

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

Python 3 stdlib only, no dependencies. From the repo root:

```bash
python3 -m unittest discover -s skills/cleanroom-implementer/tests -v
```

Every test points `CLAUDE_PROJECT_DIR` at a fresh temp directory, so running
the suite never writes a hook log into a real project or into this repo.

## What is being pinned

These suites exist mostly to protect decisions that look like bugs until you
know why they are there. Three in particular:

- **`test_edit_content_is_not_scanned`** — the hook checks tool *targets*, not
  Edit/Write *content*. A code comment mentioning `trusted-firmware-a` must not
  block the edit. Content-level leaks are `session_audit.py`'s job and the
  pre-merge output scan's, not the hook's.
- **`test_malformed_input_allows`** — bad input exits 0. A hook that blocks on
  its own parse failure would wedge every session in the project.
- **`test_shares_policy_with_the_hook`** — `session_audit.py` imports
  `cleanroom_hook.py` from its own directory so enforcement and detection read
  one policy. The fixture pattern `acme-vendor-blob-sdk` appears in no
  built-in default, so a finding proves the shared loader ran. If that import
  is ever severed, this test goes red rather than the two silently drifting.

Also pinned: role scoping allows *and still logs* (the log is the evidentiary
record, so an authorized read that goes unlogged is a failure), and matcher
`*` coverage of unknown MCP-style tools.

## Fixtures

The transcripts are hand-written JSONL in Claude Code's shape, not captured
sessions. `dirty_session.jsonl` carries license *markers* — `MODULE_LICENSE`,
an SPDX GPL tag, an `EXPORT_SYMBOL_GPL` line — because markers are what the
auditor detects; it holds no real source, and should never be made to.
