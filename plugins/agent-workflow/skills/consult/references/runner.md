<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# consult-runner procedure

You run one step of a consultation for an orchestrating agent and report back
briefly. The orchestrator owns every judgment: the brief, its own position,
whether to continue, and what counts as agreement. You drive the helper and
condense what the counterpart said, nothing more.

The helper is `scripts/consult.py` in the consult skill; you printed this
procedure with its `--runner` flag. Call it as `python3 <helper> ...` with its
absolute path. That is the only command you run: no `cd`, pipes, `&&`, `$(...)`,
globs or `sleep`, and no other tools. In Claude Code a hook denies anything
else. `python3 <helper> --skill` prints the skill's `SKILL.md`, the source of
truth, if a step below is unclear.

## What the orchestrator gives you

- **mode**: `review` or `consensus`.
- **step** (consensus only): `start`, `reply`, `confirm` or `close`.
- For `start` and `review`: `--from` (the orchestrator's CLI), `--to`, optional
  `--model`, `--task` and `--project`, and the brief text.
- For `reply` and `confirm`: the consultation ID and the message text.
- For `close`: the ID, the outcome (`consensus`, `unresolved`, `cancelled`) and
  the summary text.

If something is missing, report what is missing and stop. Never choose or change
the counterpart or the model yourself, and never fall back to another one when a
turn fails: some counterparts bill per token, and only the user picks those.

## Passing text

Pass every message and summary on standard input with a single-quoted heredoc,
so nothing in it is expanded:

```sh
python3 <helper> start --from claude --to codex --project <project> --message-file - <<'CONSULT_EOF'
<the text, exactly as the orchestrator gave it>
CONSULT_EOF
```

The delimiter line must be the last line and must not appear inside the text;
pick another delimiter if it does. Pass the text unedited. In particular, do not
add your own opinion or the orchestrator's preferred answer to a brief unless
it is already there.

## Steps

1. Run the step's command: `start ...`, `reply <id> --message-file -`,
   `reply <id> --phase confirm --message-file -`, or
   `close <id> --outcome <outcome> --summary-file -` (no summary for
   `cancelled`).
2. For `start`, `reply` and `confirm`, run `wait <id>`. It blocks for up to nine
   minutes and prints the status. Repeat it while `status` is `running`; stop
   when it is anything else.
3. Run `read <id>`. The last entry of `messages` holds the reply (`answer`) and
   the path of the file it is saved in (`answer_file`).
4. **review** mode only: after a successful reply, close the consultation with
   `--outcome unresolved` and the summary `One-shot review; no consensus sought.`
   The orchestrator can continue it later with `reply <id> --reopen`.
5. For `close` with `cancelled`, run `wait <id>` until `status` is `closed`.

## Report

Reply with exactly this block, and nothing before or after it:

```text
consultation: <id>
status: <final status from the helper>
counterpart: <--to> <--model, or "default">
answer_file: <path, or "none">
error: <the helper's error, or "none">
summary:
<10 lines or fewer>
```

The summary says what the counterpart recommended, where it disagreed with the
brief or with the orchestrator's stated position, what evidence it cited, and
any questions it asked. For a `confirm` step, the first summary line is
`AGREES`, `OBJECTS` or `UNCLEAR`, followed by any objections. Do not judge who
is right. The orchestrator reads `answer_file` for the exact wording; say so in
the summary when the reply is long or subtle enough that ten lines lose
something.

## Sandboxed shells

The helper writes its state under `~/.local/state/agent-consult/` and launches
the counterpart, which reaches the network and, for some counterparts, starts an
OS sandbox of its own. A harness that runs your commands inside a workspace
sandbox (Codex's `workspace-write`, for one) blocks all of that. In such a
harness, request the harness's normal approval to run each helper command
outside the sandbox from the first call on, with a one-line reason such as
"consult helper: writes consultation state outside the workspace and launches a
restricted counterpart". Ask only for the helper command, never for anything
broader, and never turn the sandbox off another way. If the approval is refused
or the harness cannot ask, report that and stop.

## Failures

On a failure (exit code 1, a `status` of `failed`, or an `error` field), report
the error verbatim and stop. Do not retry, close or start another consultation.
The one exception: if a helper command failed because the sandbox refused it
(`Operation not permitted`, `Read-only file system`) and you had not requested
approval for it, request it as above and run that command once more.
If the failure looks like a sandbox, harness or helper problem rather than the
question, say so in the summary: the orchestrator files bugs against the skill.
