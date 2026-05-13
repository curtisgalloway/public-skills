---
name: learn
description: Review the current session transcript for things that would have gone smoother with prior knowledge — failed commands and retries, wrong tool arguments, code patterns that didn't work, user corrections — and propose additions to either the workspace AGENTS.md or the global AGENTS.md. Use when the user invokes /learn or asks to "extract learnings" / "update AGENTS.md from this session".
---

# Learn: extract durable lessons from the current session

The goal is to convert *this session's* mistakes, retries, and corrections into instructions that future sessions will see in their context. The output is one or more proposed edits to a CLAUDE.md file — never silent writes.

## Where things live

- **Current-session transcript:** see the `claude-session-transcript` skill for the JSONL location and how to find the live session. Read `$HOME/.claude/skills/claude-session-transcript/SKILL.md` before doing transcript work.
- **Global AGENTS.md:** `$HOME/.claude/AGENTS.md` (or `CLAUDE.md` if AGENTS.md is absent) — applies to every project. Use for OS, language toolchain, CLI ergonomics, shell quoting, generic tool gotchas.
- **Workspace AGENTS.md:** `<repo-root>/AGENTS.md` (or `CLAUDE.md` as fallback) if one exists. Use for project conventions, paths, infra specifics, and anything that only matters inside this repo. If neither exists and the lesson is project-scoped, ask the user whether to create one before writing.
- **This skill itself:** `$HOME/.claude/skills/learn/SKILL.md`. If the session surfaced a *kind* of learning the procedure below didn't anticipate, the skill itself is a valid target — see "Self-update" near the bottom.

## What counts as a learning

A learning is something a future session would benefit from knowing *before* it starts working. Strong signals from the transcript:

- **Failed-then-fixed commands.** A Bash call returns non-zero, then a follow-up call with different flags / different tool / different syntax succeeds. The fix is the lesson.
- **Tool-call validation errors or wrong arguments.** A tool was called with a missing/invalid parameter, then re-called correctly.
- **User corrections.** The user said "no, don't do X" / "use Y instead" / "stop doing Z". These are the highest-signal items — capture them faithfully.
- **Environment surprises.** A command failed because of something specific to this machine/repo (PEP 668, blocked URL, missing tool, custom path).
- **Platform / OS differences.** A command worked one way on the host platform and a different way somewhere else: BSD vs GNU coreutils flags (`sed -i ''` on macOS vs `sed -i` on Linux; `find`, `xargs`, `date`, `stat`), package managers (`brew` vs `apt`/`dnf`/`pacman`), shell version (macOS bash 3.x has no `declare -A`/no `${var^^}`), platform-only tools (`pbcopy`, `osascript`, `launchctl` vs `systemctl`), or arch (`arm64` vs `x86_64`, Rosetta). Always note *which* platform the rule applies to — see classification below.
- **Code patterns that didn't work.** A first-attempt implementation got rejected by tests/lints/the user, and a different approach worked.
- **Validated non-obvious choices.** The user explicitly approved an unusual approach ("yeah, the bundled PR was right"). Worth capturing so the next session doesn't second-guess it.

What does **NOT** count (skip these):
- Bugs you fixed in the code itself — those live in the commit, not in CLAUDE.md.
- One-off file paths or values from this task.
- Things already covered by an existing instruction in either CLAUDE.md (check first — don't duplicate).
- Routine work that succeeded on the first try.

## Procedure

1. **Locate the live transcript** using the procedure in the `claude-session-transcript` skill. Read it with `Read` (use `offset`/`limit` for large files) or extract just user/tool events with `jq`.

2. **Scan for the signals listed above.** Walk forward through the transcript. For each candidate, note: (a) what was tried, (b) what failed or was corrected, (c) what worked, (d) why — the underlying reason, not just the surface fix.

3. **Read the existing instruction files** before proposing anything:
   - `$HOME/.claude/AGENTS.md` (or `CLAUDE.md` if absent) — always
   - `<cwd>/AGENTS.md` (or `CLAUDE.md` as fallback) if it exists; also check parent directories up to the repo root
   - Skip any candidate already covered by existing guidance. If existing guidance is close but not quite right, propose an *edit* to that section rather than a new one.

4. **Classify each remaining candidate** as global or workspace, and tag the platform scope:
   - **Global** — applies regardless of project. OS/toolchain quirks, shell-quoting rules, CLI preferences, generic tool patterns. Goes in the global AGENTS.md.
   - **Workspace** — only relevant inside this repo. Conventions, infra endpoints, project-specific scripts, repo layout. Goes in the workspace AGENTS.md.
   - When in doubt, prefer global only if you can imagine the same lesson biting you in an unrelated project.
   - **Platform scope.** Before filing, run `uname -s` (and `uname -m` if arch matters) to confirm what the local host actually is — don't assume from past memory. Then:
     - If the lesson is truly cross-platform (e.g. shell-quoting, generic CLI ergonomics), state it without a platform qualifier.
     - If the lesson is specific to the local host's OS (the most common case for the global CLAUDE.md), prefix or section-header it accordingly — e.g. "## macOS: …" or a leading "On macOS, …". Future sessions on the same machine still benefit; future sessions on a different OS need to know to skip it.
     - If the lesson came from a *remote* host the session SSH'd into (Linux VM, container, CI runner), don't file it under the local-host platform header. It belongs either in the workspace CLAUDE.md (if the repo deploys to that host) or in a platform-tagged subsection that names the target. Misfiling a Linux-remote lesson under macOS is a real failure mode — re-read the transcript to confirm where the failing command actually ran.

5. **Draft the additions.** Match the existing file's style — short H2/H3 sections, imperative voice, code fences for commands. Keep each lesson tight: the rule, then a one-line "why" so a future reader can judge edge cases. Do not write multi-paragraph essays.

6. **Show the proposed diff to the user** before writing. Group by target file. For each proposed change, show:
   - The target file and section (existing or new)
   - The exact text to add or change
   - A one-line citation pointing back to the transcript moment that motivated it ("from the `pip install` retry on line N" / "from the user saying 'don't use --no-verify'")

7. **Wait for confirmation.** The user may accept all, accept some, edit phrasing, or reject. Apply only what they approve, using `Edit` (preferred) or `Write` (only if creating a new workspace AGENTS.md the user agreed to).

8. **Report** what was written, to which file, and which candidates were dropped (and why — usually "already covered" or "user declined").

## Style for the additions

- **Lead with the rule, then `Why:`.** One sentence each. The why lets a future session judge edge cases instead of cargo-culting.
- **Imperative, not narrative.** "Use `op run --env-file`" beats "I learned that op run is better".
- **No session-specific names.** Don't reference "the bug we hit today" or specific filenames from this task — generalize so the lesson reads correctly six months from now.
- **Don't editorialize.** No "this is important" / "remember that". The fact that it's in the instruction file already says it's important.
- **Code fences for commands.** Show the right pattern, and if the wrong pattern is instructive, show that too with a clear ✗/✓ or "don't" / "do" framing.

## Self-update: improving this skill

After scanning the transcript, also ask: *did this session contain a kind of learning the procedure above didn't anticipate?* The "What counts as a learning" list is not exhaustive — sessions surface new categories of friction over time (a new tool gotcha pattern, a new class of user correction, a new place lessons should be filed). When that happens, the skill itself becomes a target.

Signals that the skill needs an update:
- A genuine learning showed up that didn't match any signal in the list above — the procedure missed it on the first pass and you had to reach for it.
- A new file or system became a sensible home for lessons (e.g. a per-tool config file, a shared playbook), and the "Where things live" section doesn't mention it.
- A heuristic in this skill steered you wrong — e.g. you classified something as global that belonged in the workspace, or you proposed a duplicate of existing guidance because the dedup step was too loose.
- The user explicitly says "the learn skill should also …" or rejects a proposal in a way that reveals a gap in the procedure.

Treat self-updates the same as any other proposed edit: show the diff, cite the moment that motivated it, wait for confirmation. Don't expand the skill speculatively — only add a category when a concrete session moment justifies it. Prefer editing existing sections over appending new ones; this file should stay scannable.

When updating the skill, also keep the frontmatter `description` field in sync if the scope of the skill changes — that string is what future sessions see when deciding whether to invoke it.

## Things to avoid

- Don't write learnings the transcript doesn't actually support. If you can't point to the moment that motivated a rule, don't propose the rule.
- Don't propose rules that contradict existing CLAUDE.md guidance without flagging the conflict to the user explicitly.
- Don't bundle unrelated lessons into one section — keep them granular so the user can accept/reject individually.
- Don't write to any instruction file without showing the diff first. Silent writes to instruction files are exactly the kind of thing that erodes trust.
