---
name: cli-conventions
description: Conventions for command-line tools that both people and agents will drive — a portable exit-code contract, a `--skill` flag that emits the tool's own usage doc, strict `--json`, and non-interactive-by-default behaviour. Use when writing a new CLI, reviewing an existing one, or deciding what a command should return when it fails.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# CLI conventions

Rules for command-line tools whose callers include programs, not just people.

A CLI is usually built and tested interactively, where a terminal exists, stdin is
attached, and a human reads "no results" and understands it. Every rule here exists
because that environment hides a defect that only appears once the caller is a
script or an agent.

Apply these to new tools. Retrofit existing ones opportunistically; adopt the
exit-code contract first, because everything else degrades gracefully and exit
codes do not.

## The exit-code contract

Callers branch on the exit status. Make it carry information.

```
0        success
1        completed; the answer is empty or negative

         ── 2–9: deterministic; an identical retry is futile ──
2        usage error (bad flags, arguments, paths)
3        missing precondition (binary, config, or file not found)
4        target unreachable (DNS failure, connection refused, no route)
5–9      reserved

         ── 10s: authentication and permission ──
10       remediable locally; retry after remediation
11       needs a person; stop
12       denied by rule or security policy
13–19    reserved

         ── 20s: transient; retry ──
20       nothing was done                → retry is free
21       partially done                  → reconcile before retrying
22       outcome unknown (no response within budget) → check state first
23       retry after a long or scheduled delay (quota reset, maintenance window)
24–29    reserved

         ── 30s: permanent; the request is void ──
30       never retry; the request itself must change
31–39    reserved

40–99    reserved for future standard classes
100–124  tool-specific
125–255  DO NOT USE
```

### Why the bands

The decade is the coarse signal and the exact code is the detail. A caller that
has never seen your tool can branch on `code / 10` and still behave sensibly —
back off on a `2x`, stop and ask a person on a `1x` — without reading your docs.
That property only holds if the bands mean the same thing across every tool you
write, so keep them stable even in a tool that emits three of them.

Under 100 is portable. 100 and above means "read this tool's documentation".

### Never emit 125–255

That range is already spoken for, and collisions are silent:

```
126        command found but not executable
127        command not found
128+N      killed by signal N   → 130 SIGINT (Ctrl-C), 137 SIGKILL, 143 SIGTERM
255        ssh's own failure, not the remote command's
```

A tool-specific `143` is indistinguishable from "something killed the process".

### Translate subprocess codes; do not propagate them

A tool that shells out and returns the child's status inherits that child's
vocabulary, and the caller cannot tell whose failure it is reading. Map at the
boundary:

- child `127` (not found) → **3**
- child `126` (not executable) → **3**
- `ssh` `255` → **4** if the transport failed, **10**/**11** if authentication did.
  `ssh host false` returns `1` while `ssh unreachable-host anything` returns `255`;
  a tool that conflates them reports a remote failure as a network failure.

### Choosing between the blocked states

Three codes all mean "this did not work and will not right now". The
discriminator is **what would have to change**:

| Code | Meaning | What unblocks it | Caller's move |
|---|---|---|---|
| `11` | blocked | a person acting | surface it, wait |
| `23` | blocked | time passing | schedule, come back later |
| `30` | **void** | nothing — the request is invalid | stop, report, do not queue |

`30` means the operation as requested can never succeed: an endpoint withdrawn,
a resource permanently gone, a feature unsupported on this platform, an account
terminated, an artifact that failed verification because it is genuinely wrong.

**`30` should be rare, and the cost is asymmetric.** Mislabelling a transient
failure as permanent makes a caller abandon recoverable work; mislabelling
permanent as transient only burns a few retries. When in doubt, do not use `30`.

A quota or usage limit is **not** `30` — it resets, so it is `23`.

### `22` is the one tools forget

`20` and `21` are claims about what happened. `22` is an admission that you do
not know: the request went out and no answer came back. For anything that mutates
state this is the most important code in the table, because a tool that reports
"no response" as a plain failure teaches its callers to retry blindly — which is
how a timed-out deploy becomes a double deploy. Make ignorance expressible.

### Exit `1` needs two mitigations

Reserve `1` for "the query was well-formed, the answer is negative" — no matches,
empty set, condition false. It is genuinely useful, and it is also a trap: under
`set -euo pipefail` an empty result kills the script exactly like a real error.
So both of these are required, not either/or:

1. **`--help` documents it**, in an exit-status section, and says plainly that
   callers wanting the soft behaviour need `|| true`.
2. **`--json` never depends on the exit status.** Type the empty case in the
   payload so structured callers branch on the document instead:

   ```json
   { "result": null, "empty": true, "reason": "no matching record" }
   ```

The inverse failure is worse and more common: **a tool that exits `0` when it
found nothing.** A caller testing the exit status then reads "success" and
proceeds on an empty answer. If a command can legitimately find nothing, it must
say so in the status, the payload, or both — never silently.

## `--skill`: ship the docs inside the binary

Every tool accepts `--skill` and prints its own agent-facing usage document to
stdout, then exits `0`.

Documentation that lives beside a tool drifts from it. Documentation compiled
into it cannot. Four requirements make that true in practice:

- **Embed at build time** — `include_str!` in Rust, `importlib.resources` in
  Python, `go:embed` in Go. A file read from disk at runtime can be from a
  different version than the binary reading it.
- **Emit a complete skill document, frontmatter included**, so
  `mytool --skill > <skills-dir>/mytool/SKILL.md` is the entire install
  procedure, under any harness.
- **Stamp the tool version into the emitted text**, so a reader knows which
  build it describes.
- **Accept `--skill` even on subcommand-style CLIs.** `mytool skill` reads more
  naturally, but uniformity beats elegance: an agent meeting an unfamiliar tool
  should be able to try `--skill` blind and expect it to work. Offer both if the
  subcommand form fits your CLI's shape.

Keep the emitted document about *driving the tool* — invocation, flags, exit
codes, output shape, common failures. It is not a copy of `--help`; it is what
you would tell someone automating the tool for the first time.

## Output contract

- **Data on stdout, everything else on stderr.** Logs, progress, warnings, and
  prompts go to stderr. Then `$(mytool ...)` is always safe and a progress
  indicator can never land in the middle of a caller's payload.
- **`--json` is strictly JSON.** No banner, no trailing "Done!", no ANSI. One
  document on stdout and nothing else. Prefer a single object over a stream
  unless the output is unbounded, in which case use newline-delimited JSON and
  say so.
- **Colour only when stdout is a terminal**, and honour `NO_COLOR`. Escape codes
  corrupt parsing and never show up in interactive testing.
- **Deterministic ordering.** Sort anything list-shaped by a stable key. It makes
  output diffable and lets callers write assertions that do not flake.
- **Stable schema.** Adding fields to `--json` is compatible; renaming or removing
  them is not. Version the payload if it will change.

## Never block without a terminal

If stdin is not a TTY, do not prompt. Either proceed with documented defaults or
exit `2` naming the flag that would have answered the question.

An unattended caller cannot answer a prompt, so a `Continue? [y/N]` does not fail
— it **hangs**, and it looks exactly like the tool being slow. That is far more
expensive to diagnose than an error, because nothing is logged and nothing exits.

Provide `--yes` for destructive confirmations so the interactive path stays safe
without stranding the automated one.

## Mutations

- **`--dry-run` on anything that changes state**, printing the exact actions it
  would take, in the same order, with the same identifiers. This is what lets a
  caller confirm intent as a *step* rather than as a guess.
- **Be idempotent where the domain allows it.** Re-running should converge, not
  double-apply. Where it cannot, that is exactly when exit `21` and `22` matter.
- **Say what changed.** A mutation that succeeds silently is indistinguishable
  from one that no-opped. Report counts, or the identifiers touched.

## Secrets

- **Never accept a secret as a command-line argument.** Argv is world-readable on
  most systems and lands in shell history and process listings. Read from an
  environment variable, a file path, or a secret-manager reference.
- **Never echo one**, including in verbose or debug output and in the message of
  an error that quotes the failing request.
- Accept a **reference** (a secret-manager URI or a path) rather than a value
  wherever the ecosystem has one, so callers never have to materialise the secret
  to pass it.

## `doctor`

Provide a `doctor` subcommand (or `--self-test`) that checks the tool's own
preconditions and reports each as a line: config found and parseable, credentials
resolvable, dependencies present, target reachable, versions compatible. Exit `0`
when everything a normal run needs is in place, otherwise the code of the first
class that failed — usually `3`, `4`, or a `1x`.

It turns "it doesn't work" into one command, and it gives an agent a cheap way to
distinguish "the tool is misconfigured" from "the request was wrong" before it
starts guessing.

## Flags and help

- **Use long flags in every example**, in `--help`, in the README, and in the
  `--skill` document. Short flags are fine to accept and dangerous to teach: a
  cluster like `-rn` can mean something entirely different from what it looks
  like, and the resulting output can be wrong rather than absent.
- **`--version` prints the version and the build identifier** (commit and date),
  and matches what `--skill` reports.
- **`--help` is complete and stable.** Include an exit-status section listing the
  codes the tool actually emits. That section is the contract.

## A CI forcing function

Most of the defects above are invisible in interactive testing. Make CI run the
tool the way a program does:

```
stdout piped (not a terminal)   → catches colour leakage and TTY assumptions
stdin closed                    → catches prompts that would hang
NO_COLOR=1                      → catches unconditional escape codes
assert on exit codes            → catches "exits 0 having found nothing"
```

Four lines of harness catches four classes of bug without anyone reasoning about
them.

## Checklist

- [ ] Exit codes follow the bands; nothing in 125–255; subprocess codes translated
- [ ] "Found nothing" is distinguishable from "succeeded" — in status, payload, or both
- [ ] `--skill` embedded at build time, frontmatter-complete, version-stamped
- [ ] Data on stdout, diagnostics on stderr
- [ ] `--json` is strictly JSON and does not depend on the exit status
- [ ] Colour suppressed when not a TTY; `NO_COLOR` honoured
- [ ] No prompt when stdin is not a TTY; `--yes` available
- [ ] `--dry-run` on every mutating path; mutations report what changed
- [ ] No secret accepted via argv or echoed in output
- [ ] `doctor` checks preconditions and exits with the matching class
- [ ] `--help` documents the exit statuses actually emitted
- [ ] CI runs the tool piped, with stdin closed and `NO_COLOR=1`
