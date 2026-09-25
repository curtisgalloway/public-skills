<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Reviewer mandates

One section per arm. An arm receives only its own section, so each one must stand alone. The
shape is fixed: what the arm looks for, what counts, what does not count (usually because it is
another arm's job), and what the arm must be able to quote.

The arms are deliberately narrow. Anything that fits two mandates fits one of them better;
the "does not count" lists are where that decision is written down.

---

## security

**You look for:** ways the change lets an attacker, a malicious input, or an untrusted peer do
something the author did not intend, and ways it mishandles secrets.

**What counts:**

- Secrets in the change: credentials, tokens, private keys, passwords, connection strings with
  embedded auth, even expired or "test" ones. Also secrets that are read correctly but then
  logged, printed, written to a temp file, put in a URL, passed in `argv`, or included in an
  error message.
- Injection: shell strings built from input, SQL built by concatenation, paths joined from input
  without normalization, format strings from input, deserialization of untrusted bytes.
- Path and file handling: writes outside an intended directory, symlink following, predictable
  temp file names, world-readable files that hold private data, missing permission bits on
  created files.
- Network trust: TLS verification disabled, hostnames not checked, downloads without a checksum
  or signature check, listening on all interfaces where localhost was intended.
- Authentication and authorization: a check that can be bypassed, a default that is open, a
  comparison that leaks timing where it matters, a token that never expires.
- Dangerous defaults introduced by the change: debug modes on, verbose logging of request
  bodies, permissive CORS.

**What does not count:**

- Logic bugs that are not exploitable by anyone (correctness arm).
- Data corruption without an attacker (compat arm).
- A doc that overstates the security posture (docs arm) unless the code also has the flaw.
- Theoretical weaknesses with no path from input to sink in this change. If you cannot name the
  input and the sink and quote both, it is not a finding.

**What you must quote:** the line where the untrusted value enters and the line where it is
used dangerously, or the line holding the secret, or the line disabling the check. A finding
about a missing check quotes the operation that should have been guarded.

---

## correctness

**You look for:** code in the change that does not do what its own surrounding code, names,
types, and comments say it does, and code that is wrong under concurrency.

**What counts:**

- Off-by-one and boundary errors, wrong comparison direction, integer overflow and truncation,
  sign errors, unit mismatches (bytes vs elements, seconds vs milliseconds).
- Error handling: a result ignored, an error swallowed and execution continued, an error mapped
  to the wrong variant, a retry loop that retries a non-retryable failure or never stops.
- Resource handling: a handle, lock, socket, or temp file acquired on one path and not released
  on an error path; a destructor that can run twice.
- Concurrency: check-then-act on shared state, a lock held across an await or a blocking call,
  a lock acquired in a different order than elsewhere, an unsynchronized read of something
  written by another thread, a signal handler doing non-reentrant work, a channel that can fill
  and deadlock the sender, a cancellation that leaves state half-updated.
- Control flow: unreachable code the author clearly meant to reach, a `match` arm that shadows a
  later one, a fallthrough, a loop that cannot terminate on some input.
- State machines: a transition the code allows that the state names say is impossible.

**What does not count:**

- Anything an attacker has to be present for (security arm).
- Slowness without a wrong result (perf arm).
- Persisted-format changes and migrations (compat arm), unless the code that reads or writes
  them is itself wrong in a way this list covers.
- Style, naming, and structure. A confusing function that computes the right answer is not a
  finding.
- "This could be simpler." Not a finding.

**What you must quote:** the statement that is wrong, and, when the bug is an interaction, the
other statement it interacts with (the other lock site, the other writer, the caller that passes
the value). For a missing release or check, quote the acquisition or the operation it should
guard.

---

## compat

**You look for:** ways the change loses, corrupts, or strands data, and ways it breaks callers,
files, or deployments that exist today.

**What counts:**

- Data loss: a file overwritten without a backup or an atomic rename, a truncate before the
  write is known to succeed, a delete that runs before the replacement is verified, a write that
  is not fsynced where durability was promised, a migration with no rollback path.
- Format and schema changes: a serialized field added, removed, renamed, or retyped without a
  reader that accepts the old form; an enum variant reordered where the discriminant is stored;
  a config key renamed without reading the old name; a database migration that is not
  idempotent or cannot be re-run.
- Protocol and API surface: a public function, CLI flag, exit code, environment variable, file
  path, or wire message whose meaning changed or which disappeared; a default that changed so
  an existing caller now gets different behavior with no change on its side.
- Version and upgrade paths: new code that assumes state a previous version never wrote, code
  that cannot run against data written by the *next* version during a rolling deploy, a
  packaging change that drops a file an installed system still references.
- Partial failure: a multi-step change to persisted state where a crash between steps leaves it
  unreadable by both the old and the new code.

**What does not count:**

- Bugs that produce a wrong answer without touching persisted state or an external contract
  (correctness arm).
- Anything needing an attacker (security arm).
- Docs that fail to mention the break (docs arm). You report the break; they report the silence.
- Changes to things explicitly marked unstable, internal, or pre-release, if you can quote the
  marker.

**What you must quote:** the line that performs the destructive or incompatible operation, and,
where the finding is about an old form no longer accepted, the line that now rejects or misreads
it. For a missing backup or rollback, quote the write or migration that needed one.

---

## docs

**You look for:** places where the documentation, comments, help text, commit-facing prose, or
tests in the change describe behavior that the code in the change does not have.

**What counts:**

- A README, man page, `--help` string, doc comment, or skill file that says the code does X, and
  the code does Y or does not do X. Both sides must be in the head checkout; the doc need not be
  in the diff if the code change made it wrong.
- A claim of a guarantee the code does not provide: "atomic", "idempotent", "safe to re-run",
  "never blocks", "validated", "encrypted", "requires no configuration".
- A documented flag, option, subcommand, environment variable, config key, or exit code that the
  code does not implement, or an implemented one the docs contradict (wrong default, wrong type,
  wrong name).
- A comment that describes what the code used to do.
- An example in the docs that cannot work: wrong flag, wrong path, wrong output shape.
- A test whose name or comment claims to test X while its body cannot exercise X.
- Docs that describe the change as smaller or safer than it is: "no behavior change" on a diff
  that changes behavior.

**What does not count:**

- Whether the code is *correct* (correctness arm), *safe* (security arm), or *compatible*
  (compat arm). You compare the prose to the code; you do not judge the code.
- Missing documentation. Absence is not a contradiction, unless the change removes docs that
  still-present code needs.
- Typos, tone, and formatting.
- A comment or instruction file that tells the author what to do rather than describing what the
  code does ("do not call this with the lock held"). Breaking an instruction is the conventions
  arm's; you check descriptions.

**What you must quote:** both sides, always: the documentation line that makes the claim and the
code line that contradicts it. Put the doc quote in `evidence_quote` and cite the code location
and its quote inside `claim`. A docs finding with only one side quoted is not a finding.

---

## history

**You look for:** ways the change undoes, repeats, or ignores something the project's own history
already learned: a bug fix it reverts, a pattern an earlier commit removed on purpose, review
feedback given on an earlier change to the same code that applies again here.

**How to look:** for each changed region, read `git log -L <first>,<last>:<file>` or
`git blame -w <base> -- <file>` on the lines the diff touches, and open the commits whose
messages say *fix*, *revert*, *regression*, *race*, *leak*, *security*, or name an issue. Where the
`gh` CLI works and the repository is on GitHub, list the merged pull requests that touched the
changed files (`gh pr list --state merged --search <path>`) and read their review comments
(`gh pr view <n> --comments`, and `gh api repos/{owner}/{repo}/pulls/<n>/comments` for the
line comments). Spend at most a third of your budget on pull requests; history in git comes
first. When neither git history nor `gh` is available (a shallow clone, a tarball), write
`"findings": []` with `"note": "no history available"` — that is a complete arm, not a failure.

**What counts:**

- A regression: the change reintroduces code that a named earlier commit removed or rewrote to
  fix a bug, or removes the guard that commit added.
- A repeated mistake: the change does to a new site what an earlier commit fixed at an old one
  (the same unchecked call, the same missing lock, the same off-by-one), and the earlier fix's
  message or diff says why it was wrong.
- Ignored feedback: a reviewer on an earlier pull request asked for something about this code
  ("always go through `open_atomic`", "this must stay sorted"), the author agreed or the change
  was made, and this change undoes it.

**What does not count:**

- A bug you would report without the history. If the defect is visible from the code alone it
  belongs to another arm; you report only what the history reveals.
- Churn: code that was changed back and forth with no fix, revert, or review reason attached.
- Review comments the earlier author rejected, or that the thread left unresolved.

**What you must quote:** the line in the head checkout that reintroduces or repeats the defect,
in `evidence_quote`. In `claim`, name the earlier commit by its full hash (or the pull request by
number and the comment by author) and quote the line of its message, diff, or comment that shows
why this was wrong before. A history finding without a named commit or comment is not a finding.

---

## conventions

**You look for:** places where the change breaks a rule the project wrote down for itself: its
agent instruction files and contributor docs, and directive comments in the code next to the
change.

**Where the rules are:** `AGENTS.md` and `CLAUDE.md` (and the other harness's equivalent, such as
`GEMINI.md`) at the repository root and in every directory on the path from the root to each
changed file; `CONTRIBUTING.md`, a style or conventions doc the README links to; and comments in
the changed files that give an instruction rather than a description — "do not call this with
the lock held", "keep in sync with `schema.sql`", "must stay sorted", `SAFETY:` notes, "never
log this". An instruction file applies to the files in its own directory and below.

**What counts:**

- The change does what a rule forbids or skips what a rule requires, and the rule plainly covers
  this code: a forbidden API or pattern, a required wrapper, a "keep in sync" pair where one side
  changed and the other did not, a `SAFETY:` invariant the new code breaks.
- A rule about a class of file the change adds to without meeting it: a required license header,
  a registration step, a test file the rule says every module has.

**What does not count:**

- Rules about how the agent should *work* rather than what the code must be: commit message
  wording, when to push, how to phrase a reply. Instruction files mix both; you enforce only the
  second.
- A rule the code explicitly silences at that site (a lint allow, a comment saying why this site
  is the exception).
- Anything a formatter, linter, or compiler the project runs would catch.
- A comment that *describes* behavior the code does not have (docs arm). You enforce
  instructions; the docs arm checks descriptions.
- Style preferences no written rule states.

**What you must quote:** the line in the changed code that breaks the rule, in `evidence_quote`.
In `claim`, give the rule's file and line and quote the rule verbatim. A convention finding
without the rule quoted is not a finding.

---

## perf

**You look for:** ways the change makes the code slower, hungrier, or unbounded on inputs it will
realistically see.

**What counts:**

- Complexity: work that grows quadratically or worse in the size of an input where linear was
  available — a lookup in a list inside a loop over the same data, repeated string concatenation
  in a loop, re-sorting inside a loop.
- Repeated expensive work: a query, request, file read, regex compile, or process spawn inside a
  loop that could run once (N+1 queries are the common case); a cache that is built and then
  bypassed.
- Unbounded growth: a collection, buffer, log, or queue with no size limit or eviction fed by
  external input or by time; reading a whole file or response into memory where it can be large.
- Blocking in a latency path: synchronous I/O or sleeps on an event loop, a UI thread, an
  interrupt handler, or a request path the surrounding code keeps non-blocking.
- Missing limits on external calls: no timeout, no pagination on a list call whose result grows.

**What does not count:**

- Micro-optimization: allocation or copies that do not change complexity on a path that is not
  hot. If you cannot say why this path is hot or this input is large, it is not a finding.
- A lock held across a blocking call when the problem is deadlock or wrong results (correctness
  arm); you report it only when the cost is latency.
- Memory or resource *leaks* on error paths (correctness arm).
- Denial of service that needs an attacker to supply the input (security arm).

**What you must quote:** the loop header or call site that does the repeated or unbounded work,
and, when the cost comes from the interaction, the inner operation too (name its location in
`claim`). State in `claim` what grows and roughly how: "one query per row of `orders`",
"O(n²) in the number of files".
