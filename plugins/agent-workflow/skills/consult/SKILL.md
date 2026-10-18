---
name: consult
description: >-
  Collaborate with another coding agent on a question or proposed approach:
  any of Claude Code, Codex, Antigravity (agy) and Muse consults another, or a
  different model in its own CLI (Opus consulting Fable), through a persistent
  peer session. Use when the user says "consult with <name>", where the name is
  an agent (Codex, Claude, agy, Muse), a vendor or model family (Gemini, GPT), or
  a model (Fable, Opus, Sonnet, Argon); also "consult your counterpart", "compare
  perspectives", or "work toward consensus". The original agent leads the
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
- The counterpart's CLI on `PATH`, already authenticated: `claude`, `codex`,
  `agy` or `muse`. Normal CLI usage charges/limits apply; see "Metered
  counterparts" below before choosing one billed per token. The counterpart can be the same
  CLI as the original agent when `--model` names a different model (see
  "Another model in the same CLI" below).
- For an `agy` or `muse` counterpart: bubblewrap (`bwrap`) on Linux, or
  `sandbox-exec` on macOS, and no MCP servers or plugins configured in that CLI
  (see below).
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
| agy | Runs inside an OS sandbox whose filesystem is read-only except agy's own state directory (`~/.gemini/antigravity-cli`) and a private temp directory; never `--dangerously-skip-permissions`; `--sandbox` (terminal restrictions); slash commands and skills disabled; refused if any MCP server or plugin is configured |
| Muse | The same OS sandbox, writable only for Muse's state and sign-in (`~/.local/share/muse`, `~/.config/muse`) and a private temp directory; `--disable-write`, `--disable-shell`, web tools off, hooks and plugins off; the workspace is left untrusted and other agents' personal rules and skills are excluded; refused if any plugin or MCP server is configured |

These controls are deliberately different. Claude and Muse cannot run shell
commands; Codex can run commands within its read-only sandbox. agy has a shell
tool but cannot use it: a headless run has nobody to approve a command, and one
denied command ends the turn with an empty answer (agy 1.4.0, 2026-10-16, issue
#117). So each agy prompt tells it to inspect with its file tools (`view_file`,
`list_dir`, `grep_search`, `find_by_name`) and to ask you for any command's
output. If it tries a command anyway, the turn fails with "agy stopped on a
denied action (RunCommand)": close the consultation, run the command yourself,
and start a fresh one with the output in the brief. Do not approve commands by
adding rules to agy's configuration; that changes the user's agent setup.

On macOS, exit status 71 with `sandbox-exec: sandbox_apply: Operation not
permitted` means the host blocked the peer sandbox from starting. The helper
reports this separately from a denied tool action. Close the failed consultation
and start a fresh one through the host's normal approval mechanism, keeping the
peer sandbox enabled. The helper does not retry or request approval itself.

Muse's shell is off because its own shell sandbox is also bubblewrap, which
cannot start inside the outer one ("No permissions to create a new namespace",
Muse Code 1.4.9, 2026-10-16). Skills installed for Muse itself stay loaded: it
has no per-run switch for them, and `--preset` and `-c` keys did not change the
count. Muse also loads Claude Code's and Codex's personal rules and skills by
default ("foreign personal context"); `--no-foreign-personal-context` keeps them
out, because the brief, not the other agent's configuration, is the context.

agy is enforced from outside because it has no read-only flag. In a live check
(agy 1.2.11, 2026-09-26), `--mode plan` wrote a file into the project with
default settings, no approval and no `--dangerously-skip-permissions`, so plan
mode is never used. Without it, agy's own headless check denied the same write,
but the adapter does not rely on that: bubblewrap mounts `/` read-only, and a
write fails with "Read-only file system". agy has no flag to turn off
configured MCP servers or plugins for one run, and the filesystem sandbox cannot
stop what they do over the network. So `start` refuses unless `agy mcp list`
and `agy plugin list` both report none. If evidence needs a test or
an unavailable tool, gather it in the original session under existing permissions
and share the result. CLI-owned authentication/session writes still occur. This
is not an isolation boundary for hostile projects or compromised CLIs.

Adapter flags were checked against Claude Code 2.1.277 and Codex CLI 0.155.0 on
2026-09-18, and against agy 1.2.11 on Linux on 2026-09-26: a three-turn live
consultation, with the context kept and the write denied. On macOS it was
checked against agy 1.4.0 with `gemini-4-argon` on 2026-10-16: a three-turn
consultation (brief, a context-dependent follow-up, a confirm) on one session,
and a separate write attempt that agy refused with no file created; running
the adapter's `sandbox-exec` profile directly made `touch` fail with
`Operation not permitted`, so the OS layer holds on its own too. The Muse adapter was
checked against Muse Code 1.4.9 on Linux on 2026-10-16: a two-turn live
consultation through the helper, the session and its context kept, and a write
refused with no file created. Older releases may reject flags. Fail visibly rather than removing
restrictions to make a command work. Ground truth: `claude --help`, `codex exec
--help`, and `codex exec resume --help`. See the official
[Claude programmatic guide](https://code.claude.com/docs/en/headless) and
[Codex noninteractive guide](https://developers.openai.com/codex/noninteractive).

## Choose the counterpart from the user's words

Users name the counterpart the way they think of it: "consult with Codex",
"consult with Fable", "consult with Gemini". Turn the name into `--to` and
`--model` before starting:

| The user names | `--to` | `--model` |
| --- | --- | --- |
| An agent or its CLI: Claude, Codex, agy or Antigravity, Muse | that CLI | none: its default |
| A model family another CLI serves: Gemini (agy), GPT (Codex), Muse models (Muse) | that CLI | the model, if a specific one is named |
| A model your own CLI serves, such as Fable, Opus or Sonnet from Claude Code | your own CLI | that name |
| A name you don't recognize, such as Astra | the CLI that lists it | its exact ID from that list |

For a name you don't recognize, look it up in every CLI's catalog:

| CLI | Command | What to match |
| --- | --- | --- |
| Codex | `codex debug models` (JSON) | each model's `slug` and `display_name`; skip `"visibility": "hide"` |
| agy | `agy models` | the ID in the first column and the name after it |
| Claude Code | `claude --help`, under `--model` | the aliases (`fable`, `opus`, `sonnet`) or a full ID |
| Muse | no catalog command; `muse model-profile show <id>` resolves a guess, and each run logs the model it used as `model_id` in its `run.model.configured` event | the ID |

agy lists each model once per effort level (`gemini-4-argon-high`,
`gemini-4-argon-medium`, …). The helper passes effort separately, so pass the
bare ID with the suffix dropped (`gemini-4-argon`): agy accepted bare
`gemini-3.8-flash` alongside `--effort` on 2026-10-16. If a bare ID is ever
refused, use the `-high` entry for `--task thinking`. A Muse plan name is not a model ID: Muse refused
`muse-wonder` while the plan's default model was `muse-wonder-1.0`, so leave
`--model` off for Muse unless the user names an ID that `muse model-profile
show` resolves.

Users say the short name, not the ID, so match it case-insensitively as a whole
word inside the ID or name, not as the entire string. "Astra" matches Codex's
`gpt-6-astra` (display name "GPT-6-Astra"); an exact-string search misses it.
Pass the matched ID, never the user's word, to `--model`.

If exactly one model in one CLI matches, use it. If none match, or several do
(for example two model generations sharing a name), ask the user in one line,
listing the candidates and what you checked. Don't guess a model name: a wrong
one fails the first turn, after the brief has already been sent. If the name is
the model you are running now, say so and ask for another: consulting yourself
only gets you an echo.

Tell the user which CLI and model you picked in the same message that starts
the consultation.

### Metered counterparts

Some counterparts bill per token rather than from a plan's allowance: a Gemini
model that agy reaches through a cloud project, an API key, usage credits past a
plan's limit. Which ones are metered on this machine is the user's fact, not
this skill's: read it from the user's instruction file (`AGENTS.md` /
`CLAUDE.md`), and if it says nothing, assume a CLI the user has not described is
metered.

- **A metered model runs only when the user named it for this consultation**
  ("consult with Gemini", "ask Argon"). Never pick one yourself, as a fallback
  when another CLI is unavailable, or for a skill that consults on its own
  initiative. A monthly spend cap limits the damage; it does not make the spend
  approved.
- **A plan-limited counterpart** (a subscription with its own usage limits) is
  like any other: no extra question.
- Say in the start message which model ran and that it is metered. To see what
  a consultation consumed afterward, `quota-strategy`'s `agent_usage.py` sums
  per-model token counts from Codex, agy and Muse logs.

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
   Only one confirm turn is allowed per cycle; a second `reply --phase confirm`
   fails with "Confirmation already requested; close this cycle before reopening".
   So apply every wording change the counterpart has asked for before sending the
   confirm. If the confirm reply asks for any change, even exact replacement
   wording, close the cycle and `reply --reopen` with the revised text for one
   confirm turn. `close --outcome consensus` only checks that the last turn was a
   successful confirm, not what it agreed to, so this is on you.
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

## Run it through the consult-runner agent

Never launch a counterpart CLI yourself (`agy -p`, `codex exec`, `claude -p`,
`muse exec`): without the helper's flags and sandbox, a headless peer can write
files or stall on permission prompts. Use the helper, preferably through the
`consult-runner` agent that ships with this skill. It drives the helper and
returns a short report, so polls and long replies stay out of your context, and
several reviews can run in parallel, one runner each.

Give it a mode and the exact text to send:

- **`mode=review`**: one brief, one reply. Pass `--from`, `--to`, optional
  `--model`, `--task`, the project and the brief. It closes the consultation as
  `unresolved` ("one-shot review"); continue later with `reply <id> --reopen`.
- **`mode=consensus`**: one step per call, `step=start`, `reply`, `confirm` or
  `close`, with the consultation ID after `start`. Every judgment in "Conduct
  the discussion" stays with you between calls.

It reports the consultation ID, status, counterpart, `answer_file` (the verbatim
reply), any error, and a summary of 10 lines or fewer. A confirm step's summary
starts with `AGREES`, `OBJECTS` or `UNCLEAR`. Read `answer_file` yourself before
closing a confirm as consensus, or whenever the summary says detail was lost.
The runner never picks a counterpart or model, and never retries a failure. The
metered-counterpart rule above is still yours to apply.

Its procedure is `references/runner.md` (`consult.py --runner` prints it).

| Harness | Agent | Confinement |
| --- | --- | --- |
| Claude Code | `consult-runner` (as `agent-workflow:consult-runner` from the plugin), model `sonnet` | Bash only. A hook in the plugin manifest (`scripts/runner_guard.py`) denies the runner every command except `python3 <skill-dir>/scripts/consult.py ...`, with text passed in a single-quoted heredoc |
| Codex | `agents/codex/consult-runner.toml`, model `gpt-6.1-sol` at low effort | Instructions only. A Codex custom agent inherits the parent's sandbox and approvals, and Codex's pre-tool-use hook input does not say which agent made the call (Codex docs, 2026-10-17) |

Claude Code loads the agent and hook from the `agent-workflow` or `everything`
plugin, not from a skill directory installed on its own. A subagent inherits the
parent's permission mode, so in the default mode each helper call asks for
approval. To approve them once, add an allow rule for the helper's real path
(`/permissions`, or `permissions.allow` in settings):
`Bash(python3 <skill-dir>/scripts/consult.py *)`. The hook still applies.

For Codex, copy the role into your personal agents (Codex reads
`~/.codex/agents/` and a project's `.codex/agents/`). Copy it rather than linking
it: Codex 0.163.0 lists a symlinked agent file but refuses to spawn it ("agent
type is currently not available"). Copy it again after updating the skill.

```sh
mkdir -p ~/.codex/agents
cp <skill-dir>/agents/codex/consult-runner.toml ~/.codex/agents/consult-runner.toml
```

The helper writes its state under `~/.local/state/agent-consult/` and starts the
counterpart in its own sandbox. Neither works inside Codex's `workspace-write`
sandbox on macOS, so the runner's helper calls need Codex's normal approval to
run outside it. A headless `codex exec` cannot give that approval, and the
runner then reports the failure and stops.

Checked live on 2026-10-17 with Claude Code and the plugin loaded from a
checkout: the runner's `ls -la` was denied by the hook, and a review by Codex
returned through the runner with its report. The Codex role was checked the
same day with Codex 0.163.0 in headless `codex exec` under `workspace-write`:
it spawned, ran the helper, and reported the sandbox's refusal to create the
state directory as a harness problem without working around it. A full Codex
review through it was not run, because that needs an approval only an
interactive session can give.

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

# Any direction can name the counterpart; --to is required from agy.
python3 <skill-dir>/scripts/consult.py start --from claude --to agy \
  --project <project> --message-file <brief-file>

# A different model in the same CLI: --model is required when --to matches --from.
python3 <skill-dir>/scripts/consult.py start --from claude --to claude \
  --model fable --project <project> --message-file <brief-file>

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

Poll the top-level `status` field by parsing the JSON, never by grepping the output
for "ready": `status` and `read` also list every job with its own status, so after
the first turn a grep matches an earlier job and reports a still-running reply as
done.

`wait` does the polling for you: it blocks while the status is `running` or
`closing`, up to `--timeout` seconds (default 540, under the 10-minute limit some
hosts put on one shell call), then prints the same JSON as `status`. Run it
again if the status is still active.

```sh
python3 <skill-dir>/scripts/consult.py wait <id>
```

`read` gives each reply's `answer_file`, the file holding it verbatim.

All public commands print JSON, except `--skill`, which prints these instructions,
and `--runner`, which prints the consult-runner procedure.
Exit codes: 0 = command succeeded (possibly still running), 1 = operational failure
or failed peer turn, 2 = invalid command-line usage. Inspect `status`, not just the
exit code. Peer stdout/stderr and worker errors are retained for diagnosis; do not
paste raw logs into a public report without reviewing them.

`start` accepts `--to claude|codex|agy|muse` (the counterpart; defaults to Codex from
Claude and to Claude from Codex; it may match `--from` when `--model` is given), `--task thinking|coding`, `--rounds N`, `--timeout SECONDS` (per
turn; default 600), and `--model NAME` (the **counterpart's** model).

`--task` sets the counterpart's reasoning effort on every turn, resume included.
The default is `thinking`: design, architecture, review, debugging analysis,
and any other judgment call run at **high** effort, whichever direction the
consultation goes (Codex, or Claude such as Opus 5.5). Pass `--task coding`
only when the counterpart's job is to draft or check code mechanically; it runs
at **medium**. When a consultation mixes the two, use `thinking`. The adapters
pass `--effort <level>` to `claude` and `agy`, `--reasoning-effort <level>` to
`muse`, and `-c model_reasoning_effort=<level>` to `codex`. All of them accept `high` and `medium` (checked 2026-09-26: `claude --help`
lists `low, medium, high, xhigh, max`; `agy --help` lists `low|medium|high|max`;
`muse exec --help` lists `none|minimal|low|medium|high|xhigh|max|ultra`;
the Codex API's list of valid values is `none, minimal, low, medium, high,
xhigh, max`). Not `max`: a model can lack it even when the CLI lists it, and
agy 1.4.0 refused `gemini-4-argon --effort max` ("has no \"max\" effort
(available: low, medium, high)", 2026-10-16). A Gemini model under agy follows the same rule; name it with
`--model` when a specific one is wanted (`agy models` lists them). Without a model override, its CLI
default applies with the restricted configuration; it need not match the model
in another interactive session. Specify an override only when requested or needed
for the user's stated constraints. There is no cross-provider dollar-budget cap.

### Another model in the same CLI

Pass `--to` equal to `--from` and name the counterpart's model with `--model`,
for example Claude Code on Opus consulting `--model fable`. The model name is
whatever the counterpart CLI's `--model` flag accepts: an alias such as `fable`,
`sonnet` or `opus`, or a full model ID. The helper refuses a same-CLI start
without `--model`, because the CLI's default is most likely the model already
running, which would be an echo, not a second opinion. It cannot see which model
the original agent is running, so choose one that differs from your own. The
counterpart gets the same restrictions as any other peer from that CLI.

A `claude` started from inside Claude Code inherits the parent's session and
appends its turns to the parent's transcript unless told otherwise (Claude Code
2.1.42, 2026-09-26). The helper therefore starts every Claude peer with its own
`--session-id` and fails the turn if the peer reports any other session. Checked
live the same day: Claude on Opus consulting `--model sonnet`, two turns,
context kept, a write attempt denied, and the parent transcript unchanged.

Two models in one CLI share its system prompt, tools and habits, and often
training lineage, so their agreement is weaker evidence than agreement across
vendors. Prefer a different CLI when one is available and the question is
contested; use a different model in the same CLI when only one CLI is signed in,
or when the user asks for that model by name. Say which it was when reporting.

To stop: `close <id> --outcome cancelled`. It returns `closing` while the worker
terminates the peer process group; check `status` until `closed`. For completed
work without agreement, use `--outcome unresolved --summary-file <file>`.

Revisit a successfully closed discussion with `reply <id> --reopen --message-file
<file>`. This retains the peer session and starts a new bounded cycle. Use reopening
for a new user request or genuinely new evidence, not to evade the round limit.
Failed/interrupted turns cannot be blindly resumed: provider-side completion may
be ambiguous. Close them, report the problem, and only start a fresh consultation
when appropriate. There are no automatic retries or permission escalation. If the
failure came from the skill or a counterpart's harness rather than the question,
also file a bug (next section).

## File bugs against this skill

When a consultation fails for a reason that is not the question itself, file an
issue at <https://github.com/curtisgalloway/public-skills/issues> so the adapter
gets fixed instead of worked around in the next session. That includes:

- the counterpart failing because of a sandbox or harness problem: a write or
  read denied that should have been allowed, a headless permission prompt that
  stops the turn, `bwrap` or `sandbox-exec` refusing to start, a nested sandbox
  that cannot create a namespace;
- a CLI rejecting a flag or model the adapter passes, or a release changing its
  output so the helper misreads it;
- the helper itself misbehaving: a wrong `status`, a lost session ID, a lock
  that is never released, a crash or traceback;
- instructions in this file that turned out to be wrong or missing.

Not a bug in this skill: the provider is down, the user's CLI is signed out, or a
restriction worked as documented (Claude and Muse have no shell by design).

1. **Check for an existing report:** `gh issue list --repo
   curtisgalloway/public-skills --state all --search "consult <keyword>"`. If one
   matches, add a comment with the new evidence instead of a new issue.
2. **Write the report.** Title it `consult: <what failed>`. Include the
   direction (`--from`/`--to`, `--model`), the CLI versions (`<cli> --version`),
   the OS, the exact command, the `status` JSON, the relevant lines of the
   retained peer log, and what you expected. Say whether you reproduced it.
3. **Scrub it.** The repository is public. Remove hostnames, IP addresses,
   usernames, home-directory paths (write `~`), project names and file contents
   from the user's work, and anything from the brief. Keep only the lines that
   show the failure.
4. **Show the user the title and body, then file it** with `gh issue create
   --repo curtisgalloway/public-skills --label bug`, unless the user has already
   said to file without asking. Give them the issue URL.

If `gh` is missing or not signed in, give the user the drafted issue to file
instead of dropping it.

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
For agy and Muse, also ask the counterpart to write a file in the project, and
confirm that no file appears.
Record failures honestly; fixture tests alone do not prove live compatibility.

The issue #117 fix was checked live on macOS with agy 1.4.0 and
`gemini-4-argon`: `view_file` inspection succeeded, a follow-up retained the
file's values without rereading, and a final confirmation kept the same session.
A separate write request was refused by the model before any write-tool call;
no file appeared. Independently, `touch` under the adapter's OS sandbox failed
with `Operation not permitted` and created no file.
