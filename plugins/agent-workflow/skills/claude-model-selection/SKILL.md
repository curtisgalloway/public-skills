---
name: claude-model-selection
description: Choose between Claude Opus 5.5 and Fable 5.1 for a session, subagent, or scheduled run, accounting for the billing mode (Pro, Max, Team or Enterprise seat, or API) and deciding when to escalate from one to the other. Use when the user asks "Opus or Fable?", "which Claude model should I use for this", "is this worth Fable", "should I escalate", or when picking a model for a subagent, overnight run, or API job.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Claude model selection: Opus 5.5 vs Fable 5.1

- **Last reviewed:** 2026-10-09
- **Covers:** `claude-opus-5-5`, `claude-fable-5-1`
- **Not covered:** Sonnet 5.5, Haiku 5.5 (not yet analyzed). Codex and Gemini models belong in
  their own skills.

Each number below is tagged:
- **[published]** means Anthropic states it.
- **[estimate]** means it is derived or comes from third-party testing.

This skill decides *which model suits the task*. Reading usage pools and deciding whether
there is room to spend is the job of the `quota-strategy` skill in this plugin; this skill calls
its script rather than keeping its own thresholds.

## Step 0: Staleness check (run every time)

1. Compare **Covers** with the models available now: the session's model list, the system
   prompt, or the models overview at https://docs.claude.com.
2. The guide is stale if either is true:
   - A newer Opus, Fable, Mythos, Sonnet, or Haiku version exists.
   - **Last reviewed** is more than 60 days ago.
3. If it is stale, start the reply with one line: `claude-model-selection guide is stale:
   <reason>`. Then apply the rules below and label the recommendation provisional.
4. Do not rewrite the rules yourself. Updating is the user's call.

## Step 1: Identify the billing mode

Work this out before choosing a model. The deciding factor differs by mode.

| Signal | Billing mode |
|---|---|
| claude.ai, the desktop app, or Claude Code signed in with a Max plan, a Team premium seat, or an Enterprise seat-based premium seat (`/status` shows the plan) | **Capped subscription** (Step 2a) |
| Signed in with Pro, a Team standard seat, or an Enterprise seat-based standard seat | **Subscription without Fable** (Step 2b) |
| `ANTHROPIC_API_KEY` set, a Console API key, Agent SDK scripts, Bedrock or Vertex, third-party harnesses, usage-based Enterprise | **API** (Step 2c) |
| Capped subscription, but Fable's cap is used up and work continues on Fable | **Usage credits at API rates** (treat as API) |

To confirm, run `python3 <skill-dir>/../quota-strategy/scripts/claude_usage.py --model fable`.
Exit 0 lists a scoped Fable pool, so the plan caps Fable (Step 2a). Exit 1 means no Fable pool:
Fable either bills usage credits from the first token or is not on the plan (Step 2b). Exit 2
means no reading; ask the user which plan they are on.

**Gotcha:** if `ANTHROPIC_API_KEY` is set in the shell, Claude Code may bill the API instead of
the plan. Check `/status` before long runs.

## Step 2a: Capped subscription (Max, Team premium, Enterprise premium)

The constraint is **the weekly pool, not dollars**. A token costs nothing extra until a limit is
hit. The thing to protect is running out mid-week or mid-run.

Facts:
- **[published]** On these seats Fable may use **at most 50% of the weekly limit**. It comes out
  of the same pool as every other model; it is not a bonus on top.
- **[published]** Fable **uses the pool faster** than other Claude models. Anthropic does not
  publish the ratio.
- **[estimate]** The burn ratio is about 2.5× Opus per token, assuming it tracks API list prices.
- **[estimate]** Combined with the cap, the most Fable work in a week is about **1/5 of an
  all-Opus week**.
- **[published]** A rolling 5-hour window applies on top of the weekly limit.
- **[published]** The effort picker labels max effort as **4× or more usage**.
- **[estimate]** So Opus at max effort can burn about as fast as Fable at high effort. Escalating
  from Opus-max to Fable-high costs less extra than the per-token ratio suggests.
- **[published]** Fable's default effort is high in Claude Code but medium on claude.ai and in the
  desktop app.

Rules:
1. **Check the pools first** with `quota-strategy`'s `claude_usage.py`. Fable is eligible only
   when that skill's rules would not exclude it: its scoped limit, the general weekly limit, and
   the 5-hour window all below `quota-strategy`'s cutoffs.
2. **Unattended or overnight runs: Opus only.** If Fable hits its cap mid-run, the run either
   stalls or starts billing usage credits.
3. **Known-hard one-shot problems: going straight to Fable is fine.** Two failed Opus attempts at
   max effort can cost about as much pool as one Fable-high attempt [estimate].
4. **Escalation threshold:** escalate after **one** failed Opus attempt at max effort, as long as
   Fable is eligible under rule 1.

## Step 2b: Subscription without Fable (Pro, Team standard, Enterprise standard)

- **[published]** Fable is not in these plans' limits. It runs on pay-as-you-go usage credits
  from the first token (on Enterprise standard seats, only if the organization has enabled
  them). The Free plan has no Fable at all.

Rules:
1. **Use Opus.** Every Opus token is inside the plan; every Fable token is extra spend.
2. **Use Fable only with the user's approval** for that task, and then apply the API rules in
   Step 2c to the Fable part, since credits bill at API rates.
3. Check the general pools with `quota-strategy` before long Opus runs, as on any plan.

## Step 2c: API and usage credits (pay per token)

The constraint is **dollars**. There is no 50% cap.

Facts:
- **[published]** List prices are Opus $4/$20 and Fable $10/$50 per million tokens
  (input/output), so Fable is **2.5× per token**.
- **[estimate]** On real tasks the gap is smaller, because Opus tends to use more tokens (it
  overthinks). In one third-party coding test, Opus came out only **22% cheaper** overall.
- **[estimate]** The effective cost ratio is about **1.3×–2.5×**, depending on how verbose Opus
  gets.

Rules:
1. **Default to Opus for high-volume and repeated calls:** subagents, batch jobs, scheduled
   reports. The per-token difference compounds.
2. **Use Fable for single high-value calls** where a retry costs more than the 2.5× premium.
3. **Escalation threshold:** escalate after **two** failed Opus attempts at max effort.
4. **Cap Opus thinking budgets** on API runs. Runaway thinking is what eats Opus's price
   advantage.

## Default (all modes)

**Use Opus 5.5. Fable 5.1 is the exception.**
- **[published]** Anthropic says Opus 5.5 performs at Fable 5.1's level on most work.
- **[published]** Opus leads on agentic coding (Terminal-Bench 4.0: 66.4% vs 55.8%).
- **[published]** Anthropic says the gap in its own use is narrower than the benchmarks suggest.

## Route to Opus 5.5

- **Agentic loops with a check:** tests, builds, linters, or hardware feedback the model can
  verify against.
- **Long unattended or overnight runs**, including multi-milestone orchestration.
- **Subagents and delegated implementation.**
- **Security-adjacent work:** debug protocols, fuzzing, reverse engineering, LLM harnesses.
  Fable has extra safeguards for cybersecurity and LLM R&D that may refuse these.
- **Anything needing fast mode.** Fast mode is supported only on Opus models.

## Route to Fable 5.1

- **One-shot tasks with no way to verify** the result, where it has to be right without tests.
- **Concurrency and ordering reasoning** (locks, IRQ context, races) that Opus has already
  looped on or returned nothing for.
- **Deliverables that must be right the first time and concise**, such as decks or tight prose.
- **Latency-sensitive work**, when the answer is needed fast.

## Escalation rule

1. Start on Opus 5.5 at the effort level the task needs.
2. Escalate to Fable 5.1 at **high** effort when either happens:
   - Opus fails at max effort: once on a capped subscription, twice on the API (Steps 2a, 2c).
   - Opus burns its budget without producing output.
3. Before escalating, confirm Fable is eligible (Step 2a rule 1) or approved (Step 2b). If not,
   stay on Opus and narrow the task instead.
4. If Fable returns something plausible but shallow, go back to Opus and add tests.
5. If a lab notebook or session log exists, record the switch, the reason, and the billing mode
   in one line.

## Failure signatures

| Model | Typical failure | What to do |
|---|---|---|
| Opus 5.5 | Overthinks, runs out of room, buries the point | Escalate to Fable, narrow the task, or cap thinking (API) |
| Fable 5.1 | Cuts corners | Return to Opus with tests |

## Comparing the two fairly

- **Match effort levels.** Opus defaults to medium. Fable defaults to high in Claude Code and
  medium on claude.ai.
- **Use exact model IDs, not aliases.**
  - `claude --model claude-opus-5-5`
  - `claude --model claude-fable-5-1`
- **Claude Code:** Opus 5.5 needs version 2.1.280 or later.
- **Compare total cost per accepted result,** not per-token price.

## Updating this skill when new models ship

Budget 30–45 minutes. Wait at least one week after launch, so independent reviews exist.

1. **Official facts (15 min).** Read the Anthropic launch post, the docs.claude.com model page,
   and the support.claude.com article on plan availability. Record:
   - API price
   - plan treatment per seat type: included or not, any cap, any "uses limits faster" note
   - default effort per surface
   - the effort-picker usage multipliers
   - special safeguards
   - fast-mode support
2. **Independent reviews (15 min).** Read 2–3 comparisons. Record:
   - each model's failure signatures
   - real-task total cost, not just per-token price
3. **Rewrite (10 min).** Update Steps 1–2c, Default, both Route sections, and Failure
   signatures. Re-derive both [estimate] ratios.
4. **Bookkeeping (5 min).** Update **Last reviewed**, **Covers**, and **Sources**.

## Sources (as of 2026-10-09)

- https://support.claude.com/en/articles/15424964-claude-fable-5-promotional (official plan
  availability and the 50% cap)
- https://www.notebookcheck.net/Claude-Fable-5-1-is-not-included-in-your-Pro-subscription.1385320.0.html
- https://christopheralarcon.com/blog/claude-opus-5-5-vs-fable/ (effort-picker multipliers)
- https://theaicareerlab.com/blog/claude-opus-5-5-vs-fable-5-1-for-professionals
- https://thenewstack.io/claude-opus-5-5-vs-fable-5-1/ (real-task cost comparison)
