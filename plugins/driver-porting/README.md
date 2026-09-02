# driver-porting

Skills for writing and reviewing device drivers against source you may or may not be allowed
to copy from: a clean-room pipeline for encumbered source, source-anchored specs and reviews
for source you own, and board experts that supply the per-SoC facts both need.

```
/plugin install driver-porting@public-skills
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
| You need memory maps, boot chains, clocks, or interrupt details for a specific board | `rpi-expert`, `indiedroid-nova-expert` |

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

Board experts are dirty-side roles that `os-investigator` calls into. They supply the per-SoC
map and the sources and datasheets to cite; the method and the no-source-code rule come from
`os-investigator`.

- **`rpi-expert`** — Raspberry Pi 5 and Compute Module 5 (BCM2712 plus the RP1 southbridge):
  memory map and MMIO addresses, device tree, boot chain and exception-level hand-off,
  PSCI/SMP, interrupts, timers, clocks and power, UART/GPIO, PCIe and the RP1.
- **`indiedroid-nova-expert`** — the Indiedroid Nova (same hardware as the 9Tripod Pico PC
  V2.0) and Rockchip RK3588S/RK3588 bring-up generally (Radxa ROCK 5, Orange Pi 5, …): memory
  map, device tree, boot chain, PSCI/SMP, GIC-600, timers, clocks and power (CRU, SCMI, RK806),
  debug UART, GPIO and pinmux via the GRF, PCIe/USB/eMMC.

The Fuchsia-specific skills that consume this pipeline live in
[curtisgalloway/fuchsia-skills](https://github.com/curtisgalloway/fuchsia-skills) and hand
off to these by name.

## Tests

```bash
python3 -m unittest discover -s plugins/driver-porting/skills/os-investigator/tests -v
python3 -m unittest discover -s plugins/driver-porting/skills/cleanroom-implementer/tests -v
```
