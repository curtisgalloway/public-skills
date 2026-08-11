---
name: agent-agnostic-skills
description: >-
  How to write skills, hooks, subagent definitions and agent-facing scripts that survive a change of
  harness — Antigravity, Claude Code, whatever ships next — and how to port one that didn't. Use
  this whenever authoring or reviewing a SKILL.md, a pre-tool-use hook, a settings/permissions
  fragment, a subagent definition, or any script that resolves a project directory, a skills
  directory, a tool name, or a session transcript; whenever a path like `~/.claude/skills`, a
  variable like `$CLAUDE_PROJECT_DIR`, or a tool name like `Read`/`view_file` is about to be written
  down as a constant; whenever a skill "does nothing" under a different agent; and whenever a
  harness deprecation forces a migration. Reach for it even when the request sounds like ordinary
  skill-writing — most lock-in is added by accident, one hardcoded path at a time. Ships
  `scripts/portability_scan.py`, a mechanical check for the assumptions below.
---

<!--
SPDX-FileCopyrightText: 2026 Curtis Galloway
SPDX-License-Identifier: Apache-2.0
-->

# Agent-agnostic skills and tooling

Harness-specific assumptions do not raise. That is the whole problem.

A tool-name table that matches nothing returns an empty dict, so the hook inspects no arguments and
allows every call. A skills directory that doesn't exist falls through to a fallback that also
doesn't exist, and the error message names a path the user has never had. A hook wired to an event
this harness doesn't fire simply never runs. In each case the code executes, exits zero, and reports
success. **Portability bugs present as silence**, which is why they survive review and why a
security-shaped skill can ship with its enforcement quietly disconnected.

So the discipline here isn't about elegance or hypothetical future agents. It's that a hardcoded
harness assumption is an *unobservable* failure, and the fixes below are mostly about converting
silent no-ops into loud, checkable behaviour.

## Bind to the most stable layer available

Rank the things you could key on, most stable first. Use the highest one that answers your question,
and treat everything below it as a fallback rather than a plan:

1. **Data carried in the event payload** — `workspacePaths`, `transcriptPath`, `cwd`. It travels
   with the call, so it can't be out of sync with the session that made it.
2. **Relative position on disk** — a sibling skill in the same tree. Needs no configuration and
   survives every rename the vendor ships.
3. **Your own environment variable** — you choose the name, so nobody can deprecate it.
4. **Argument names** — `file_path`, `command`, `url`, `TargetFile`. These converge across
   harnesses far more than tool names do, because they describe the *thing* rather than the vendor's
   product decisions.
5. **The harness's environment variables** — `$CLAUDE_PROJECT_DIR`, `$GEMINI_PROJECT_DIR`. Fine in
   a ladder, fatal as a single choice; some harnesses export none at all.
6. **Tool names** — `Read` / `read_file` / `view_file`. Renamed between releases, different per
   vendor. Never key logic on these.
7. **Absolute installed paths** — `~/.claude/skills/...`. The least stable thing you can write down.

The general move: prefer what the *call* tells you over what the *environment* tells you, and prefer
what *describes the operation* over what *names the product*.

## Resolution ladders, not constants

Anywhere you need a location, write an ordered list and walk it. The shape:

```python
def project_dir(cwd_hint=None):
    explicit = os.environ.get("MYTOOL_PROJECT_DIR")   # yours; nobody deprecates it
    if explicit:
        return explicit
    if cwd_hint:                                      # from the event payload
        return _find_root(cwd_hint)
    for var in ("GEMINI_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        if os.environ.get(var):
            return os.environ[var]
    return _find_root(os.getcwd())                    # walk up to a config dir
```

Three properties make a ladder worth the extra lines:

- **It degrades instead of failing.** A missing harness is one skipped rung.
- **It documents the landscape.** The list is the compatibility matrix, in code, next to the logic.
- **It fails loudly when it fails at all.** When nothing resolves, report *what you searched* —
  a user staring at "not found: `~/.claude/skills/foo`" on a machine that has never had Claude Code
  learns nothing; a user seeing all six candidate roots knows immediately which one to create.

**Bound the walk-up rung, and say where you landed.** A ladder that ends in "walk up until you find
`.git` or a config directory" will always resolve to *something*, and that something can be
correct-by-the-rule and wrong-in-fact — a nested checkout, a sandbox inside a larger repo, a
worktree. Then your tool writes its log or reads its policy somewhere nobody expected, silently,
because every rung reported success. (This is not hypothetical: while this skill was being written,
a hook under test walked past its own working directory into the enclosing repository and left its
audit log there.) Two cheap defences: stop the walk at a boundary you name rather than at the
filesystem root, and record the resolved root in your first log line, so "where did it think it
was?" is answerable after the fact instead of by re-deriving it.

Same pattern for skills directories, config files, and policy files. See
`skills/cynthion-capture/scripts/_sibling.py` in this repo for a worked example that prefers the
zero-configuration sibling case and keeps dead harnesses only as labelled legacy rungs.

## Match on argument names, not tool names

The same operation is called something different everywhere, and the names churn:

| Operation | Antigravity | Claude Code | Gemini CLI (retired) |
|---|---|---|---|
| read a file | `view_file`, `read_file` | `Read` | `read_file` |
| run a shell command | `run_command` | `Bash` | `run_shell_command` |
| fetch a URL | `read_url_content` | `WebFetch` | `web_fetch` |
| search the web | `search_web` | `WebSearch` | `google_web_search` |
| delegate | `invoke_subagent` | `Task` | (subagent invocation) |

A dictionary keyed on one column is a lock-in you cannot see failing. Key on argument names instead
and classify them by *kind*:

- **path-ish** (`file_path`, `path`, `paths`, `TargetFile`, `Cwd`, `SearchDirectory`) — match against
  path rules.
- **command-ish** (`command`, `CommandLine`, `cmd`) — match against path *and* URL rules; a shell
  line can contain either.
- **authored content** (`content`, `CodeEdit`, `new_string`, `patch`) — **never** match. A doc
  comment that names a forbidden project, or a reference list that cites a URL you block, must not
  block the edit that writes it. Exempt these by name, deliberately, with a comment saying why —
  it looks like an oversight to the next reader, and someone will "fix" it.
- **everything else** — match URLs only. Path patterns over arbitrary prose false-positive.

**Case-fold the keys.** That one line is what makes `CommandLine`, `command_line` and `command` land
in the same set, and it is why the same matcher survives a vendor switching conventions.

The payoff: a tool from a harness you have never heard of, with a name nobody anticipated, is still
checked correctly as long as it takes an argument that means "file path". That is the property to
optimise for.

## Emit every dialect at once

Protocol contracts differ, and they differ in ways that fail *open*:

| | Antigravity | Claude Code |
|---|---|---|
| deny a call | `{"decision":"deny","reason":…}` on stdout | exit 2 + stderr, or `hookSpecificOutput.permissionDecision: "deny"` |
| allow a call | `{"decision":"allow"}` — **required**, empty stdout is rejected | exit 0; silence is "no objection". `permissionDecision: "allow"` is **not** silence — it auto-approves |
| payload shape | `toolCall.{name,args}`, camelCase envelope, PascalCase args | `tool_name`/`tool_input`, flat, snake_case |

For a **deny**, these formats are additive: harnesses ignore the fields they don't recognise. So
don't detect the harness and branch — **emit every deny dialect in one response** and let each
reader take what it knows. One code path, no detection logic, no "which agent am I" heuristic to
get wrong.

**Allow is the exception, and getting it wrong is a permission escalation.** The symmetry breaks
because an allow field is not inert: Claude Code's `permissionDecision: "allow"` doesn't mean "no
objection", it means *auto-approve* — it consumes the user's permission prompt and lets the call
through unasked. Broadcast that alongside Antigravity's allow and your hook quietly grants every
call it was only supposed to have no opinion about. So:

- **Deny** — every dialect at once.
- **Allow** — only the dialect that *requires* it (Antigravity's `{"decision":"allow"}`), and
  nothing that any other harness would read as approval. Where silence means "no objection", stay
  silent.

The general rule this is an instance of: broadcasting is safe for fields that *withhold*
permission and dangerous for fields that *grant* it. Before you add a field to a
fire-and-forget response, ask which of the two it is.

**Do not assume silence means yes.** Antigravity's pre-tool-use contract rejects an empty response,
so a hook that allows by printing nothing can deny *every* tool call in the session. That failure is
worse than a missing hook: an enforcement layer that breaks ordinary work gets ripped out by
lunchtime, and the protection goes with it. Print the allow explicitly, on every allow path,
including the one you take when the input is malformed.

## Decide fail-open vs fail-closed per path, not per tool

These pull in opposite directions and both are right:

- **The enforcement path fails closed.** When you have matched something forbidden, deny — and pick
  the mechanism every harness treats as a block (a non-zero exit is the widely-shared one).
- **The tool's own error path fails open.** Malformed input, an unreadable policy file, a logging
  failure: allow, silently. A hook that blocks because it couldn't parse its own configuration
  wedges every session in the workspace.

Write both properties down as tests, because each one looks like a bug to someone who only knows
about the other.

## What not to abstract

Capability denial is genuinely different per harness — deny lists with `tool(arg)` syntax, TOML
policy engines with priorities, permission modes, sandbox policies. Do **not** invent a universal
wrapper over these. A layer that pretends they're the same ships a wall with a hole in it, and the
hole is invisible because your abstraction reports success.

Split it instead:

- **One harness-neutral data file** holding *what* is forbidden (paths, URL patterns, roots), read by
  *your* code. This is portable because you own the reader.
- **N thin wiring fragments**, one per harness, holding *how* it is enforced. These are short,
  obviously harness-specific, and expected to rot.

Then say, in each fragment, which file it must stay in sync with. Two enforcement layers that drift
apart are worse than one, because the weaker one creates the confidence.

## Enumerate the ways your integration can be inert

Every one of these was observed in real harnesses, and none of them produce an error:

- **Untrusted workspace** → workspace-local hooks are silently not loaded.
- **Unmapped tool name in an allowlist** → dropped without warning. You believe you removed a
  capability, or you believe you kept one. Both are wrong and both are quiet.
- **IDE versus CLI** → the same product may run hooks in one surface and not the other.
- **Wrong event name** → the hook is installed, valid, and never fires.
- **Payload the harness didn't expect** → it either denies everything (loud, at least) or allows
  everything (silent).

The remedy is the same in all cases and it is not more code: **provoke it**. After install, and
after every upgrade, deliberately trigger the thing your tool is supposed to catch and confirm the
log line appears. A hook you believe is running and isn't is worse than no hook, because you get the
confidence without the enforcement. Ship this instruction *with* the tool, not as a footnote.

## Sniff formats; don't assume one

Session records are JSONL here, single-document JSON there, SQLite somewhere else, plus markdown
artifacts a harness writes alongside the conversation. Sniff by magic bytes, then by parse attempt,
then fall back to text. Walk directories rather than demanding a file. Recognise several record
shapes in one pass — nested `toolCall` objects, `toolCalls[]` arrays, `functionCall` parts,
`tool_use` blocks — because a build can change how it records a session without telling you.

`skills/cleanroom-implementer/scripts/session_audit.py` is the worked example.

## Write the documentation portably too

- **`AGENTS.md` is the cross-tool context file.** Harness-specific ones (`CLAUDE.md`, `GEMINI.md`)
  *override* it. Keep exactly one real copy: if you duplicate the content into the override, the two
  drift, and the file that loses is the one you edited.
- **Use placeholders for install paths** — `<skill-name>/scripts/tool.py`, not
  `~/.claude/skills/<skill-name>/scripts/tool.py`. If the reader must substitute something, say so
  once at the top rather than encoding one vendor's layout into every command.
- **Name the mechanism, not the brand**, in prose — "the pre-tool-use hook", "the delegation tool",
  "the permissions layer" — and give the per-harness name in a table or parenthetical, where it can
  be updated in one place.
- **"Subagent" does not mean isolation.** A subagent gets a separate *context*; it usually inherits
  the parent's *environment, credentials and permissions*. If you need separated authority — a role
  that may do what the parent may not — you need a separate **process**, not a subagent. Skills that
  confuse these two ship a wall that a delegation call walks straight through.
- **Date your facts and name the ground truth.** Every path and event name in a skill is a claim
  about a moving target. Say when it was verified, and tell the reader the command that shows the
  current answer (`/hooks`, `/permissions`, `/agents`, `/skills`) so they can check rather than
  trust. `references/harness-matrix.md` holds this repo's dated table.

## When a harness dies

They do. Gemini CLI stopped serving on 2026-06-18, about a month after its replacement was
announced. The migration rule that keeps things honest:

- **Keep it in search ladders**, as a rung labelled legacy. Users mid-migration still have those
  directories, and a silent removal breaks them for no reason.
- **Delete it from the prose.** A new reader following your install instructions must not be told to
  configure a product that no longer exists.

The asymmetry is the point: code should be generous about what it accepts, documentation should be
strict about what it recommends.

## Testing portability

- **Table-driven cases per dialect.** One test per payload shape and argument convention, not one
  test for "the happy path".
- **Pin the invariants that look like bugs** — content-is-not-scanned, allow-is-explicit,
  malformed-input-allows — each with a comment saying *why*, because the next reader's instinct will
  be to remove them.
- **Build binary fixtures at runtime** (SQLite stores, archives) rather than committing them, so the
  fixture stays readable and reviewable as code.
- **One fixture per record shape**, named for the harness it imitates.

## The mechanical check

```
python3 scripts/portability_scan.py skills/<name>/
```

It flags single-harness paths, single-harness environment variables, brand context files named
without `AGENTS.md`, tool-name tables, and absolute home paths. The core heuristic is **ladder vs
constant**: one harness's names appearing alone is lock-in; several appearing together is a
translation table, which is the pattern this skill is arguing for, so it passes.

A finding is a prompt to look, not a verdict. A skill that is *deliberately* single-harness — one
that reads a specific agent's transcripts, or a per-harness install asset — will light up, and that
is the scanner working. Record the decision rather than arguing with it: `portability-ok` on the
line, or `portability-scan: intentional` anywhere in the file, each with a reason beside it. In
Markdown, put the marker inside an HTML comment so readers never see it.

A clean scan is necessary, not sufficient. It cannot tell you the event name is wrong, and it will
never replace provoking the tool and watching for the log line.
