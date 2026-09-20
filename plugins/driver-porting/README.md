# driver-porting

Skills for writing and reviewing device drivers against source you may or may not be allowed
to copy from: a clean-room pipeline for encumbered source, source-anchored specs and reviews
for source you own, and board experts that supply the per-SoC facts both need.

```
/plugin install driver-porting@curtisg-skills
```

Antigravity and other harnesses that read skill directories: link the skill you want from
`plugins/driver-porting/skills/<name>` into your skills root.

## Which one do I want?

| Situation | Skill |
| --- | --- |
| The reference driver is GPL, NDA, or otherwise not yours to copy, and you need a driver in a differently licensed OS | `cleanroom-spec` (which drives `os-investigator` and a board expert) |
| The reference driver is yours, or you may copy from it, and you want a spec whose every fact points back at the code | `anchored-peripheral-spec` |
| A driver exists and you want it checked against the upstream, vendor, or original implementation | `reference-driver-review` |
| You are the agent writing code from a clean-room spec | `cleanroom-implementer` |
| You need memory maps, boot chains, clocks, or interrupt details for a specific board | `rpi-expert`, `rpi4-expert`, `indiedroid-nova-expert`, `pixel10-expert`, or `board-expert` for any board with a spec |
| You need a board expert for a board that does not have one yet | `board-spec-scaffold` writes the spec and stub; `board-expert` does its best without one |
| You want a spec checked against every source it cites, or re-checked after the sources moved | `spec-verifier`, for board specs, clean-room driver specs, and anchored specs and reviews alike |

## Clean-room driver porting

Three skills compose into one pipeline for reimplementing a driver in a differently-licensed
OS, splitting the work across contexts so encumbered source never reaches the one that writes
the new code:

- **`os-investigator`** — the dirty-side method: read the original source (Linux, Trusted
  Firmware-A, vendor boot code, device trees) and return hardware facts and mechanism prose,
  never code, every fact tagged by provenance class (databook, standard, device tree,
  source-observed). Triggers whenever someone asks how the kernel or firmware does something,
  whether or not they say "clean room". Ships `scripts/leak_scan.py`, the mechanical leak
  scanner, with tests under `tests/`.
- **`cleanroom-spec`** — orchestration and the wall: the transfer protocol, the independent
  five-check verifier, mandatory scanning, and the evidentiary provenance ledger. Produces a
  per-peripheral spec (Ethernet MAC, UART, GPIO, SD/MMC, USB, display/mailbox, I2C/SPI, …) an
  engineer can implement from scratch. Spec templates live under `templates/`.
- **`cleanroom-implementer`** — the consumer side: standing rules for the implementing agent,
  enforcement (a `PreToolUse` hook, permission deny rules, a restricted subagent definition,
  policy fragments), spec-gap filing, and the session and artifact audit
  (`scripts/cleanroom_hook.py`, `scripts/session_audit.py`, tests under `tests/`).

Enforcement install material targets **Antigravity**: a `PreToolUse` hook in
`<workspace>/.agents/hooks.json`, permission deny rules, a sandboxed `driver-implementer`
subagent in `.agents/agents/`, the `AGENTS.md` standing block, and audits over session
transcripts and task artifacts (`~/.gemini/antigravity/brain/<GUID>/`). The two shipped Python
scripts are harness-neutral: they key off argument names and event fields rather than
tool-name tables, so they also run unchanged under Claude Code with `.claude/` paths.

The `assets/` under `cleanroom-implementer` are install material for *consuming* projects.
They are not this repo's own configuration.

## Source-anchored driver specs

- **`anchored-peripheral-spec`** — the same per-peripheral spec shape as `cleanroom-spec`, for
  driver source you or your organization authored or may otherwise copy from, where the wall
  is not just unnecessary but in the way. Every source-derived fact carries a
  `[src: path:L1-L2 (symbol)]` anchor at a pinned commit, so a reviewer can check the spec
  against the code and the checker can tell which claims need re-reading when the tree moves.
  Ships `scripts/anchor_check.py` (stdlib-only: resolves anchors, renders a claim-vs-source
  review sheet with `--show`, detects and rewrites drift with `--drift REV --rewrite`) and
  `scripts/inventory_check.py` (omissions and value mismatches against the register headers).
  Not a substitute for `cleanroom-spec` on encumbered source: an anchored spec is a derivative
  of its source by design.
- **`reference-driver-review`** — review a driver implementation against a reference
  implementation of the same hardware (the upstream kernel driver, the vendor BSP, the original
  a port was made from) and produce an anchored findings report: missing init steps, wrong
  constants, absent errata workarounds, ordering and timing divergences, each cited to the
  file:line on *both* sides at pinned commits (`[impl:]`/`[ref:]`). Defaults to the driver in
  the current directory; locates the reference via a matching board-expert skill or by asking.
  The reference is evidence, not truth: the databook breaks ties. Reuses
  `anchored-peripheral-spec`'s checkers, so implementation-side anchors get drift tracking as
  fixes land. Output is a review, never driver code.

## Board experts

Board experts are dirty-side roles that `os-investigator` calls into. They supply the per-board map
and the sources and datasheets to cite; the method and the no-source-code rule come from
`os-investigator`. The map itself lives in **board specs**: one Markdown-with-frontmatter file per
board, SoC, or companion chip, composed (a board names its SoC and chips as `parts`) and overlaid
(vendor and bench-local material sits in separate roots and merges in a fixed layer order). A spec
is the clean-side artifact, so it may live in the target OS tree next to the board code it
describes; the reference source stays in the expert's out-of-tree cache.
`board-expert/SPEC-FORMAT.md` is the contract, and `scripts/spec_check.py` (stdlib-only, tests
under `tests/`) enforces it: required keys per kind, every reference resolving, instance shapes, the
tag clause at the end of every fact, nothing internal under a public root, and every stub's id
resolving (`--stubs-from` finds the stubs by their "stub over" sentence).

- **`board-expert`** — the reader. Resolves a spec by id or by the board/SoC names in the question
  across every spec root it can see (its own `specs/`, roots declared by project or vendor skills, a
  root at the checkout, the user's local root), composes and overlays it, clones the sources it
  names into the cache, and answers with `os-investigator`'s method. Best-effort when no spec
  exists, with a suggestion to scaffold one. An IP block (`dwc3`, `pl011`) resolves *anchored*
  through a board's `instances:` table and kernel tree, or *generic* from mainline at head plus the
  public standards. Ships `specs/`, the public root: the `rpi5`, `rpi4`, `indiedroid-nova`, and
  `pixel10` board specs, the `bcm2712`, `bcm2711`, `rk3588s`, and `tensor-g5` SoC specs, the `rp1`
  chip spec, and the `pl011` and `dw-apb-uart` IP specs their instance tables place; `QUESTIONS.md`, the structured
  question catalog and the `Needs decision` protocol every skill here follows instead of guessing;
  and `VENDOR-GUIDE.md`, how a vendor adds overlay roots, wraps internal tools as skills, and keeps
  internal material out of public roots.
- **`rpi-expert`** — Raspberry Pi 5 and Compute Module 5 (BCM2712 plus the RP1 southbridge), a
  stub over the `rpi5` spec: memory map and MMIO addresses, device tree, boot chain and
  exception-level hand-off, PSCI/SMP, interrupts, timers, clocks and power, UART/GPIO, PCIe and the
  RP1.
- **`rpi4-expert`** — Raspberry Pi 4 Model B and the BCM2711 (family includes the Pi 400 and
  Compute Module 4/4S), a stub over the `rpi4` spec: the low- versus high-peripheral memory map, device tree, the boot chain
  from BootROM through the SPI-EEPROM bootloader and `start4.elf` to the armstub, PSCI/SMP across
  4×Cortex-A72, the GIC-400, the PL011 debug UART and the mini-UART trap, GPIO and the BCM2711
  pull registers, GENET Ethernet, EMMC2/SDHCI, and the VL805 USB bridge on PCIe. The BCM2711 ARM
  Peripherals datasheet is public, so it is the citation of record rather than the kernel.
- **`indiedroid-nova-expert`** — the Indiedroid Nova (same hardware as the 9Tripod Pico PC
  V2.0) and Rockchip RK3588S/RK3588 bring-up generally (Radxa ROCK 5, Orange Pi 5, …), a stub over
  the `indiedroid-nova` spec and the `rk3588s` SoC spec it composes: memory
  map, device tree, boot chain, PSCI/SMP, GIC-600, timers, clocks and power (CRU, SCMI, RK806),
  debug UART, GPIO and pinmux via the GRF, PCIe/USB/eMMC.
- **`pixel10-expert`** — the Google Pixel 10 (Tensor G5, codename laguna / `lga`; board
  `frankel`, with the Pixel 10 Pro and Pro XL as variants), a stub over the `pixel10` spec and the
  `tensor-g5` SoC spec it composes: the flat 64-bit memory map, the unmerged mainline device trees
  and the production DTBs as the public map, the closed Android boot chain and boot-image layout,
  PSCI/SMP across Cortex-X4/A725/A520, the GICv3, timers, the DesignWare debug UART, and what is
  and is not publicly established for a handset whose vendor kernel is not published.
- **`board-spec-scaffold`** — write a new board spec (board, SoC, chip, or IP block) in the format
  `board-expert` reads, optionally with a thin `<board>-expert` stub, a vendor overlay, a
  `<vendor>-board-tools` skill for a vendor's internal resources, or a new spec root in a source
  tree: an interview for the hardware's identity, root, sources, citations, cache name, and
  quick-facts, an optional research-fill by an `os-investigator` subagent, and a template for every
  artifact under `templates/`. Its last step is the verification phase. Authoring only; it reads no
  source and answers no hardware questions itself.
- **`spec-verifier`** — re-derive a spec's claims from the sources it cites, in a fresh verifier
  context, and write a verification record outside the spec (`<root>/resources/<id>.verify.md` for
  a board spec; a `resources/` sibling or the project's `docs/provenance/` for the others). One
  procedure with a section per kind: board specs (every tagged fact against its device tree,
  databook, or document; two independent verifiers for the addressing model, entry state, and debug
  UART), anchored specs and reviews (`anchor_check.py` resolves every anchor at the pin, then the
  creating skill's own verifier judges whether the cited lines support each claim; one verdict per
  anchor), and clean-room driver specs (`cleanroom-spec`'s five-check verifier unchanged, then an
  accuracy pass over every `[databook]`/`[standard]`/`[DT]` fact). It never edits a spec; a `FAIL`
  carries the proposed correction and re-running is the loop. The checker reads the record's
  frontmatter: unverified and stale are warnings, a recorded `FAIL` is an error, and
  `--require-verified` makes the warnings errors too.

The Fuchsia-specific skills that consume this pipeline live in
[curtisgalloway/fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills) and hand
off to these by name.

## Evaluating specification quality

The [remaining implementation plan](IMPLEMENTATION-PLAN.md) organizes trial preparation,
paired evaluation, test quality, companion-skill validation, and final verification into
session-sized milestones with explicit dependencies and review gates.

[Faster driver development with evidence we can test](DRIVER-QUALITY.md) explains the problem,
the proposed workflow, and how independent checks could reduce human review while improving
driver quality and test coverage. It is written for programmers new to driver development.

The [evaluation plan](EVAL-PLAN.md) measures both document quality and downstream usability.
The [OS-neutral reconstruction protocol](RECONSTRUCTION.md) defines how isolated implementers
build drivers from generated specs and evaluators compare them with the selected reference.
The [ENC28J60 pilot](evals/enc28j60/README.md) has documentary scoring tools and a paired-run
protocol; paired generation and reconstruction remain pending. Its
[reconstruction run guide](evals/enc28j60/RECONSTRUCTION-RUN.md) lists preparation still needed.
See the repository [glossary](../../GLOSSARY.md) for evaluation terminology.

## Tests

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests -v
python3 -m unittest discover -s plugins/driver-porting/skills/cleanroom-implementer/tests -v
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
python3 plugins/driver-porting/skills/board-expert/scripts/spec_check.py \
  plugins/driver-porting/skills/board-expert/specs \
  --stubs-from plugins/driver-porting/skills
```

Add `--require-verified` to make a missing or stale verification record an error rather than a
warning (CI keeps the default). The checker's last line names the parser it ran. CI has no PyYAML, so it and the plain `python3`
commands above exercise the checker's own subset parser; to exercise the PyYAML path as well, run
the tests and the checker once under a Python that has it, for example
`uv run --with pyyaml python -m unittest discover -s plugins/driver-porting/skills/board-expert/tests`.
