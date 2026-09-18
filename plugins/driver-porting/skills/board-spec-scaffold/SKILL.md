---
name: board-spec-scaffold
description: >-
  Scaffold a new board spec (board, SoC, companion chip, or IP block) in the format board-expert reads,
  optionally with a thin <board>-expert stub skill, a vendor overlay, a <vendor>-board-tools skill,
  or a new spec root in a source tree. Use when the user asks to scaffold, create, or generate a
  board spec, a board expert, or a bring-up reference for a specific board, SoC, or chip family, or
  when board-expert reports that no spec exists. Authoring only: it reads no source and answers no
  hardware questions. Ships the spec, stub, overlay, vendor-skill, and root-marker templates under
  templates/.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Board-spec scaffold (write a new board spec)

You produce **board specs**: the per-hardware files that `board-expert` reads to answer bring-up
questions. One spec per piece of hardware — a board composes an SoC and companion chips, and an SoC's
`instances:` table names the IP blocks it places — plus, when
wanted, a thin `<board>-expert` stub so the harness finds the board by name, a vendor overlay for
private resources, a `<vendor>-board-tools` skill for a vendor's internal tools, or a new spec root in
a source tree. The format, the layers, and the clean-room rules are in `board-expert/SPEC-FORMAT.md`;
read it before writing anything, and do not restate it in what you write.

The worked example to mirror is the `rpi5` set under `board-expert/specs/`: `rpi5.spec.md` (board),
`bcm2712.spec.md` (SoC), `rp1.spec.md` (chip), and the `rpi-expert` stub that points at it.

## What you produce

| Artifact | When | Template |
| --- | --- | --- |
| `<id>.spec.md`, kind `board` / `soc` / `chip` | always; one per piece of hardware that has no spec yet | `templates/board.spec.md`, `soc.spec.md`, `chip.spec.md` |
| `<id>.spec.md`, kind `ip` | an SoC's `instances:` row names an IP block with no spec, or a generic IP spec is asked for | `templates/ip.spec.md` |
| `board-specs.yaml` | the chosen root does not exist yet | `templates/board-specs.yaml` |
| `<board>-expert/SKILL.md` stub | the user wants the board findable by name and callable by consumers | `templates/stub-SKILL.md` |
| `<id>.spec.md` with `overlays:` | private resources for this hardware, vendor or bench-local | `templates/overlay.spec.md` |
| `<vendor>-board-tools/SKILL.md` | a vendor has no generic skill yet for its internal tools | `templates/vendor-board-tools-SKILL.md` |

## Conventions to honor

- **One id everywhere.** The frontmatter `id`, the filename `<id>.spec.md`, the `parts` entries that
  reference it, and the stub's `spec: <id>` line all agree. Ids are kebab-case: `rk3399`, `bcm2711`,
  `jh7110`, `rock5b`. A stub's skill name is `<board>-expert`.
- **Reuse before writing.** If an SoC or chip spec already resolves in any root the user can see,
  reference it in `parts` rather than writing another. Two boards on the same SoC share one SoC spec.
- **Agent-neutral prose.** Refer to "the agent", not to any one product's name.
- **License header: match the target repo's convention.** In this repo every spec, stub, and
  SKILL.md carries exactly `SPDX-FileCopyrightText: 2026 contributors` and
  `SPDX-License-Identifier: Apache-2.0` in an HTML comment immediately *after* the frontmatter,
  never above it — a comment before the frontmatter stops it parsing. A source tree carries whatever
  header its neighbors do.
- **Cache convention.** A board spec names `cache: <short>-resources`; the expert clones under
  `~/src/<short>-resources/`. Pick a short, unambiguous `<short>`. Parts inherit the board's cache
  unless they name their own.
- **Clean-room first.** Every fact carries a provenance tag, at the end of its bullet; anything
  unverified is `TODO (verify on hardware)`; no source excerpts, ever. A spec may end up in the
  target OS tree, so it must already be safe there. Device trees are hardware description, not
  source: you may read them and copy node names, compatibles, and values into a spec as `[DT]`
  facts. Driver and firmware code is source: only the research-fill subagent reads it.
- **Public root, public content.** A spec under a `public` root names nothing private: no internal
  hosts, tools, codenames, or NDA documents. Those go in an overlay under a vendor or local root.

## Steps

1. **Interview for the inputs** (ask only for what you don't already have; one concise batch,
   structured as `board-expert/QUESTIONS.md` prescribes — that catalog is this interview's
   checklist, and a spec that leaves one of its questions unanswered is the spec that will make the
   reader ask later):
   - **Identity:** the kind(s) needed, marketing/board name(s), SoC part number, core topology,
     notable variants and aliases, companion chips, and the **trigger keywords** a question would
     contain.
   - **Root:** where the spec lives. Choices: `board-expert/specs/` in this repo (a board with no home
     tree); an existing root in a source tree (next to the board driver, or its central directory);
     a vendor root; or a new root, in which case you also write `board-specs.yaml` with its layer.
   - **Sources:** repos and refs — vendor/downstream Linux *and* mainline if both carry it; the
     Trusted Firmware-A platform directory; U-Boot; any vendor BSP; firmware/boot blobs. Note the
     highest-value files per repo (board `.dts`, SoC `.dtsi`, console UART driver, irqchip).
   - **Citations:** the authoritative datasheet / TRM / programmer's guide URLs (and public *proxy*
     parts when the exact one is NDA), plus the relevant ARM specs (GIC, PSCI, SCMI, ARM ARM).
   - **Cache:** the `<short>-resources` name.
   - **Quick-facts** (fill what's known; the rest is TODO for the expert or user to confirm on
     hardware). SoC: addressing model, boot chain + entry EL + MMU/cache state + DTB-pointer register
     + secondary-core release, SMP/MPIDR mapping, interrupt controller (version, GICD/GICR/GICC
     addresses, DT interrupt-cells, SPI/PPI INTID base), debug UART (IP, address, IRQ,
     reg-shift/io-width, baud, earlycon, pinmux), timers (freq + PPIs), clocks/power (firmware-owned
     vs OS-managed), GPIO/pinmux banks + syscon, DTB runtime patching. Board: boot media and
     configuration, debug connector and which UART, PMIC, headers. Chip: how it is reached, its
     address window, what it carries. SoC and chip: the `instances:` rows (name, `ip` id, base
     address, interrupt, clocks, role). IP: the standards it implements, the databook or public
     proxy, the programming model at the databook's level, public variants and errata; never an
     instance fact.
   - **Stub, overlay, vendor skill:** wanted or not, and where the stub lives (the skills repo that
     serves this project).
2. **Research-fill the facts (the default when the sources are public).** Spawn a subagent with
   the harness's delegation tool, have it load `os-investigator` plus `board-expert` (so a sibling
   SoC or IP spec is available to it), and ask it to return the addressing model / boot hand-off /
   GIC / UART / timer / clock facts as a clean-room report, each fact tagged, plus ready-to-paste
   `instances:` rows in the format's shape. It may clone into `~/src/<cache>/` as `os-investigator`
   directs. Drop the returned facts into the templates. Driver and firmware code is read only by
   that subagent; you may read device trees yourself (see Conventions). Write TODO stubs instead
   only when the user asks for a skeleton or no public source exists.
3. **Write the spec(s)** from the templates, substituting every `<...>` placeholder. Split facts by
   kind: entry state, the GIC, and the on-SoC UART placement are SoC facts; boot media, the debug
   connector, and the PMIC are board facts; a companion chip's window and contents are chip facts;
   a block's register model and sequences are IP facts, written once and referenced from every
   `instances:` row that places it. Tag every fact; mark anything unverified
   `TODO (verify on hardware)` rather than guessing. Put the tag clause at the end of every bullet
   (`SPEC-FORMAT.md` § Tag rules); a `[doc]` names its page; `[press]` and `[source-observed]`
   carry the TODO. Sibling models go in `variants:` or their own `variant_of` spec
   (`QUESTIONS.md` item 6).
4. **Write the root marker, stub, overlay, and vendor skill** if wanted, from their templates.
   Placeholders only in the vendor templates: the real names belong in the vendor's private repo.
5. **Register.** A spec needs no registration; a stub does. In this repo a stub goes under
   `plugins/driver-porting/skills/<board>-expert/` and its name must appear, backtick-quoted, in:
   the Themes table of the root `README.md` (the `driver-porting` row); the "Which one do I want?"
   table and the "Board experts" list in `plugins/driver-porting/README.md`; and the `board-expert`
   bullet's list of shipped specs in that README, for the new spec ids. The `plugin.json` and
   `marketplace.json` descriptions enumerate the board experts in prose; add the new one.
   `python3 utilities/check-skill-registration.py` confirms the two READMEs and CI runs it on every
   push. CI's checker step and the README's Tests block use `--stubs-from`, which finds every stub
   whose description says "stub over", so they need no edit. A spec in a source tree follows that
   tree's review process.
6. **Check.** Run `python3 <board-expert>/scripts/spec_check.py <root>... --stubs-from <skills dir>`
   over every root the new spec references (a vendor root needs the public root beside it, or its
   overlay targets do not resolve). It enforces `SPEC-FORMAT.md` § *What the checker enforces*:
   required keys per kind, every `parts`, `instances[].ip`, `variant_of`, and `overlays` reference
   resolving, instance `reg`/`irq` shapes, the tag clause at the end of every fact, nothing internal
   under a public root, and every stub's id resolving.
7. **Remind to sync.** If the user's machines link skills from a checkout with a sync tool, tell them
   to re-run it so a new stub is linked; a plugin install picks it up on the next update. Specs in a
   source tree need nothing.
8. **Don't push unprompted.** Stage/commit if asked; follow the repo's push rules.

## Filling guidance

- **Quick-facts are the value.** A spec with vague quick-facts is a link dump. Get the addressing
  model, the entry exception level, and the debug-UART address right first — those brick bring-up if
  wrong and are what investigators reach for most.
- **Cite the datasheet, map with the kernel.** When the SoC has no public datasheet, say so in the
  docs list and note that the device tree is the primary public address map (as `bcm2712` does).
- **Public proxy parts.** If the exact part is NDA, point at the closest publicly documented family
  member or the IP vendor's databook (Synopsys DesignWare, ARM PrimeCell, Cadence GEM, …), and leave
  the NDA document for a vendor overlay.
- **Plain TODOs.** A clearly flagged gap is useful; a confident wrong address is a bring-up trap.

## Quality bar

- One id for the file, the frontmatter, every `parts` reference, and the stub; agent-neutral prose;
  license header per the target repo's convention.
- Required keys present for the kind; every `parts` and `overlays` reference resolves.
- Every quick-fact and gotcha tagged; unverified items flagged, not guessed; no source excerpts.
- Sources name obtainable repos and refs *and* citable datasheets/specs, not just the kernel.
- Nothing internal under a public root.
- A stub, if written, starts its description with the prefix "Board expert for" (the article is
  free: "Board expert for the Raspberry Pi 5" is fine; consumers such as `reference-driver-review`
  match the prefix), says "A stub over the `<id>` board spec" (which is how `--stubs-from` finds
  it), names its spec id in a `` `spec: <id>` `` line, and is registered where its repo requires.
