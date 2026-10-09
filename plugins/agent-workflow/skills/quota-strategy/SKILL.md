---
name: quota-strategy
description: Stretch Claude or Codex subscription allowances across long unattended runs by reading available usage pools, reserving capacity for the orchestrator, and routing implementation to a cheaper model or the other provider. Works with either orchestrator and with one or both providers configured. Use when the user mentions quota, usage limits, "stretch my quota", running overnight, or choosing which model or agent should implement a unit of work.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Quota strategy

Long agent runs can burn through a weekly limit while no one is watching it. This skill reads the
usage figures at each work boundary, such as between milestones, and decides who implements the
next unit.

**Terms.**
- *Orchestrator*: the session that plans, verifies and lands work.
- *Implementer*: the subagent or other agent CLI that does one unit of work.
- *Pool*: one usage limit that runs out on its own schedule.
- *Scoped limit*: an extra weekly cap Anthropic applies to one model. It is a cap, not extra
  capacity: that model's usage counts toward its scoped limit **and** toward the general weekly
  limit and the 5-hour window. Which models have one depends on the plan and changes over time;
  the script reports whatever the account has. Example: on Max, Fable models may use up to 50% of
  the weekly limit, and they use it up faster than other models.
- *Usage credits*: pay-as-you-go spending at API rates that both Claude and Codex plans can turn
  on. With credits on, reaching a limit does not stop work; it starts billing.
- *Home provider*: the provider running the orchestrator, Claude or Codex. An external
  implementer on that same provider still consumes its allowance.

See the repository [glossary](../../../../GLOSSARY.md) for shared terms.

**Needs:** Python 3.9+ and usage access for each provider the run will use. Claude readings
need a logged-in Claude Code; Codex readings need local Codex session logs. Either provider
can be used alone. A missing provider is unavailable, not a pool with zero usage. This
subscription policy does not measure API-key billing; use a separate spending budget for it.

## Reading the pools

| Pool | What draws on it | How to read it |
|---|---|---|
| 5-hour | every Claude model | `python3 <skill-dir>/scripts/claude_usage.py [--json]` |
| General weekly | every Claude model, including those with a scoped limit | same command |
| Scoped weekly (one per model, when the plan has them) | that model, in addition to the general weekly limit | same command; `--model <name>` exits 1 if that model has no scoped limit |
| Codex weekly (and a 5-hour window, when the plan has one) | Codex local and cloud tasks, plus ChatGPT Work and other OpenAI agentic features on the same plan | `python3 <skill-dir>/scripts/codex_usage.py [--json]` |

Some models are not covered by a plan's limits at all. On Pro and on Team standard seats, Fable
bills usage credits from its first token, and no pool for it appears in the script's output.
Before routing work to a model, confirm it is in the plan's limits; if it is not, route the work
elsewhere unless the user has approved spending. OpenAI's Pro plans currently have no 5-hour
window, only a weekly one.

`claude_usage.py` makes one call to the endpoint Claude Code's `/usage` command uses
(`api.anthropic.com/api/oauth/usage`, undocumented), authenticating with Claude Code's own OAuth
token (the Keychain on macOS, `~/.claude/.credentials.json` on Linux). If that fails, it falls back <!-- portability-ok: Claude-only credential adapter. -->
to Claude Code's cache in `~/.claude.json`, which may be stale; every line says which source it
used. Exit 0 is a reading, 1 is a missing `--model` limit, 2 is no token and no cache.

The endpoint is undocumented, so a Claude Code update can break it. Report a cache-sourced or
failed reading plainly rather than guessing. The token never leaves the machine except in that
one request to Anthropic.

Prefer a current usage reading exposed by the client when available. The offline fallback,
`codex_usage.py`, reads `rate_limits` events from
`<CODEX_HOME>/sessions/YYYY/MM/DD/rollout-*.jsonl` (default home: `~/.codex`). It compares
the events' timezone-aware timestamps across all logs and calculates age from the selected
event. Later tool output, a resumed session, or copying a file cannot make old usage fresh.
Malformed lines, empty readings, and records without a usable timestamp are skipped;
exit 1 means no timestamped reading was found. It needs no token or network call.

For unattended routing, require a reading no older than 15 minutes by default and taken
after any applicable reset. Record a user override of that freshness limit. Stale,
cache-only without a known observation time, missing, or failed readings mean unknown
capacity. Refresh through the provider's usage UI or another supported usage mechanism
before assigning work to that pool; do not launch an implementation just to refresh it.
An old percentage is not a lower bound across a reset.

## Routing

At startup, record the home provider, the orchestrator model, available implementation
providers, and the selected model and effort for each implementer. At every work boundary,
read the pools those agents actually consume and include percentages, freshness, and reset
times in the progress line. Changing models within one provider does not escape its shared
allowance. Do not assume orchestration and review are negligible costs.

Apply these rules in order; a fallback never overrides an earlier exclusion:

1. **Protect the orchestrator.** If its provider's weekly usage is at least 85%, any
   applicable short window is at least 90%, or its own scoped model limit is at least 90%,
   checkpoint and start no new units, including on the other provider. Unknown home
   capacity also stops new assignments until refreshed. The orchestrator still needs room
   to verify and land work; moving implementation does not move that cost.
2. **Filter implementers.** Exclude a provider at 85% weekly usage, a provider whose short
   window is at 90%, and a model whose scoped limit is at 90%. Also exclude unknown or stale
   capacity, unavailable credentials, unapproved paid-only models, and environments that
   cannot run the unit. Apply the short-window rule to Codex too whenever its plan has one.
3. **Choose among the eligible routes:**

   | Home provider's weekly usage | Implementer |
   |---|---|
   | Under 60% | User's preferred cheaper capable model on the home provider; if unavailable, an eligible alternative. After two failed verifications, one main-model rerun is allowed if all its pools remain eligible. |
   | 60–75% | Prefer an eligible model on the other provider. Otherwise use a cheaper home-provider model. Reruns use an eligible implementer, not the main model. |
   | 75–85% | Use an eligible model on the other provider. Use a cheaper home-provider model only if the alternative is unavailable or cannot run the unit. |

4. **If nothing is eligible, checkpoint and wait or stop.** Report the blocking pool and
   its reset time when known. Re-read usage after a reset before continuing; a timestamp
   passing is not itself a new reading. Do not bounce work between two exhausted providers.

These are starting defaults: 60% begins conserving the rest of the week, 75% favors shifting
implementation, 85% preserves a weekly reserve, and 90% bounds short windows and scoped
limits. A project or user can override them; record the override with the run's decisions.
Compare each provider's actual reset time; their weeks need not align.

With **Claude as orchestrator**, Claude's weekly reserve gates the loop; Codex is an
alternative implementer. With **Codex as orchestrator**, Codex's reserve gates the loop;
Claude is the alternative. For example, Codex at 40% and Claude at 90% can continue with a
cheaper Codex implementer. Codex at 86% stops a Codex-led loop even if Claude is at 10%.
With **only one provider**, omit the unavailable route and apply the same reserve to the
remaining provider. Never require Claude authentication merely to run a Codex-only loop.

The orchestrator stays on its model. Launch same-provider subagents using the model,
fresh-context, and verification guidance in
[run-delegate](../run-delegate/SKILL.md#launching-a-runner), with an implementation brief
rather than its command-only brief. Choose effort for the unit: `low` command-runner
examples are not a milestone default. If that skill is unavailable, inspect the current
tool schema and set the model and supported effort explicitly; do not assume inheritance
is cheaper. The orchestrator launches any other provider's CLI itself; the implementer's
brief never launches another agent CLI.

For a **Claude implementer launched by Codex**, run the following from the worktree using
the shell tool's working-directory setting. Replace both placeholders with the selected,
available model and its supported effort before launch:

```bash
claude --print --model <implementer-model> --effort <supported-effort> \
  < <run-dir>/brief.md > <run-dir>/claude.log 2>&1
```

Keep existing permission controls. If a headless run cannot obtain a required approval,
return the blocked action to the orchestrator. Check effective model and effort in the
client's session metadata where exposed; if unavailable, label them unverified. Use the
same complete implementation brief and independent review required below.

## Running Codex as an implementer

Before launch, select an available model explicitly using the client's model catalog
(`codex debug models` in CLI versions that expose it). A narrow implementation can use
`gpt-6-luna` with `medium` effort; demanding milestones may need a stronger available model.
Honor the user's preference and check supported effort levels. Replace the model and
effort placeholders below with those exact choices; never rely on the CLI's default model.

This extends the workspace recipe verified with codex-cli 0.157.0; model and effort flags
were rechecked with 0.162.1 on 2026-10-09. Run in the background:

```bash
codex exec -C <worktree> -s workspace-write --model <implementer-model> \
  --add-dir <main-checkout>/.git --add-dir <cargo-home> --add-dir <other caches the unit writes> \
  --add-dir <run-dir> \
  -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort=<supported-effort> \
  -o <run-dir>/last-message.md - < <run-dir>/brief.md > <run-dir>/codex.log 2>&1
```

- **Write access.** A git worktree's metadata lives in the main checkout's `.git/worktrees/`,
  outside `-C`. Without `--add-dir <main-checkout>/.git`, Codex cannot commit. Build tools that
  lock or fill a shared cache (cargo's home, a package or download cache) need their directories
  too. `/tmp` is writable by default.
- **Hardware and virtualization.** `/dev/kvm` was unavailable in one Linux
  `workspace-write` setup with codex-cli 0.157.0. Probe the actual environment before
  assigning a unit that needs it; neither "Codex" nor "Claude" establishes device access.
  Route to an eligible environment that passes the probe, or report the blocker.
- **Network.** Network access is off by default in `workspace-write`. Loopback-only tests and
  fetches need `network_access=true`.
- **Model and effort.** Pass both explicitly. Read the log header's `model:`, `sandbox:`,
  and `reasoning effort:` immediately after launch and compare them with the chosen values.
  On a mismatch, stop and investigate before spending on the unit. If the client does not
  expose effective settings, mark them unverified rather than asserting savings.
- **The brief.** Codex does not have the orchestrator's skills. Give it file paths to read (the
  plan, the process skill's `SKILL.md`), every rule it must follow (commit author, trailer, no
  push), and "stop before review". Then review its branch with a separate, read-only Codex session
  (for example through the `consult` skill), so a Codex unit spends no Claude quota on review.
  Resume with `codex exec resume --model <implementer-model> <session-id>` for fixes,
  preserving the same explicit effort. `resume` takes
  no `-s` or `--add-dir` flags, so pass the sandbox as config keys:
  `-c sandbox_mode='"workspace-write"'`, `-c 'sandbox_workspace_write.writable_roots=[...]'`,
  the same `network_access` and effort keys, and run it from the worktree. Then check the log
  header again.
- **Permission.** A harness's auto-approval mode may refuse the launch as creating an unsafe
  agent. The fix is an allow rule the **user** adds (in Claude Code, `Bash(codex exec:*)`). An
  agent editing its own permission settings is refused, and must not try.
- **Content refusals.** Codex's provider may refuse a brief as a possible cybersecurity risk
  (observed for a fuzzing milestone). The run then exits nonzero, having done nothing, and with no
  last-message file. Check the log's last lines. Do not reword the brief to get past the filter;
  route the unit to the next pool instead. Plan for this with security-adjacent units such as
  fuzzing, exploit reproduction or protocol hardening.
- **Stopping a run.** Stop it through the harness's background-task control, or by its PID. A
  `pkill -f '<pattern>'` whose pattern appears in the calling shell's own command line kills that
  shell too.

## When the user is away

No one checks usage overnight, so apply the same reserve and freshness rules at every
boundary. If an implementer hits a usage limit, keep its checkpoint and re-evaluate all
eligible routes, including the orchestrator's capacity, before assigning the remainder.
If a reading fails or comes only from an undated cache, report unknown capacity and stop
using that pool until refreshed. Do not keep routing on the last good percentage forever.

A limit does not always stop work. With usage credits on, a Claude model past its weekly limit
or its scoped cap keeps running at API rates. Codex finishes the turn that crosses its limit, and
it can run on purchased credits. Either way the run spends money instead of failing, and nothing
in the log shows a failure. Before an unattended run, ask the user whether credits are on and
whether the run may spend them. If the answer is no, the stop thresholds above are the only
thing preventing billing, so do not raise them.

## Sources

Checked against the providers' documentation on 2026-10-08. Plans change; re-check these before
retuning anything:

- Anthropic, [What is the Max plan?](https://support.claude.com/en/articles/11049741-what-is-the-max-plan):
  the 5-hour session limit, and a weekly limit "that applies across all models."
- Anthropic, [Claude Fable models on your plan](https://support.claude.com/en/articles/15424964-claude-fable-models-on-your-plan):
  Fable "draw[s] from your plan's regular weekly usage limits", is capped at 50% on Max and
  premium seats, and on Pro and standard seats bills only usage credits.
- OpenAI, [Codex pricing](https://learn.chatgpt.com/docs/pricing): the allowance is shared with
  ChatGPT Work, Pro has no 5-hour limit, a turn that crosses the limit may finish, and Plus and Pro can
  buy credits to continue.
  OpenAI's help article on GPT-6 Astra usage returned HTTP 403 to automated fetches and was not
  read.
