<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Model recommendation contract

Shared by `claude-model-selection` and `codex-model-selection`. It fixes how a
recommendation is evidenced and stated. Vendor facts, plan rules, model tables,
CLI controls and escalation thresholds stay in each vendor's skill; usage
readings and reserve thresholds stay in `quota-strategy` (this skill's
SKILL.md). It lives here only because both model skills already load this
sibling.

## Evidence tags

Tag every number and every claim a route depends on with exactly one of:

| Tag | Means | Must carry |
|---|---|---|
| **[published]** | The vendor states it. | A source in the skill's Sources list. |
| **[derived]** | Arithmetic on tagged inputs. | The inputs, so it can be redone when they change. |
| **[estimate]** | Third-party or own testing. | The source and its limits (one test, one task type). |
| **[policy]** | This skill's starting rule. | Nothing more; the user's constraints override it. |

Untagged route and escalation rules are **[policy]**. A [derived] value built on
an [estimate] is an [estimate].

Examples:

- **[published]** API list price is $10 per million output tokens.
- **[derived]** At $10 vs $4 per million, the per-token ratio is 2.5×.
- **[estimate]** On one third-party coding test the cheaper model was only 22% cheaper
  overall, because it used more tokens.
- **[policy]** Escalate after one failed attempt at max effort.

## Recommendation output

State each field, or say it is unknown:

1. **Model**: the exact model ID, not an alias.
2. **Effort**, and **speed** where the client has a speed setting.
3. **Billing mode**: what pays for the run (included subscription, credits, API), and
   how it was established; "unknown" if it was not.
4. **Rationale**: one or two lines, citing the tagged facts it rests on.
5. **Verification**: how the result will be checked before it is accepted.
6. **Escalate or stop**: the condition that moves to another model, and the one that stops.

## A recommendation is not an authorization

Recommending a model does not launch work, switch the current session, change saved
defaults, or approve extra spending. Each of those needs the user's go-ahead, or a
standing authorization the user already gave (for example, a plan's conventions block).
