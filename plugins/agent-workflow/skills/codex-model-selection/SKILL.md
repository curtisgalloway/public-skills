---
name: codex-model-selection
description: Choose GPT-6.2 Sol, GPT-6.2 Astra, GPT-6.1 Terra, or GPT-6 Luna for a Codex session, subagent, or scheduled run, accounting for subscription allowances, paid credits, API billing, reasoning effort, and escalation. Use when the user asks "which Codex model", "Sol or Astra", "can Luna handle this", or wants a Codex model recommendation for delegated or unattended work.
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

- **Last reviewed:** 2026-11-19
- **Covers:** `gpt-6.2-sol`, `gpt-6.2-astra`, `gpt-6.1-terra`, and `gpt-6-luna` in Codex,
  with API prices for comparison.
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
Tags and output fields follow the shared
[recommendation contract](../quota-strategy/references/model-recommendation.md), which
`claude-model-selection` uses too; vendor rules stay here.

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
4. Confirm access in the actual client and workspace. **[published]** Codex CLI requires
   version 0.166.0 or later for GPT-6.2 Sol and Astra. Available models depend on the plan,
   seat, and workspace settings. If a pinned model is unavailable, report that and offer
   a verified alternative for the user's approval.
   [ChatGPT Work and Codex availability](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).

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
| Enterprise USD usage-based agreement | Approved money budget | Use the workspace agreement and Enterprise USD rate card |
| API key or explicitly configured paid provider | Approved money budget | Apply Step 2c. Use provider-specific rates when applicable |

### Step 2a: Included subscription usage

**[published]** Codex and ChatGPT Work share usage. Pro currently has no five-hour limit;
other plans can have short-window and weekly limits. API prices do not predict included
task counts. A turn crossing a limit may finish, so the limit is not a precise spending stop.
[Source](https://learn.chatgpt.com/docs/pricing).

**[policy]** Before a long run or escalation, use a current client usage reading and apply
`quota-strategy`. If the client reading is unavailable, use its helper to try a live read:

```bash
python3 <skill-dir>/../quota-strategy/scripts/codex_usage.py --json
```

Use `--offline` for a log-only reading. Read that skill for freshness, reserve, and stop
rules. A missing or stale reading leaves capacity unknown. If the sibling skill is
unavailable, obtain a fresh dashboard reading and an explicit reserve before starting
unattended work. Changing models does not create a new allowance. Check any model-specific
limits against the current plan.

For overnight work, prefer Standard speed and an explicit checkpoint at each unit boundary.
Establish whether paid continuation is enabled and already authorized before launching.

### Step 2b: Paid credits

**[published]** Standard-speed rates per million tokens:

| Model | Input | Cached input | Output |
|---|---:|---:|---:|
| GPT-6.2 Astra | 200 credits | 10 credits | 1,000 credits |
| GPT-6.2 Sol | 50 credits | 2.5 credits | 250 credits |
| GPT-6.1 Terra | 25 credits | 1.25 credits | 125 credits |
| GPT-6 Luna | 2.5 credits | 0.25 credits | 12.5 credits |

Credit billing has no separate cache-write charge. Credit purchase prices depend on the plan
or agreement. [ChatGPT credit rates](https://learn.chatgpt.com/docs/pricing#token-rates).

**[policy]** Apply the task routes below within the authorized budget. Budget the complete
run, including retries and review. A subscription usage log cannot establish credit balance
or permission to spend. If the account uses a legacy or contractual rate card, use that card.

### Step 2c: API billing

**[published]** Standard API prices in USD per million tokens, for prompts up to 272K input
tokens; these are separate from Codex credits:

| Model | Input | Cached input | Cache writes | Output | Source |
|---|---:|---:|---:|---:|---|
| `gpt-6.2-astra` | $8 | $0.40 | $10 | $40 | [Astra](https://developers.openai.com/api/docs/models/gpt-6.2-astra) |
| `gpt-6.2-sol` | $2 | $0.10 | $2.50 | $10 | [Sol](https://developers.openai.com/api/docs/models/gpt-6.2-sol) |
| `gpt-6.1-terra` | $1 | $0.05 | $1.25 | $5 | [Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra) |
| `gpt-6-luna` | $0.10 | $0.01 | $0.125 | $0.50 | [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna) |

The listed cache-write rates use 30-minute retention. Above 272K input tokens, all four
models charge 2× input and cache rates and 1.5× output for the full request. Tool charges
and applicable processing premiums are additional. Fast costs 2× the applicable Standard
API rate for all four. API Ultrafast for the two GPT-6.2 models costs 3× Standard through
February 28, 2027, and 6× starting March 1, 2027 (Pacific time).
[API pricing](https://developers.openai.com/api/docs/pricing).

**[derived]** With equal uncached input and output counts at Standard API rates, Astra costs
4× Sol, Sol costs 2× Terra, and Terra costs 10× Luna. Cached-input ratios differ. To compare
total task cost, count retries, review, and usage from tools in addition to model tokens.

**[policy]** Prefer Luna for verified repetitive units and Sol for general implementation.
Use Astra directly when a failed attempt would cost more than its premium. Bound retries
and total spending through the caller's supported controls; a reasoning-effort setting is
not a dollar cap. Compare cost per accepted result, including review and failed attempts.

## Choose the model and effort

**[published]** OpenAI recommends GPT-6.2 Sol for everyday coding, GPT-6.2 Astra for demanding
work, GPT-6.1 Terra for visual understanding and computer use, and GPT-6 Luna for focused,
repeatable work. The Work and Codex model guide suggests starting Luna at High for general
use. Max increases reasoning on a single task. Ultra uses subagents. Luna supports up to Max.
[Work and Codex model guide](https://learn.chatgpt.com/docs/models).

Use these **[policy]** starting points when the user has left the choice open.

| Task | Starting choice | Verification or escalation trigger |
|---|---|---|
| Exact commands and a report with objective checks | `gpt-6-luna`, `low` | Escalate when the task needs diagnosis or code changes |
| Bounded extraction or mechanical implementation with a clear check | `gpt-6-luna`, `medium` or `high` | Escalate if the check fails because reasoning or scope exceeded the brief |
| Interpret screenshots, charts, or app state, or operate a supported app | `gpt-6.1-terra`, `low` for straightforward work, `medium` for multistep work | Verify readings against the source. Use Sol when code or diagnosis becomes the main task |
| General coding, failure diagnosis, or multi-file implementation | `gpt-6.2-sol`, `medium` | Use `high` when the task requires deeper planning or diagnosis |
| Ambiguous architecture, subtle concurrency, difficult cross-system diagnosis | `gpt-6.2-astra`, `high` | Define what evidence would resolve the question before starting |
| Long unattended run | `gpt-6.2-sol` for coordination, with `gpt-6-luna` for independently checkable units if delegation is authorized | Apply quota and budget gates at every boundary, including review |
| Tight latency target | Narrow the task and try lower effort first | Pay for a faster speed only when latency justifies it |

**Local catalog check.** The bundled catalog in Codex CLI 0.171.0-alpha.13 lists `low`,
`medium`, `high`, `xhigh`, and `max` for all four models, plus `ultra` for Sol, Astra,
and Terra. It defaults to `low` for those three and `medium` for Luna. Check current
client controls and get authorization for delegation before selecting Ultra.

**[published]** API reasoning controls differ. The API rejects `none` for GPT-6.2 Sol and
Astra. The Terra and Luna API pages list `none`, `low`, `medium` (default), `high`,
`xhigh`, and `max`. For API delegation on GPT-6.2, use the Responses API's Multi-agent
beta. [Using GPT-6.2 in the API](https://developers.openai.com/api/docs/guides/latest-model),
[Terra API model](https://developers.openai.com/api/docs/models/gpt-6.1-terra),
[Luna API model](https://developers.openai.com/api/docs/models/gpt-6-luna).

**[published]** Work and Codex speed multipliers apply relative to Standard on the same
model. [Work and Codex pricing](https://learn.chatgpt.com/docs/pricing).

| Speed and model | Included allowance | Eligible purchased credits or Enterprise pay-as-you-go |
|---|---:|---:|
| Fast on GPT-6.2 Sol and Astra | 2× | 2× |
| Fast on GPT-6.1 Terra and GPT-6 Luna | 2.5× | 2× |
| Ultrafast on GPT-6.2 Sol and Astra | 6× | 3× through February 28, 2027, then 6× starting March 1 (Pacific time) |

Ultrafast for both GPT-6.2 models is available to Pro $500 and eligible Enterprise and
Edu workspaces. Pro $200 offers GPT-6.2 Sol Ultrafast in Codex. Confirm eligibility and
administrator controls in the actual client.
[Work and Codex speed settings](https://learn.chatgpt.com/docs/agent-configuration/speed),
[Plan availability](https://help.openai.com/en/articles/20001275-chatgpt-work-and-codex).

**[policy]** Start at Standard unless the user has chosen another speed. Treat reasoning
effort and processing speed as independent settings.

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
exact model and effort explicitly. Codex CLI 0.171.0-alpha.13 exposes these flags.

```bash
codex --model gpt-6.2-sol -c model_reasoning_effort=medium
codex exec --model gpt-6-luna -c model_reasoning_effort=low - < runner-brief.txt
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
