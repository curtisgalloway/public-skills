---
name: consult
description: >-
  Collaborate with the other coding agent on a question or proposed approach:
  Claude Code consults Codex, and Codex consults Claude Code, through a persistent
  peer session. Use when the user asks to consult the counterpart, compare both
  agents' perspectives, or work toward consensus. The original agent leads the
  exchange and reports the agreed recommendation or unresolved disagreement.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Consult

Keep leading the user's conversation. Start a dedicated counterpart session,
exchange reasoned follow-ups, and bring the result back to the user. The user
does not need to open another terminal or copy messages. This does not attach to
an existing interactive counterpart session.

## Requirements and scope

- Python 3.9+ on macOS or Linux; standard library only (uses Unix process groups
  and `flock`). Windows is not supported.
- The counterpart's CLI on `PATH`, already authenticated: `claude` when you are
  Codex, `codex` when you are Claude Code. Normal CLI usage charges/limits apply.
- Permission to launch the counterpart and reach its provider. If the host's
  sandbox blocks this, use its normal approval mechanism; do not bypass it.
- A trusted project directory and selected task context. Invocation authorizes
  consultation about that task, not forwarding unrelated conversation history
  or secrets, changing either agent's configuration, or implementing the result.

The counterpart advises and inspects; the original agent owns implementation.
Both adapters enforce restrictions on every invocation, including resume:

| Counterpart | Inspection controls |
| --- | --- |
| Claude Code | Only `Read`, `Glob`, `Grep`; permission mode `dontAsk`; no MCP servers, hooks, Chrome, or skills; user/project settings excluded |
| Codex | Read-only sandbox, approvals `never`; user config and exec rules excluded; MCP/plugin maps cleared; hooks, multi-agent delegation, and app integrations disabled |

These controls are deliberately different. Claude cannot run shell commands;
Codex can run commands within its read-only sandbox. If evidence needs a test or
an unavailable tool, gather it in the original session under existing permissions
and share the result. CLI-owned authentication/session writes still occur. This
is not an isolation boundary for hostile projects or compromised CLIs.

Adapter flags were checked against Claude Code 2.1.277 and Codex CLI 0.155.0 on
2026-09-18. Older releases may reject flags. Fail visibly rather than removing
restrictions to make a command work. Ground truth: `claude --help`, `codex exec
--help`, and `codex exec resume --help`. See the official
[Claude programmatic guide](https://code.claude.com/docs/en/headless) and
[Codex noninteractive guide](https://developers.openai.com/codex/noninteractive).

## Conduct the discussion

1. **Frame the question.** Preserve the user's objective, constraints, relevant
   files/evidence, and open questions. Record your own current proposal in your
   conversation before consulting. Send the counterpart a neutral initial brief
   without your preferred answer, unless the user specifically requested a
   critique of that answer. Include relevant project instructions explicitly if
   they are essential; the restricted peer does not inherit your loaded context.
2. **Get an independent assessment.** Start the opposite CLI. Read the response
   and identify actual differences in assumptions, evidence, or recommendations.
   Do not treat a peer answer as verified merely because it sounds confident.
3. **Compare and investigate.** Send your proposal, substantive disagreements,
   and concrete questions. Relay answers to the counterpart's questions and any
   user corrections. Ask for counterexamples or discriminating tests when useful.
   Follow up in the same consultation, not a new peer session for every message.
4. **Confirm the exact recommendation.** Once you agree with a proposal, send its
   full final text using phase `confirm`. Ask the counterpart to explicitly agree
   or identify remaining objections. A response that changes the proposal does
   not confirm the original text. Silence, a timeout, or partial agreement is not
   consensus. Read and assess the response yourself: the helper checks that a
   confirmation turn succeeded, not whether its prose actually agrees.
5. **Close and report.** Record `consensus` only when both agents agree on the same
   recommendation. Otherwise record `unresolved` and explain the remaining
   disagreement, missing evidence, or user decision. Give the user the conclusion,
   the important changes of mind and their reasons, any caveats, and the transcript
   location. Consensus is agreement, not proof of correctness.

Default limit: an initial assessment, up to three comparison rounds, and one final
confirmation. Stop earlier if arguments repeat without new evidence, access is
missing, or the problem requires a user decision. Do not spend all rounds just
because they are available. Do not pressure the counterpart to concede.

Neither participant should recursively consult or delegate consultation. Peer
processes receive `CONSULT_PEER=1`; the helper refuses calls from that environment.
If you are already the counterpart, answer directly rather than invoking this skill.

## Drive the helper

Resolve `scripts/consult.py` relative to **this loaded skill**, not a hardcoded
installation directory. In the examples, replace `<skill-dir>` with that directory,
`<project>` with the working project, and `<id>` with the ID returned by `start`.
Message and summary files are UTF-8; `--message-file -` also accepts stdin.
Use files or quoted heredocs, never interpolate prose into shell command strings.

```sh
# If the original agent is Codex; use --from claude for the reverse direction.
python3 <skill-dir>/scripts/consult.py start --from codex \
  --project <project> --message-file <brief-file>

python3 <skill-dir>/scripts/consult.py status <id>
python3 <skill-dir>/scripts/consult.py read <id>

python3 <skill-dir>/scripts/consult.py reply <id> \
  --message-file <comparison-file>

python3 <skill-dir>/scripts/consult.py reply <id> --phase confirm \
  --message-file <exact-final-proposal-file>

python3 <skill-dir>/scripts/consult.py close <id> --outcome consensus \
  --summary-file <agreed-recommendation-file>
python3 <skill-dir>/scripts/consult.py read <id> --all
```

`start` and `reply` return immediately. They launch a detached worker and print JSON
with an ID, status, and state directory. Poll `status` at reasonable intervals
(e.g. 10 seconds), keep the user informed during longer work, and call `read` when
status is `ready`. A successful launch is not a completed consultation.

All public commands print JSON, except `--skill`, which prints these instructions.
Exit codes: 0 = command succeeded (possibly still running), 1 = operational failure
or failed peer turn, 2 = invalid command-line usage. Inspect `status`, not just the
exit code. Peer stdout/stderr and worker errors are retained for diagnosis; do not
paste raw logs into a public report without reviewing them.

`start` accepts `--rounds N`, `--timeout SECONDS` (per turn; default 600), and
`--model NAME` (the **counterpart's** model). Without a model override, its CLI
default applies with the restricted configuration; it need not match the model
in another interactive session. Specify an override only when requested or needed
for the user's stated constraints. There is no cross-provider dollar-budget cap.

To stop: `close <id> --outcome cancelled`. It returns `closing` while the worker
terminates the peer process group; check `status` until `closed`. For completed
work without agreement, use `--outcome unresolved --summary-file <file>`.

Revisit a successfully closed discussion with `reply <id> --reopen --message-file
<file>`. This retains the peer session and starts a new bounded cycle. Use reopening
for a new user request or genuinely new evidence, not to evade the round limit.
Failed/interrupted turns cannot be blindly resumed: provider-side completion may
be ambiguous. Close them, report the problem, and only start a fresh consultation
when appropriate. There are no automatic retries or permission escalation.

## Local state and privacy

State defaults to `~/.local/state/agent-consult/`; override it with
`CONSULT_STATE_DIR` or global `--state-dir <directory>` **before** the subcommand.
Keep this directory outside the consulted project. In restricted environments,
use an allowed private state directory and pass it consistently on later calls.
Each consultation has its own directory and lock; competing replies cannot run
against the same peer session at once. Different consultations can run concurrently.

State includes the project path, selected messages, peer session ID, answers,
diagnostic logs, and recorded outcome. New consultation directories are private
to the current user. Keep message drafts outside the public repository too.
Native CLI session histories may also retain this material; deleting helper state
does not delete those histories. Do not commit transcripts or authentication data.

## Validation

```sh
python3 -m unittest discover -s <skill-dir>/tests -v
```

The tests use fake CLIs and make no model calls. After adapter changes, also run
a small real consultation in each direction: initial assessment, a follow-up that
depends on initial context, and explicit confirmation of the exact final proposal.
Verify inspection succeeds, mutation is denied, and the session ID stays constant.
Record failures honestly; fixture tests alone do not prove live compatibility.
