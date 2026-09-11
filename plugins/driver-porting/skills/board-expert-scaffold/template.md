<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Board-expert SKILL.md template

Write this to `plugins/driver-porting/skills/<slug>/SKILL.md`, replacing every `<...>` token. Keep
the **fixed** sections ("How to run this skill", "Method and constraints live in os-investigator",
"Report") essentially verbatim — they are the same for every board expert. Fill the **variable**
sections (sources, quick-facts, gotchas) from the interview/research. Keep the SPDX comment where it
is, after the frontmatter; drop it only if the target repo carries no license headers.

````markdown
---
name: <slug>
description: >-
  Board expert for the <Board Display Name> (<SoC part number><, variants>): the board-specific map
  of MMIO addresses, the memory map, the boot chain and exception-level hand-off, interrupts, timers,
  clocks/power, debug UART, GPIO/pinmux, source repos, and datasheets/TRM for bring-up work. Trigger
  whenever "<keyword1>", "<keyword2>", or "<keyword3>" appears in a hardware or low-level software
  question, even if Linux isn't mentioned. Pairs with `os-investigator`, which supplies the
  investigation method and the clean-room no-source-code rule.
---

<!--
SPDX-FileCopyrightText: <year> contributors
SPDX-License-Identifier: Apache-2.0
-->

# <Board Display Name> Expert (<SoC> <+ notable companion chip>)

<One-paragraph orientation: what the board/SoC is, the core topology, the standout architectural facts
an investigator must hold (where peripherals sit, who owns clocks, what's on-SoC vs off-SoC).>

## How to run this skill (delegate; don't inline)

**<slug> is a *subagent* role.** Everything below — cloning sources, reading the cache, walking driver
code — is written for the agent that *is* the expert. If you are the main/orchestrating agent, do
**not** execute this skill body inline: **spawn a subagent, have it load this skill, and pass it the
question.** Only that subagent clones/reads/manages `~/src/<short>-resources`. The main agent never
touches the cache, never reads GPL source, and never micromanages the cache in the subagent's prompt
(no paths, no `git`/`curl`/`ls` steps — the expert handles its own resources). The main agent's entire
job is: ask the question → receive clean-room facts back.

This split is the whole point. Letting the main agent (which writes the differently-licensed target-OS
code) run the skill body inline would pull GPL source into its context and destroy the clean-room
boundary. When in doubt, delegate.

## Method and constraints live in `os-investigator`

**Load and follow the `os-investigator` skill** for the investigation method, the report format, and —
non-negotiably — the **clean-room discipline: return hardware facts and mechanism descriptions in your
own words, never source code**, even if asked to paste it. This board skill supplies the *where* and
*what* (sources, addresses, quirks); `os-investigator` supplies the *how*. If for any reason that skill
isn't loaded, still apply the one rule that matters most: **no source code in the output** — describe
behavior, give addresses/sequences, and link the human to the upstream file instead.

---

## Local resource cache: `~/src/<short>-resources`

Clone and cache all <board> reference material (Linux tree, TF-A, datasheets, fetched source files)
under **`~/src/<short>-resources/`**. Reuse what's already there before re-cloning or re-fetching.

**This cache is for the <slug> agent ONLY.** The main agent must not read files in
`~/src/<short>-resources` directly — it asks <slug>, which returns clean-room facts (no source code).
Keeping the cache behind this skill is what preserves the clean-room boundary.

## Sources to clone and keep locally (into `~/src/<short>-resources`)

**Linux — <vendor/downstream and/or mainline>:**
- Repo: `<repo URL>` (branch `<branch>`). `<git clone command into the cache dir>`
- Highest-value files (raw, on `<branch>`):
  - `<board .dts URL>`
  - `<SoC .dtsi / pinctrl .dtsi URLs>`
  - `<console UART driver path>` (read for *behavior* only); `<irqchip driver path>`; `<clock driver>`
  - arm64 entry-state contract: `.../Documentation/arch/arm64/booting.rst`

**Boot / firmware:**
- Trusted Firmware-A (BL31 = EL3 runtime; PSCI<, and SCMI server if applicable>): `<TF-A repo>` → `<plat dir>`
- U-Boot (BL33): `<U-Boot repo>`
- <Vendor prebuilt DDR-init / BL31 blobs, if the board needs them>: `<repo>`

**Datasheets & specs (cite these, not the kernel):**
- **<Primary TRM/datasheet>** — `<URL or mirror>`. <Note NDA status + public proxy part if relevant.>
- The debug UART is a <16550/PL011/...>-compatible <IP>; <which databook/TRM documents it>.
- ARM specs: <GIC architecture (IHI ...)>; PSCI (DEN 0022)<; SCMI (DEN 0056)>; ARMv8-A ARM
  (exception levels, generic timer, MMU).

---

## Board quick-facts (orient every investigation)

<Fill each bullet from research; mark unverified items `TODO (verify on hardware)`. Drop bullets that
don't apply, but cover at least these dimensions:>

- **Addressing model.** <Flat vs high window; the `#address-cells`/`#size-cells` at root and on the
  peripheral bus; any `ranges` translation trap; on-SoC peripheral window; whether there's an off-SoC
  I/O chip / southbridge across PCIe. Give a worked example address (e.g. the debug UART).>
- **Boot chain & entry state.** <BootROM → ... → kernel; the entry exception level, MMU/cache state,
  DTB-pointer register; secondary-core release mechanism (PSCI `CPU_ON` vs spin-table).>
- **SMP topology.** <Core count, big.LITTLE clusters, the cpu `reg` → MPIDR affinity mapping, boot core.>
- **Interrupts.** <GIC version; GICD/GICR/GICC addresses; DT `#interrupt-cells`; SPI→INTID and
  PPI→INTID base; GICv3 system-register/redistributor notes if applicable.>
- **Debug UART / console.** <IP type; base address; IRQ; `reg-shift`/`reg-io-width`; default baud;
  `earlycon=` string; the TX-ready flag bit; pinmux/IOMUX requirement.>
- **Timers.** <Arch timer frequency (read `CNTFRQ_EL0`, don't hard-code); the secure/phys/virt/hyp
  PPIs; any on-SoC timer block.>
- **Clocks / power.** <Firmware-owned (mailbox) vs OS-managed (CRU/SCMI/PMIC); what bringing a
  peripheral up requires (ungate clock, deassert reset); the PMIC part.>
- **GPIO / pinmux.** <Bank addresses; the syscon/GRF used for IOMUX/drive/pull; the pinctrl compatible.>
- **DTB runtime patching.** <What firmware/BL31 fills in (`/memory`, `/chosen`, PSCI node,
  reserved-memory); parse the live DTB rather than trusting the static `.dts`.>

---

## Common gotchas (<board>-specific)

<The deviations from common assumptions that bite during bring-up — wrong peripheral base region,
GICv3-not-GICv2, console IP confusion, clocks the OS must program itself, mandatory firmware blobs,
entry EL, etc. Two to seven bullets.>

---

## Report

Produce the report in the format defined by `os-investigator`, ending with the clean-room attestation.
This skill's job is to make sure the addresses, sources, and quirks above are reflected accurately —
and that no <SoC> driver source ends up in the output.
````
