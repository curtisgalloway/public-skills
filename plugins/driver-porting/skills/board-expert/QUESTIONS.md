<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Questions: the catalog and the `Needs decision` protocol

Shared by every skill that produces or consumes board specs. The rule in one line: **never guess
identity, instance, tree, mode, or root. Ask, in one structured batch, with a recommended default
where one exists. Default everything else and say so.**

## Terms

- **Orchestrator** — the skill running in the main agent's context: `cleanroom-spec`,
  `anchored-peripheral-spec`, `reference-driver-review`, `board-spec-scaffold`. It may ask the user.
- **Subagent role** — a skill whose body runs in a spawned subagent: `board-expert`,
  `os-investigator`. It cannot reach the user. It returns a `Needs decision` block instead.
- **Fork** — a missing input for which different answers lead to materially different work.
- **Gap** — a missing fact that only makes the result less complete. Gaps are defaulted and marked,
  never asked about.

## Who asks

| Skill | Role | Behavior |
| --- | --- | --- |
| `cleanroom-spec` | orchestrator | asks at intake, and again for any `Needs decision` the expert returns |
| `anchored-peripheral-spec` | orchestrator | asks at intake: repository and commit, peripheral, instance |
| `reference-driver-review` | orchestrator | asks when the reference cannot be resolved from a board spec |
| `board-spec-scaffold` | orchestrator | asks in its interview; this catalog is the interview's checklist |
| `board-expert` | subagent | never asks; returns `Needs decision` |
| `os-investigator` | subagent | never asks; returns `Needs decision` |

## How to ask

- **One batch.** Collect every fork that blocks the work and ask them together. Do not drip one
  question per turn.
- **Structured.** If the harness has a structured-question tool, use it: one question per fork, the
  options as choices, the recommended option first and marked as such. Without one, a numbered list
  with the same options and "reply with the numbers", never a free-form "tell me more".
- **Options come from the specs.** Board variants from `triggers`/`aliases` of the specs that
  matched; instances from the SoC spec's `instances:` rows; trees from the board spec's `repos`;
  roots from the roots the reader collected. If the specs offer no options, say so and ask openly.
- **State the default you would take** for every question that has one, so a "just go" answer is
  well defined.
- **Then proceed.** Once answered, do not re-ask in the same task.

## The catalog

Ask only the questions whose answer is missing. Each entry: what is missing → the question → where
the options come from → default, if any.

1. **Which hardware.**
   - The board name matched several specs or variants → "Which one: <variants>?" Options from the
     matching specs' `name` and `aliases`. No default.
   - The board revision changes the facts (different SoC stepping, different PMIC) → "Which
     revision?" Options from the board spec if it lists them. Default: the latest, stated.
   - The board resolves nothing but an SoC does → "The board has no spec. Continue from the
     `<soc>` SoC spec with board facts missing, or scaffold the board first?" Default: continue.
   - The function named lives on two chips (a UART on the SoC and on a companion) → "On the SoC or
     on <chip>?" Options from the `instances:` rows. No default.
2. **Which instance.** The IP resolves and the SoC has several placements → "Which `<ip>`
   instance: <name (role)> ...?" Options from `instances:` rows with matching `ip`. Default: none,
   unless exactly one row has a `role` matching the question.
3. **Which tree and ref.**
   - Anchored or generic → "Anchor to <board>'s kernel at <ref>, or generic from mainline at head?"
     Default: anchored when a board was named, generic otherwise.
   - The board spec lists two Linux repositories → "Lead with <vendor tree> or <mainline>?"
     Default: the vendor tree, mainline for provenance.
   - A ref pin is wanted for reproducibility → "Pin to <tag> or read head?" Default: head, commit
     recorded.
4. **Which root and layer.** For the scaffold and for overlays.
   - "Write the spec under: this repository's public root, the tree root next to the driver, a
     vendor root, or a new root?" Options from the roots collected. Default: the tree root if the
     current checkout has one, else the public root.
   - For an overlay: "Which vendor skill does this overlay go through?" Options from loaded vendor
     skills. No default.
5. **How far.** "Full driver spec, quick-facts only, or answer the one question?" Default: what the
   caller asked for; if nothing was asked for, quick-facts.

Anything not in the catalog is a gap: default it, mark it `TODO (verify on hardware)` or "not
established", and move on.

## The `Needs decision` block

A subagent that hits a fork stops the work that depends on it, finishes everything that does not,
and adds this block to its report, before the provenance section:

```
## Needs decision
1. <what is missing, one line> — options: <a> | <b> | <c>; recommended: <a> because <reason>.
   Blocks: <which part of the answer waits on this>.
2. ...
Answered so far / assumed: <list, so the orchestrator does not re-ask>
```

The orchestrator turns each numbered item into one structured question, asks the batch, and re-runs
the subagent with the answers added to its prompt as `decisions:` lines. A subagent must never
answer a fork by picking silently; a picked default is stated in the block as "assumed", so the
orchestrator can still override it.
