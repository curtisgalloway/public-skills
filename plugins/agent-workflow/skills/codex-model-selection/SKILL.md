---
name: codex-model-selection
description: Choose GPT-6.1 Sol, GPT-6 Astra, or GPT-6 Luna for a Codex session, subagent, or scheduled run, accounting for subscription allowances, paid credits, API billing, reasoning effort, and escalation. Use when the user asks "which Codex model", "Sol or Astra", "can Luna handle this", or wants a Codex model recommendation for delegated or unattended work.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Codex model selection

**Terms.**
- *Reasoning effort*: how much reasoning the model spends before and during its work.
- *Usage pool*: a subscription allowance with its own reset time.
- *Credits*: paid units used for work outside included allowances or on credit-based plans.
- *Speed mode*: a processing-speed choice, separate from model and reasoning effort.
- *Subagent*: a separate agent session assigned part of the work.

See the repository [glossary](../../../../GLOSSARY.md) for shared terms.

- **Last reviewed:** 2026-10-09
- **Covers:** `gpt-6.1-sol`, `gpt-6-astra`, `gpt-6-luna` in Codex; API prices for comparison.
- **Not covered:** specialized models, custom providers, or migration of existing model pins.
- **Needs:** the current client's model picker or catalog and official documentation access.
  Quota checks additionally need the sibling `quota-strategy` skill and its Python 3.9+ helper
  when no current client reading is available.
- **Input:** task, quality check, available models, billing mode, time/spending constraints.
- **Output:** exact model ID, effort, speed, reason, and escalation/stop condition. State any
  unknown access or billing information. Recommending a model does not itself launch work,
  switch the current session, change saved defaults, or authorize extra spending.

**[published]** marks official facts, **[derived]** arithmetic, and **[policy]** this skill's
starting rules, which the user's constraints can override. These rules are not benchmark
results. Usage readings and reserve thresholds belong to
[quota-strategy](../quota-strategy/SKILL.md); do not maintain another copy here.

## Step 0: Check freshness and availability

1. Compare **Covers** with the current model picker/tool schema and the official
   [model guide](https://learn.chatgpt.com/docs/models). In CLI versions exposing it,
   `codex debug models` displays the catalog; check `codex debug --help` first.
   `--bundled` is an offline snapshot, not proof of account access or freshness.
2. If a covered family has a newer model, relevant access/pricing has changed, or the review
   date is over 60 days old, say `codex-model-selection guide is stale: <reason>` and make
   the recommendation provisional. If sources cannot be checked, report freshness unknown.
3. Use verified current facts for the recommendation, but do not silently rewrite this skill
   or replace a model the user explicitly requested. Never invent a replacement model ID.
4. Confirm access in the actual client and workspace. **[published]** GPT-6.1 Sol's launch
   includes Plus, Pro, Business, Enterprise, and Edu; Enterprise/Edu administrators must
   enable it, and Free/Go are excluded at launch.
   [Source](https://learn.chatgpt.com/docs/models#gpt-61-sol).

## Step 1: Establish what pays for the run

Use the client's account/status display; in the CLI, `/status` and `codex login status`
provide evidence. Also account for an explicitly configured provider or launch override.
Do not read credentials or infer effective billing merely from an environment variable's
presence. If billing is unknown, ask whether this is included usage, paid credits, or an API
key before authorizing a paid route; a conditional recommendation can proceed.

| Billing mode | What to protect | Action |
|---|---|---|
| ChatGPT sign-in, included allowance | Remaining usage until reset | Apply Step 2a |
| Purchased credits or a workspace credit agreement | Approved credit budget | Apply Step 2b |
| API key or explicitly configured paid provider | Approved money budget | Apply Step 2c; provider-specific rates override OpenAI's table |

### Step 2a: Included subscription usage

**[published]** Codex and ChatGPT Work share usage. Pro currently has no five-hour limit;
other plans can have short-window and weekly limits. API prices do not predict included
task counts. A turn crossing a limit may finish, so the limit is not a precise spending stop.
[Source](https://learn.chatgpt.com/docs/pricing).

**[policy]** Before a long run or escalation, use a current client usage reading and apply
`quota-strategy`. Its offline fallback is:

```bash
python3 <skill-dir>/../quota-strategy/scripts/codex_usage.py --json
```

Read that skill for freshness, reserve, and stop rules. A missing/stale reading means unknown
capacity; it does not establish a full pool. If the sibling skill is unavailable, obtain a
fresh dashboard reading and an explicit reserve before starting unattended work. Changing
models does not create a new allowance. Do not infer an Astra cap from Claude's Fable rules.

Use Sol for general work, Luna for bounded units, and Astra when the task warrants it and
capacity permits. For overnight work, prefer Standard speed and an explicit checkpoint at
each unit boundary. Establish whether paid continuation is enabled and already authorized;
do not switch to credits or an API key merely because the included pool is exhausted.

### Step 2b: Paid credits

**[published]** Standard-speed rates per million tokens:

| Model | Input | Cached input | Output |
|---|---:|---:|---:|
| GPT-6.1 Sol | 50 credits | 2.5 credits | 250 credits |
| GPT-6 Astra | 250 credits | 25 credits | 1,250 credits |
| GPT-6 Luna | 2.5 credits | 0.25 credits | 12.5 credits |

Credit billing has no separate cache-write charge. Credit purchase prices depend on the plan
or agreement; do not assume a universal dollar conversion.
[Source](https://learn.chatgpt.com/docs/pricing#token-rates).

**[policy]** Apply the task routes below within the authorized budget. Budget the complete
run, including retries and review. A subscription usage log cannot establish credit balance
or permission to spend. If the account uses a legacy or contractual rate card, use that card.

### Step 2c: API billing

**[published]** Standard API prices in USD per million tokens, for prompts up to 272K input
tokens; these are separate from Codex credits:

| Model | Input | Cached input | Cache writes | Output | Source |
|---|---:|---:|---:|---:|---|
| `gpt-6.1-sol` | $2 | $0.10 | $2.50 | $10 | [Sol](https://developers.openai.com/api/docs/models/gpt-6.1-sol) |
| `gpt-6-astra` | $10 | $1 | $12.50 | $50 | [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra) |
| `gpt-6-luna` | $0.10 | $0.01 | $0.125 | $0.50 | [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) |

All three pages specify higher rates above 272K input tokens: 2x input/cache and 1.5x output
for the whole request. Tool charges and applicable processing premiums are additional.

**[derived]** With equal uncached input and output counts, Astra costs 5x Sol, and Sol costs
20x Luna. Cached-input ratios differ. These ratios predict neither subscription consumption
nor total task cost: a stronger model may finish with fewer attempts.

**[policy]** Prefer Luna for verified repetitive units and Sol for general implementation.
Use Astra directly when a failed attempt would cost more than its premium. Bound retries
and total spending through the caller's supported controls; a reasoning-effort setting is
not a dollar cap. Compare cost per accepted result, including review and failed attempts.

## Choose the model and effort

**[published]** OpenAI recommends Sol for complex coding and long-running work, Luna for
focused repeatable tasks, and Astra for the most demanding work. Max spends more reasoning
on one task; Ultra uses subagents. Luna has no Ultra mode.
[Source](https://learn.chatgpt.com/docs/models).

The following are **[policy]** starting points, not mandatory changes to an existing session:

| Task | Starting choice | Verification or escalation trigger |
|---|---|---|
| A specified command, extraction, or mechanical edit with a clear check | Luna, `low` for commands; `medium` or `high` for implementation | Escalate if the check fails because reasoning or scope exceeded the brief |
| General coding, debugging, multi-file implementation, repeated scheduled work | Sol, `medium` | Use `high` when the task requires deeper planning or diagnosis |
| Ambiguous architecture, subtle concurrency, difficult cross-system diagnosis | Astra, `high` | Define what evidence would resolve the question before starting |
| Long unattended run | Sol for coordination; Luna for independently checkable units, if delegation is authorized | Apply quota/budget gates at every boundary, including review |
| Tight latency target | Narrow the task and try lower effort first | Pay for a faster speed only when latency justifies it |

Check supported efforts in the current client. The codex-cli 0.162.1 bundled catalog inspected
on the review date offered `low`, `medium`, `high`, `xhigh`, and `max` for all three; Sol and
Astra also offered `ultra`. Its defaults were Sol/Astra `low` and Luna `medium`. Defaults and
available controls can differ by client; the table deliberately selects effort explicitly.
Do not pass Codex's `ultra` to an API request: the API model pages list different supported
controls. Ultra involves delegation and requires the same authorization as other subagents.

**[published]** Relative to Standard, Fast consumes 2.5x included usage or 2x paid credits;
Sol/Astra Ultrafast consumes 8x included usage or 6x paid credits, where available.
[Source](https://learn.chatgpt.com/docs/pricing).
**[policy]** Start at Standard unless the user has chosen another speed. Fast processing and
high reasoning effort solve different problems; neither guarantees a better answer.

## Escalate on evidence

These are **[policy]** retry limits, shared across billing modes because this skill has no
measured evidence for a different optimal count on subscriptions versus API calls:

1. Distinguish a reasoning failure from missing access, a broken build environment, an
   unclear requirement, or a provider refusal. A model upgrade does not fix those conditions;
   resolve the prerequisite or report it. Do not route around a safety refusal.
2. After one failed Luna implementation and a concrete failed check, hand the evidence to Sol.
3. After a Sol failure, allow one targeted retry with improved evidence or higher supported
   effort if it has a plausible fix. After two failed verifications, recommend Astra for the
   remaining reasoning problem, subject to access, capacity, and the approved budget. Do not
   force a Max attempt first. Known-hard tasks can start with Astra.
4. Preserve tests, failed approaches, and constraints in the handoff. Do not restart blindly.
   For subagents under `quota-strategy`, its eligibility and rerun rules take precedence.
5. If Astra also fails to make progress, narrow the task or request missing evidence; do not
   start an unbounded cycle of model switches. Return to Sol/Luna for routine execution once
   the hard decision is resolved.

Record a switch's model, effort, speed, billing mode, and reason in an existing session log.
Do not attribute fixed failure personalities to these models without measured evidence.

## Apply a choice

Use `/model` in an interactive Codex CLI session. For an already authorized new run, set the
exact model and effort explicitly; these flags were checked with codex-cli 0.162.1:

```bash
codex --model gpt-6.1-sol -c model_reasoning_effort=medium
codex exec --model gpt-6-luna -c model_reasoning_effort=high - < <brief-file>
```

These examples inherit the caller's speed, provider, and permission configuration. Confirm
those settings separately. Use the current client's supported speed control; do not invent a
CLI flag or silently edit saved configuration. For subagents, inspect the tool schema and
select a supported model/effort explicitly; use a fresh context when required for overrides.
Launching details belong to [run-delegate](../run-delegate/SKILL.md#launching-a-runner) and
`quota-strategy`. Preserve the existing permission controls.

Check effective model and effort in session metadata or the run header where exposed. If
they cannot be confirmed, label them unverified. A recommendation alone cannot switch the
assistant currently answering. For comparisons, hold the task, checks, context, and speed
constant, record effort, and measure both acceptance quality and total usage/time.

## Updating this skill

When asked to update it, recheck the linked official sources and the current CLI catalog.
Update model IDs, access, prices, effort/speed support, **Last reviewed**, and source links
together. Keep policy separate from published facts. Add benchmark or failure-pattern claims
only with a reproducible comparison and its limitations; do not manufacture them to mirror
the Claude skill. Keep quota thresholds and usage-reading mechanics in `quota-strategy`.
