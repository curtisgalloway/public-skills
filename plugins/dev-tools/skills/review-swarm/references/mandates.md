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

**What you must quote:** both sides, always: the documentation line that makes the claim and the
code line that contradicts it. Put the doc quote in `evidence_quote` and cite the code location
and its quote inside `claim`. A docs finding with only one side quoted is not a finding.
