# Portability scanner tests

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

Python 3 stdlib only, no dependencies. From the repo root:

```bash
python3 -m unittest discover -s plugins/agent-workflow/skills/agent-agnostic-skills/tests -v
```

## What is being pinned

- **`test_ladder_is_not_lock_in`** — the scanner's central distinction. Several
  harnesses named together is a resolution ladder or a translation table, which
  is the pattern this skill argues for; one harness named alone is lock-in. Lose
  the distinction and the tool either flags every compatibility table it should
  be encouraging, or stops flagging anything.
- **`test_shared_tool_names_are_not_a_table`** — `read_file` and `grep_search`
  belong to more than one agent's vocabulary, so the check resolves names to
  harness families rather than counting them. Counting alone would flag a
  perfectly portable set.
- **`test_placeholder_home_paths_are_fine`** — `/home/dev/` is the fix this check
  asks for, not a violation. Flagging placeholders would push people back toward
  real paths to quiet the tool, which is the opposite of the intent (and of this
  repo's privacy rules).
- **`test_reference_implementation_is_clean`** — the clean-room scripts this
  skill cites as worked examples are scanned on every run. A skill should not be
  able to recommend code that fails its own check, so if a future edit
  reintroduces a tool-name table or a lone harness path there, this goes red.
- **Both suppression forms** — `portability-ok` on a line and
  `portability-scan: intentional` in a file. Deliberate single-harness code must
  have a way to record the decision, or people will silence the scanner by
  deleting it.

## Fixtures

`locked_skill/` and `portable_skill/` are the same small skill written twice —
once welded to one harness, once bound to stable layers — so the suite compares
authoring style rather than subject matter. Between them the locked fixture
triggers all five checks.

The locked fixture uses a fictional account, `/home/rjmiller/`, deliberately <!-- portability-ok -->
distinct from any real contributor: it exercises the privacy/portability check
without committing a real username to a public repo, which is the very thing
that check exists to prevent.

## Known findings elsewhere in this repo

Running the scanner over `skills/` reports findings in the transcript-reading
skills (`claude-session-transcript`, `teach`) and in a few places where the
clean-room skills name Antigravity's layout specifically. Those are true
statements, not bugs: the transcript skills are bound to one agent's session
format by definition, and the clean-room install steps target one harness on
purpose. They are left unsuppressed so the report keeps telling the truth about
what is portable and what isn't — suppress a finding when you have *decided*
something is deliberately harness-specific, not to reach zero.
