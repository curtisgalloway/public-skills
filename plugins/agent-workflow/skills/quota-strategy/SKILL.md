---
name: quota-strategy
description: Stretch a Claude subscription's usage limits across long unattended runs (milestone loops, overnight orchestration) by reading live usage for each pool — the 5-hour window, the general weekly limit, any per-model weekly cap (which also counts toward the general limit), and Codex's limit — and routing work to a cheaper model, Codex, or the main model by threshold. Use when the user mentions quota, usage limits, "stretch my quota", running overnight, or choosing which model or agent should implement a unit of work.
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

**Needs:** Python 3.9+, a logged-in Claude Code on the same machine, and, for the Codex pool, the
Codex CLI.

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
token (the Keychain on macOS, `~/.claude/.credentials.json` on Linux). If that fails, it falls back
to Claude Code's cache in `~/.claude.json`, which may be stale; every line says which source it
used. Exit 0 is a reading, 1 is a missing `--model` limit, 2 is no token and no cache.

The endpoint is undocumented, so a Claude Code update can break it. Report a cache-sourced or
failed reading plainly rather than guessing. The token never leaves the machine except in that
one request to Anthropic.

`codex_usage.py` reads the newest `rate_limits` record from Codex's own session logs
(`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`). Codex writes one with every response, so the
script needs no token and makes no network call. The record is only as fresh as the last Codex
run, and the output gives its age. Treat a reading hours old as a lower bound, and let the first
Codex unit of a run refresh it. Exit 1 means no record was found (Codex has not run here).

## Routing

Read every pool at every boundary and put the numbers in the progress line. The table below uses
a cheaper Claude model as the default implementer: "cheap model" means whichever model the user
prefers for implementation. Moving work to a model with its own scoped limit does not move it off
the general weekly limit; it still draws on that limit. The only routes that spare the general
weekly limit are a model that uses less of it per unit of work, and Codex.

| Condition | Implementer |
|---|---|
| General weekly under 60% | cheap model; one rerun on the main model is allowed when a unit fails verification twice |
| General weekly 60–75% | Codex for units its sandbox can run (no KVM, emulator or VM); cheap model for the rest; reruns go to Codex, not the main model |
| General weekly 75–85% | Codex for every unit its sandbox can run; cheap model only where it cannot |
| General weekly 85% or more | stop the loop; start nothing new |
| Cheap model's scoped weekly 90% or more | route its share to Codex |
| 5-hour 90% or more | pause until its `resets_at`, then continue |
| Codex weekly 85% or more | stop sending units to Codex; they return to the cheap model, or wait for a reset |

These are starting defaults. Why each one sits where it does, so they can be retuned:

- **60%** is where the run starts protecting the rest of the week. Below it, main-model reruns are
  affordable and keep quality up.
- **75%** leaves room for interactive work the user will do before the reset. Raise it when the
  run is the only thing that week; lower it on a busy week.
- **85% stop** keeps a reserve for the orchestrator to finish verifying and landing work, and for
  the user. A run that hits 100% overnight leaves nothing for the morning.
- **90% on a scoped or 5-hour limit** is late on purpose. The 5-hour window refills within hours.
  A scoped limit only caps one model; the general weekly rows above already protect the shared
  limit underneath it, so running the scoped cap close to empty costs little.

A project or the user may override any threshold. Record the override where the run's other
decisions live.

Check each pool's `resets_at`. Codex's week usually does not reset when Claude's does, which makes
it the natural overflow late in the Claude week.

The orchestrator stays on its own model throughout. Its cost is small next to an implementer's,
and it is the part that verifies the work. The orchestrator launches Codex itself; a subagent's
brief never does.

## Running Codex as an implementer

A launch that worked with codex-cli 0.157.0, run in the background:

```bash
codex exec -C <worktree> -s workspace-write \
  --add-dir <main-checkout>/.git --add-dir <cargo-home> --add-dir <other caches the unit writes> \
  --add-dir <run-dir> \
  -c sandbox_workspace_write.network_access=true \
  -c model_reasoning_effort=high \
  -o <run-dir>/last-message.md - < <run-dir>/brief.md > <run-dir>/codex.log 2>&1
```

- **Write access.** A git worktree's metadata lives in the main checkout's `.git/worktrees/`,
  outside `-C`. Without `--add-dir <main-checkout>/.git`, Codex cannot commit. Build tools that
  lock or fill a shared cache (cargo's home, a package or download cache) need their directories
  too. `/tmp` is writable by default.
- **No KVM.** On Linux, `/dev/kvm` does not exist inside the `workspace-write` sandbox (observed
  with codex-cli 0.157.0), so units that boot a VM or an emulator with KVM cannot run there. Route
  them to a Claude model. If in doubt, make the brief's first step a feasibility probe that
  stops and reports on failure; that costs one short run.
- **Network.** Network access is off by default in `workspace-write`. Loopback-only tests and
  fetches need `network_access=true`.
- **Effort.** Pass `model_reasoning_effort` explicitly. With nothing configured, the effective
  effort was `none`, which is wrong for a milestone. The log's header shows the settings that took
  effect (`sandbox:`, `reasoning effort:`); read it right after launch, before the run gets far.
- **The brief.** Codex does not have the orchestrator's skills. Give it file paths to read (the
  plan, the process skill's `SKILL.md`), every rule it must follow (commit author, trailer, no
  push), and "stop before review". Then review its branch with a separate, read-only Codex session
  (for example through the `consult` skill), so a Codex unit spends no Claude quota on review.
  Resume the implementer with `codex exec resume <session-id>` for the fixes. `resume` takes
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

No one checks usage overnight, so the rules above are the only brake. If an implementer fails on
a usage limit, treat it like a crash: the last checkpoint stands, and the remaining units go to
the next pool in the table. If a reading fails or comes only from the cache, say so in the
progress line and keep following the last good reading.

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
