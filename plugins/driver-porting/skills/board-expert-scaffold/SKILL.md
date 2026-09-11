---
name: board-expert-scaffold
description: >-
  Scaffold a new board-expert skill for an SoC / single-board computer, matching the structure of the
  existing experts (rpi-expert, indiedroid-nova-expert). Use when the user asks to scaffold, create,
  or generate a board-expert or bring-up reference skill for a specific board, SoC, or chip family.
  Authoring skill only — it does not itself read source or answer hardware questions. Ships
  template.md, the SKILL.md skeleton every board expert is written from.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Board-expert scaffold (generate a new board-expert skill)

You produce a new **board-expert skill**: a board-specific MAP that a coding agent or developer consults
for low-level bring-up questions about one SoC / SBC family. A board-expert skill owns the *where* and
*what* (sources, addresses, quirks); it defers all *method* and the clean-room discipline to
`os-investigator`, and it is consumed by `cleanroom-spec` when speccing individual drivers and by
`reference-driver-review` when it needs to locate the authoritative reference driver for a board.

The two reference implementations to mirror are **`rpi-expert`** (Raspberry Pi 5 / BCM2712 + RP1) and
**`indiedroid-nova-expert`** (Rockchip RK3588S). Read one of them if you want a fully-worked example;
the template (in `template.md` beside this file) is distilled from both.

## What a board-expert skill is (and isn't)

- **It is** a board/SoC *map*: which repos+branches hold the device trees and drivers, which datasheet/
  TRM to cite, the physical/MMIO addressing model, the boot chain + exception-level hand-off, the
  interrupt controller, debug UART, timers, clocks/power, GPIO/pinmux, and the board-specific gotchas.
- **It is a subagent role.** Its body is written for the agent that *is* the expert and reads source.
  Every board-expert skill therefore carries a "delegate; don't inline" block so the main/orchestrating
  agent spawns a subagent instead of running the body inline and pulling GPL source into the context
  that writes the differently-licensed target-OS code.
- **It is not** the method. The investigation procedure, the report format, and the no-source-code rule
  live in `os-investigator`; the generated skill points at it rather than restating it.
- **It is not** a driver spec. Per-peripheral implementation specs are `cleanroom-spec`'s job (or
  `anchored-peripheral-spec`'s, for source you own); the board expert supplies the facts those skills
  route through.

## Conventions to honor

- **One slug everywhere.** Use the same kebab-case slug for the directory
  (`plugins/driver-porting/skills/<slug>/`), the frontmatter `name:`, and every place the skill is
  registered. A good slug is `<soc-or-board>-expert`, e.g. `rk3399-expert`, `bcm2711-expert`,
  `jh7110-expert`.
- **Agent-neutral prose.** Refer to "the agent", not to any one product's name.
- **License header: match the target repo's convention.** In this repo a SKILL.md carries a two-line
  SPDX comment immediately *after* the frontmatter, never above it — a comment before the frontmatter
  stops it parsing. A private skills repo may carry no header at all; copy what its neighbors do.
- **Cache convention.** Each board expert clones its reference material under
  `~/src/<short>-resources/` (e.g. `~/src/rpi5-resources/`) and that cache is for the expert subagent
  only. Pick a short, unambiguous `<short>` from the board/SoC name.
- **Clean-room first.** The generated skill must tell the expert to return facts/mechanism, never
  source, and to cite the datasheet/TRM/ARM spec as the *authority* and the kernel as the *map*.

## Steps

1. **Interview for the inputs** (ask only for what you don't already have; one concise batch):
   - **Identity:** marketing/board name(s), the SoC part number, the core topology (e.g. 4×A76+4×A55),
     notable variants/aliases, and the **trigger keywords** the skill's description should fire on.
   - **Sources:** the repos + branches to clone — vendor/downstream Linux *and* mainline if both carry
     it; Trusted Firmware-A platform dir; U-Boot; any vendor BSP; firmware/boot blobs. Note the
     highest-value files (the board `.dts`, the SoC `.dtsi`, the console UART driver, the irqchip).
   - **Citations:** the authoritative datasheet / TRM / programmer's guide URLs (and public *proxy*
     parts when the exact one is NDA), plus the relevant ARM specs (GIC, PSCI, SCMI, ARM ARM).
   - **Cache:** the `~/src/<short>-resources` directory name.
   - **Quick-facts** (fill what's known; leave the rest as TODO for the expert/user to confirm on
     hardware): addressing model, boot chain + entry EL + MMU/cache state + DTB-pointer register +
     secondary-core release, SMP/MPIDR mapping, interrupt controller (version + GICD/GICR/GICC
     addresses + DT interrupt-cells + SPI/PPI INTID base), debug UART (IP + address + IRQ +
     reg-shift/io-width + baud + earlycon + pinmux), timers (freq + PPIs), clocks/power (firmware-owned
     vs OS-managed CRU/SCMI/PMIC), GPIO/pinmux banks + syscon, DTB runtime patching.
2. **(Optional) Offer to research-fill the facts.** If the user wants the quick-facts/sources
   populated rather than stubbed, spawn a subagent with the harness's delegation tool, have it **load
   `os-investigator` + (if one already exists) a sibling board expert**, and ask it to return the
   addressing model / boot hand-off / GIC / UART / timer / clock facts as a clean-room report (facts
   only, no source). Drop the returned facts into the template. Do **not** read the source yourself.
3. **Write `plugins/driver-porting/skills/<slug>/SKILL.md`** from `template.md` (beside this file),
   substituting every `<...>` placeholder and filling the quick-facts/gotchas with known values; mark
   anything unverified `TODO (verify on hardware)` rather than guessing.
4. **Decide the home repo and register.** A board expert with nothing private in it belongs in this
   repo, under `plugins/driver-porting/skills/<slug>/`, and has to be registered in two more places:
   the Themes table in the root `README.md` (the `driver-porting` row) and the "Board experts" list in
   `plugins/driver-porting/README.md`. `python3 utilities/check-skill-registration.py` confirms both;
   CI runs it on every push. A board expert that names private hosts, caches, or NDA material goes in
   your private skills inventory instead and is registered the way that repo requires.
5. **Remind to sync.** If the user's machines link skills from a checkout with a sync tool (qbranch,
   for example), tell them to re-run it so the new skill is linked into their skills directory; a
   plugin install picks it up on the next update.
6. **Don't push unprompted.** Stage/commit if asked; follow the repo's push rules.

## Filling guidance

- **Quick-facts are the value.** A board expert with vague quick-facts is just a link dump. Get the
  addressing model, the entry exception level, and the debug-UART address right first — those are the
  facts that brick bring-up if wrong, and the ones investigators reach for most.
- **Cite the datasheet, map with the kernel.** When the SoC has no public datasheet, say so and note
  that the device tree is the primary public address map (as `rpi-expert` does for BCM2712).
- **Public proxy parts.** If the exact part is NDA, point at the closest publicly-documented
  family member or the IP vendor's databook (Synopsys DesignWare, ARM PrimeCell, Cadence GEM, …).
- **Plain TODOs.** Mark anything you couldn't verify `TODO (verify on hardware)`. A clearly-flagged
  gap is useful; a confident wrong address is a bring-up trap.

## Quality bar

- One slug for the directory, the frontmatter `name`, and every registration; agent-neutral prose;
  license header per the target repo's convention.
- The fixed sections (delegate-don't-inline, os-investigator deferral, report) are present and intact —
  these are non-negotiable for the clean-room boundary.
- The description is short: what the skill is + the trigger keywords. Procedure detail belongs in the
  body, not the description (descriptions are loaded into every session).
- Sources name obtainable repos/branches *and* citable datasheets/specs, not just the kernel.
- Quick-facts cover the standard dimensions; unverified items are flagged, not guessed.
- The skill is registered where its repo requires (`check-skill-registration.py` passes here) and
  synced or installed on the machines that need it.
