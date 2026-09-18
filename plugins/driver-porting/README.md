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
| You need memory maps, boot chains, clocks, or interrupt details for a specific board | `rpi-expert`, `rpi4-expert`, `indiedroid-nova-expert`, or `board-expert` for any board with a spec |
| You need a board expert for a board that does not have one yet | `board-spec-scaffold` writes the spec and stub; `board-expert` does its best without one |

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
  public standards. Ships `specs/`, the public root: the `rpi5`, `rpi4`, and `indiedroid-nova`
  board specs, the `bcm2712`, `bcm2711`, and `rk3588s` SoC specs, the `rp1` chip spec, and the
  `pl011` and `dw-apb-uart` IP specs their instance tables place; `QUESTIONS.md`, the structured
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
- **`board-spec-scaffold`** — write a new board spec (board, SoC, chip, or IP block) in the format
  `board-expert` reads, optionally with a thin `<board>-expert` stub, a vendor overlay, a
  `<vendor>-board-tools` skill for a vendor's internal resources, or a new spec root in a source
  tree: an interview for the hardware's identity, root, sources, citations, cache name, and
  quick-facts, an optional research-fill by an `os-investigator` subagent, and a template for every
  artifact under `templates/`. Authoring only; it reads no source and answers no hardware questions
  itself.

The Fuchsia-specific skills that consume this pipeline live in
[curtisgalloway/fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills) and hand
off to these by name.

## Tests

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests -v
python3 -m unittest discover -s plugins/driver-porting/skills/cleanroom-implementer/tests -v
python3 -m unittest discover -s plugins/driver-porting/skills/board-expert/tests -v
python3 plugins/driver-porting/skills/board-expert/scripts/spec_check.py \
  plugins/driver-porting/skills/board-expert/specs \
  --stubs-from plugins/driver-porting/skills
```
