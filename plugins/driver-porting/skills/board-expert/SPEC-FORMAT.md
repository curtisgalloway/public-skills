<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Board spec format

The contract between a **board spec** (the data), `board-expert` (the reader), `board-spec-scaffold`
(the author), and any vendor skill that overlays private material. Every rule the reader relies on is
stated here; the skills point at this file instead of restating it.

## Terms

- **Board spec** — a Markdown file with YAML frontmatter describing one piece of hardware: a board, an
  SoC, a companion chip, or an IP block. Cited facts plus pointers to sources, documents, and tools;
  never source code. Distinct from a *driver spec* (`cleanroom-spec`, `anchored-peripheral-spec`),
  which describes one peripheral's programming model for an implementer.
- **IP spec** — a spec of kind `ip`: one silicon IP block (a PL011 UART, a DesignWare `dwc3` USB
  controller, a GIC-400) independent of any SoC. Its authorities are the IP databook and the public
  standards the block implements; its map is the mainline Linux driver.
- **Instance** — a row in an SoC or chip spec's `instances:` table: one placement of an IP block at
  an address, with its interrupt, clocks, and per-SoC quirks. The IP spec is the binding; the
  instance is the node.
- **Anchored / generic** — the two ways an IP spec resolves. *Anchored*: through a board, so the
  Linux tree is the board's repository at its ref and the instance facts apply. *Generic*: the IP
  spec alone, from mainline Linux at head plus the public standards, with no instance facts.
- **Needs decision** — the report block a subagent-role skill returns when a fork it cannot resolve
  blocks the work. Subagents never ask the user; the orchestrator turns this block into structured
  questions. See `QUESTIONS.md`.
- **Root** — a directory holding a `board-specs.yaml` marker. Every `*.spec.md` below it is a spec.
- **Layer** — a root's position in the merge order: `public`, `ip-vendor`, `soc-vendor`, `product`,
  `local`. Declared in the root marker.
- **Overlay** — a spec file that adds to another spec instead of standing alone (`overlays: <id>`).
  Vendor and bench-local material is always an overlay.
- **Stub** — a short skill named `<board>-expert` whose content is trigger keywords and a spec id. It
  exists so the harness's skill matching finds the board by name and so consumers can call the expert
  by a stable name. Its description starts with the prefix "Board expert for" and contains the
  sentence "A stub over the `<id>` board spec": consumers match the prefix, and the checker's
  `--stubs-from` finds stubs by the sentence.
- **Cache** — the out-of-tree directory `~/src/<cache>/` where the expert clones reference source. The
  cache is the encumbered side of the clean-room wall; the spec is the clean side.
- **Provenance tag** — the class of authority behind a fact. `[databook]`, `[standard]`, `[DT]`, and
  `[source-observed]` are `os-investigator`'s; specs add `[doc]`, `[hardware]`, and `[press]`. The
  classes, with what falls in each:
  - `[databook]` — the IP databook, TRM, or datasheet; cite the section.
  - `[standard]` — a public standard or architecture specification (ARM ARM, GICv3, PSCI, USB, IEEE
    802.3, the 16550 register model, the arm64 boot protocol in `booting.rst`); cite the clause.
  - `[DT]` — a value read out of a device tree. Always followed by a parenthetical naming the file it
    came from and, when that file is not a source `.dts`/`.dtsi` (a decompiled production DTB or an
    entry in a DTBO image), where the blob came from.
  - `[doc]` — a project's or vendor's own published documentation: a vendor's official
    specification page, a platform documentation site, a repository README, a commit message, a
    patch cover letter, or a maintainer's reply on a list. Always followed by a parenthetical naming
    which, so a store page, a platform guide, and a cover letter cannot be confused.
  - `[hardware]` — measured on a live board; say which board and how.
  - `[press]` — third-party press, teardowns, reviews, and marketing claims that appear nowhere in
    the vendor's own documentation (a modem part named only by reviewers, a GPU model, clock speeds
    from a launch article). Allowed in a fact bullet only with `TODO (verify on hardware)`, and
    freely in Orientation prose.
  - `[source-observed]` — established only by code or by the shape of a tree: a driver's behavior,
    a module file name, a kernel version string, a third-party prebuilt tree's file listing. Always
    with `TODO (verify on hardware)`.
- **Series** — a patch series on a mailing list that adds or changes device trees or drivers before
  it is merged. A `resources.series` entry; a map (`[DT]`, `[source-observed]`), never an authority.
- **Variant** — a model of a board that shares the SoC and most facts with a base model (a "Pro"
  phone, a board revision). Listed under `variants:` on the base spec, or a spec of its own with
  `variant_of:` when its board facts differ materially.
- **Verification record** — `<root>/resources/<id>.verify.md`: the verdicts a fresh verifier
  reached when it re-derived every fact bullet from the authority it cites, kept outside the spec so
  no reader spends context on it. Written by `spec-verifier` as the scaffold's last step and on
  demand; the checker reads only its frontmatter. See *Verification*.

## What a spec is, and is not

A spec is the artifact allowed to cross the clean-room wall. It may live in the target OS tree next to
the code it describes, so everything in it must already be safe there: facts cited to a datasheet,
standard, project documentation, or device tree; facts the `cleanroom-spec` verifier has PASSed; facts
measured on hardware; and pointers to where the encumbered source lives. It carries the *where* and
the *what*. The *how* (investigation method, report format, no-source-code rule) belongs to
`os-investigator` and is not repeated in a spec.

A spec is not:

- a driver spec (a per-peripheral programming model for an implementer);
- a place for source excerpts, source-invented identifiers, or unverified extracts;
- a home for private hostnames, internal tools, or NDA documents when its root's layer is `public`.

## Files

### `board-specs.yaml` — the root marker

```yaml
layer: public                 # public | ip-vendor | soc-vendor | product | local
name: driver-porting          # optional; shown in reports
roots: []                     # optional; further roots, relative to this file or absolute
```

A root is found only through a pointer (see *Roots and layers*). The reader never searches a tree for
markers.

### `<id>.spec.md` — a spec

Found by globbing `**/*.spec.md` below a root. Placement under the root is free: next to the driver the
spec describes, so a driver change and its spec update land in one review under the same owners, or in
a central directory. The filename is a convention; the frontmatter `id` is what resolves.

```yaml
---
kind: board                   # board | soc | chip | ip
id: rpi5                      # kebab-case; unique across every root the reader sees
name: Raspberry Pi 5 / Compute Module 5
triggers: [pi 5, raspberry pi 5, rpi5, cm5, compute module 5]
aliases: []                   # optional: other ids this spec answers to
parts: [bcm2712, rp1]         # board (required) and chip (optional): ids this spec composes
cache: rpi5-resources         # <board id>-resources by convention; cloned under ~/src/<cache>/
variants:                     # optional, board only: models that share this spec's facts
  - name: Raspberry Pi 5 (16 GB)
    triggers: [pi 5 16gb]
    shares: [soc, parts, boot, console]
    differs: DRAM size only
resources:
  repos:
    - name: linux-rpi
      url: https://github.com/raspberrypi/linux
      ref: rpi-6.12.y
      license: GPL-2.0-only
      status: merged          # optional: the default for every file below (unmerged | merged)
      verified: 2026-09-18    # optional: the date the URL and ref were last checked
      fetch: ok               # optional: ok | blocked | truncated, for automated fetchers
      files:                  # highest-value paths, relative to the repo root
        - arch/arm64/boot/dts/broadcom/bcm2712-rpi-5-b.dts
        - {path: arch/arm64/boot/dts/google/lga.dtsi, status: unmerged, note: "lands with the series"}
      note: "the real Pi 5 device trees and drivers; read for behavior, cite the datasheet"
  series:                     # optional: unmerged patch series that are the public map
    - title: Add Laguna SoC and boards
      url: https://lore.kernel.org/linux-arm-kernel/<message-id>/
      message_id: <message-id>
      target: linux-mainline  # the repo entry it patches
      status: unmerged        # unmerged | merged | superseded
      files: [arch/arm64/boot/dts/google/lga.dtsi]
      note: "a map, never cite: true; the canonical lore URL is bot-challenged, see Paths and URLs"
  docs:
    - title: RP1 peripherals datasheet
      url: https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf
      access: public          # public | internal
      cite: true              # a clean-room authority: cite it, not the kernel
      verified: 2026-09-18
      fetch: ok
  tools: []                   # usually filled by overlays; see Tools
---
```

`cite: true` marks a clean-room authority: cite it, not the kernel. `cite: false` or absent means
context or map only; the reader never cites such an entry as authority. A `series` entry can never
be `cite: true`. `status` on a repo or series entry says whether the listed `files` exist at the
`ref` yet (`unmerged` when they do not) and is the default for every file it lists; a `files:`
entry may also be a mapping `{path, status, note}` when one repository carries some of the listed
files and not others (mainline may carry a binding and a driver while the SoC's `.dtsi` is still on
the list). `verified` and `fetch` record when a URL was last checked and whether an automated fetcher
could read it; they make link rot detectable and are optional.

**Quoting.** Both parsers the checker uses reject an unquoted scalar that contains `: ` (a colon
followed by a space) or ends with a colon; a `#` after a space starts a comment; a comma inside a
flow mapping (`{...}`) splits the entry. Double-quote any `note`, `title`, or `name` that contains
one of those, as the examples do.

An SoC or chip spec also carries an `instances:` table, one row per placement of an IP block:

```yaml
instances:
  - name: uart10              # the instance name as the device tree or datasheet calls it
    ip: pl011                 # id of the IP spec (the binding)
    reg: 0x107d001000         # CPU-physical base as an integer, or null with a TODO in `note`
    irq: {kind: SPI, number: 121, intid: 153, trigger: level-high, note: "shared by all PL011s"}
                              # null, or a mapping: kind SPI | PPI | extended, integer number,
                              # optional integer intid, optional trigger and note strings (quoted)
    clocks: [clk_uart]        # DT clock names as the SoC's device tree uses them
    role: debug console       # optional: what this instance is for
    note: "quirks, or TODO (verify on hardware): what is missing"   # quote it: it holds a colon
  - name: cli12_uart
    ip: dw-apb-uart
    reg: 0x3a352000
    irq: {kind: extended, number: 4, parent: gia_lsio, note: "GIA aggregator line, not a GIC SPI"}
```

`irq.kind` is `SPI` or `PPI` when the line goes to the GIC: `number` is the DT interrupt number and
`intid` (optional) the resulting INTID (`32 + number` for an SPI, `16 + number` for a PPI). It is
`extended` when the line goes to a secondary controller or aggregator (`interrupts-extended` in the
DT): `parent` names that controller by its DT label, `number` is the line on that parent, and
`intid` is absent; the parent's own GIC line, if known, goes in `note`.

Keys by kind:

| Key | board | soc | chip | ip | overlay |
| --- | --- | --- | --- | --- | --- |
| `kind`, `id`, `name`, `triggers` | required | required | required | required | not used |
| `parts` | required | no | optional | no | no |
| `instances` | no | required (may be empty) | recommended | no | optional |
| `variants`, `variant_of` | optional | no | no | no | no |
| `cache` | required | recommended | optional | recommended | no; inherited |
| `resources` | optional | optional | optional | required | optional |
| `overlays` | no | no | no | no | required |

**Variants.** A model that shares the SoC and most board facts with a base model is a row under
the base spec's `variants:` (`name`, `triggers`, `shares`: which fact groups apply, `differs`: one
line). A model whose board facts differ materially (another SoC stepping, another console path,
another PMIC) is a board spec of its own with `variant_of: <base id>`, carrying only what differs
and pointing at the base for the rest. `triggers` match by substring, so "pixel 10" also matches a
question about a "Pixel 10 Pro"; when a question matches a variant's triggers, or the base's
triggers with a variant name present, the reader treats it as a `Needs decision` between the base
and the variant (`QUESTIONS.md` item 1).

Body: fixed `##` headings per kind. The templates under `board-spec-scaffold/templates/` carry the
exact list; in short:

- **board** — `Orientation`; `Quick-facts` covering what is on the board and how it is wired (which SoC
  and companion parts, boot media and boot configuration, the debug connector and which UART it is,
  power and PMIC, headers and board-level GPIO); `Gotchas`.
- **soc** — `Orientation`; `Quick-facts` covering the addressing model, boot chain and entry state, SMP
  topology, interrupts, debug UART, timers, clocks and power, GPIO and pinmux, DTB runtime patching;
  `Gotchas`.
- **chip** — `Orientation`; `Quick-facts` covering how the chip is reached, its address window, and
  what it carries; `Gotchas`.
- **ip** — `Orientation`; `Standards and databook` (which public standards the block implements and
  which databook or public proxy documents its registers); `Programming model` (register map
  organization, the init / reset / teardown sequences at the level of the databook, DMA and
  interrupt model); `Known variants and quirks` (IP versions, configuration options an SoC may set,
  errata that are public); `Gotchas`. No instance facts: those belong in the SoC spec's
  `instances:` row.

**Tag rules.** Every bullet in a fact section (`Quick-facts`, `Gotchas`, and for an IP spec
`Standards and databook`, `Programming model`, `Known variants and quirks`) ends with its **tag
clause**: one or more tags, each optionally followed by a parenthetical citation, then at most one
closing sentence that starts with `TODO (verify on hardware)`. A tag in the middle of the prose does
not count; put the facts first and the tags last.

```
- **Debug UART.** PL011 `uart10` at `0x10_7D00_1000`, left enabled by firmware. `[DT]`
  (`bcm2712.dtsi`), `[databook]` (DDI 0183). `TODO (verify on hardware)`: the IRQ number.
```

- `[source-observed]` and `[press]` facts must carry `TODO (verify on hardware)`.
- `[doc]` is always followed by a parenthetical naming the page or document, so a store page, a
  platform guide, and a cover letter cannot be confused.
- `[DT]` is always followed by a parenthetical naming the file the value came from (`bcm2712.dtsi`,
  and the node when it helps) and, when the file is a decompiled production DTB or a DTBO entry
  rather than a source `.dts`/`.dtsi`, where the blob came from (`lga-b0.dtb` from a named public
  prebuilt tree). A value from a mailing-list `.dtsi` and one from a shipped blob are both `[DT]`;
  the parenthetical is what tells them apart.
- A **gap bullet** is one whose text, after the optional bold lead-in, starts with
  `TODO (verify on hardware)`; it records what is missing and carries no tag:
  `- **Power.** `TODO (verify on hardware)`: the PMIC part is not recorded here yet.`

### Overlays

```yaml
---
overlays: rpi5                # the id this file adds to
resources:
  docs:
    - title: <internal document>
      url: <internal URL>
      access: internal
      via: skill:<vendor>-board-tools     # the skill that knows how to reach it
  tools:
    - kind: bench
      name: <target name on the lab rig>
      via: skill:<vendor>-board-tools
---
```

The body uses the same headings as the spec it overlays. Merging appends each overlay section under a
sub-heading naming the layer and root, so a reader can see where every fact came from.

## Roots and layers

Pointers to roots come from exactly four places. The reader unions them and never walks a tree:

1. `board-expert`'s own `specs/` directory (layer `public`: boards with no home tree, and examples).
2. Any loaded skill that declares a root with one line in its body:
   `board-spec root: <path>` (relative to the checkout root, or absolute). A project skill that
   describes a source tree declares that tree's public root; a vendor skill declares its vendor roots.
3. `board-specs.yaml` at the root of the current checkout, if present. The checkout root is the top of
   the current git checkout, or the directory holding the tree's multi-repository marker when the
   project skill names one.
4. `~/.config/board-specs/board-specs.yaml`, if present (normally layer `local`).

Any marker may list further roots under `roots:`; those are added the same way.

Merge order is by layer, never by skill load order: `public` < `ip-vendor` < `soc-vendor` < `product`
< `local`. Within one layer, roots merge in pointer order (1 to 4 above). Two overlays for the same id
in the same layer is a checker warning.

Merge rules:

- Composition first, then overlays: a board's `parts` are resolved recursively, and every id in the
  composition receives its own overlays.
- Frontmatter lists (`resources.*`, `triggers`, `aliases`) concatenate; a later entry with the same
  `name`, `title`, or `url` replaces the earlier one.
- Frontmatter scalars: later wins. `id`, `kind`, and `parts` cannot be overridden.
- Body: each overlay `##` section is appended under the matching heading of the target, as
  `### Overlay: <layer> (<root name>)`.

## Resolution

Given a question, the reader finds the spec by:

1. A spec id handed to it by a stub or by the orchestrator (`spec: rpi5`, `ip: dwc3`, or both).
2. Otherwise, matching the board, SoC, chip, and IP names in the question against `triggers` and
   `aliases` across every root. A match on an SoC or chip without a board is still a hit; the report
   says the board-level facts are absent.
3. Otherwise, no spec: `board-expert` does its best from public sources, labels the report spec-less,
   and suggests `board-spec-scaffold`.

An IP spec resolves in one of two modes, and the report names which:

- **Anchored** (`spec: <board>` and `ip: <id>`, or an IP named in a question about a board): the
  reader composes the board, finds the `instances:` rows whose `ip` matches, and uses the board's
  Linux repository at its `ref` as the map. If several instances match and the question does not
  say which, that is a `Needs decision`. Mainline is still read for provenance; both commits go in
  the report. A fact present only in the board's tree is tagged `[source-observed]` with the tree
  named, because it may be a vendor addition rather than the IP's behavior.
- **Generic** (`ip: <id>` alone): the IP spec's own repository entry is the map, by default
  `torvalds/linux` at head with the commit actually read recorded in the report. A caller may pin
  `ref:`. The public standards and databook in the IP spec's `docs` are the authority. The report
  carries no instance facts and says so.

When the question is under-specified in a way that changes the answer (which board variant, which
instance, which tree, anchored or generic), the reader does not guess. It returns a `Needs decision`
block per `QUESTIONS.md`, and the orchestrator asks.

## Paths and URLs

- A path inside a spec is relative to the checkout that contains the spec. A project may use its own
  label convention (for example a `//src/...` prefix) when its project skill defines it.
- Out-of-tree material is a URL plus, for repositories, the `cache` it is cloned under.
- Nothing in a spec points into a cache by absolute path; caches are per machine.
- Arm documents are cited by id (`DDI 0183`, `IHI 0069`, `DEN 0022`); the document id is the
  citation. `developer.arm.com/documentation/<id>/latest` is the citation form to write; it now
  redirects to `support.arm.com/documentation/<id>/latest`, a portal that automated fetchers cannot
  read. Record `fetch: blocked` on such an entry rather than dropping the URL or inventing another.
- Mailing-list series are cited by their canonical `lore.kernel.org/<list>/<message-id>/` URL, whose
  HTML form is bot-challenged. Record that URL with `fetch: blocked` and a `note` naming the form
  that does work: the `/raw` suffix for one message, `/t.mbox.gz` for the whole thread, fetched
  with a `Wget` user agent. Do not substitute a mirror's URL for the canonical one; a mirror may go
  in `note`.

## Verification

A spec is written once by an author who read the sources as they went. Verification is the separate
pass that re-derives every fact bullet from the authority its tag clause cites, in a fresh context
that never saw the author's reasoning, and records the result **outside the spec**. The procedure is
`spec-verifier` § Board specs (the one statement of it; the scaffold runs it as its last step and it
runs again on demand). This section fixes only what the format and the checker rely on.

- **Location.** `<root>/resources/<id>.verify.md`, in a `resources/` directory beside the root
  marker, one file per spec, overlays included under their own root. It is not a spec: the reader
  globs `*.spec.md` only and loads nothing from `resources/`. `board-expert` reports a spec's
  verification status from the record's **frontmatter only**.
- **Frontmatter.** `spec` (the id), `spec_file` (relative to the root), `spec_sha256` (the spec
  file's SHA-256 when the record was written), `verified` (ISO date), `verifier` (free text: which
  agent and harness), `sources` (a list of `{name, commit | url, fetch}` for every repository,
  series, and document actually consulted), and `summary` (`{pass, fail, unverifiable, gap}`,
  integers that equal the verdict lines in the body).
- **Body.** One line per fact bullet, keyed `<Section>/<ordinal> "<bold lead-in>"` (1-based,
  top-level bullets only), never by line number: `PASS` with what was compared against what; `FAIL`
  with the discrepancy and the proposed correction; `UNVERIFIABLE` with the reason; `GAP` for a
  TODO-only bullet. `instances:` rows are keyed `instances/<name>`. No source is reproduced.
- **Staleness.** Any edit to the spec file changes its hash, so the record is stale until the phase
  runs again. Stale is a fact about the record, not a judgment of the edit.
- **What the checker does with it.** No record: warning `unverified`. Record whose `spec_sha256`
  differs from the file: warning `verification stale`. Record whose `summary.fail` is not zero:
  error. A record with a malformed frontmatter: error. `--require-verified` turns the two warnings
  into errors, for a root whose policy is that nothing unverified lands. CI keeps the default so a
  new spec can merge before its first verification, but a failing or stale record never can.

## Tools

`resources.tools` entries are declarative: what exists and which skill knows how to drive it. The
reader does not invent invocation syntax; it loads the `via:` skill and follows it. Kinds are
free-form; the shipped conventions are `bench` (a target on a lab rig: serial console, power, netboot,
screen), `mcp` (an MCP server or one of its tools), and `script` (a path in the tree). When the `via:`
skill is not loaded, the reader reports the tool as unavailable and continues.

## Clean-room rules for spec content

These are `os-investigator`'s caching rule applied to a file that may sit in the target tree:

- Only facts that are datasheet-, standard-, documentation-, or DT-cited, verifier-PASSed, or
  measured on hardware belong in a spec. `[source-observed]` and `[press]` are allowed only with
  `TODO (verify on hardware)`.
- **Device-tree content is hardware description, not source.** Node names, labels, `compatible`
  strings, property names, and values (addresses, interrupt tuples, clock names, pin groups) are
  hardware facts, tagged `[DT]`, and may be read from a device tree and written into a spec by the
  spec's author directly. Driver and firmware *code* is different: only the research subagent reads
  it, and it returns facts and mechanism prose, never excerpts.
- No source excerpts, no source-invented identifiers (function, struct, and variable names from
  driver code), no reconstructed file organization.
- An overlay in a vendor layer may cite NDA documents. Facts from it reach the report tagged with
  their layer, so the clean-room verifier can see that a citation is not publicly checkable. They are
  never copied into a public-layer spec.
- A public-layer root contains no `access: internal` entry, no `via:` naming a private skill, and no
  private hostname. The public-skills repository's privacy rules apply to every public root.

## What the checker enforces

`board-expert/scripts/spec_check.py <root>... [--stubs-from <skills dir>] [--stub SKILL.md]
[--public-skill NAME] [--require-verified]` fails on:

- frontmatter missing a key its kind requires, an unknown `kind` or `layer`, or a duplicate `id`;
- a `parts`, `overlays`, `variant_of`, or `instances[].ip` reference that resolves to nothing
  across the given roots, or an `ip` spec with no `docs` entry marked `cite: true`;
- an `instances:` row whose `reg` is not an integer or null, or whose `irq` is not null or a
  mapping with `kind` (SPI | PPI | extended) and an integer `number`; an `extended` irq without
  `parent`, or a SPI/PPI irq with one; a `variants:` entry without a `name`;
- a `series` entry with `cite: true`; a `fetch` value other than ok | blocked | truncated; a
  `status` other than unmerged | merged | superseded, on an entry or on one of its `files`;
- `access: internal`, or a `via:` naming a skill outside the public set, under a `public` root;
- a fact bullet that does not end with its tag clause, a `[source-observed]` or `[press]` bullet
  without `TODO (verify on hardware)`, or a `[doc]` or `[DT]` without a parenthetical naming its
  source;
- a stub whose `spec: <id>` does not resolve. `--stubs-from` finds every `*/SKILL.md` under a
  skills directory whose frontmatter says "stub over", so CI cannot forget one;
- a verification record (`<root>/resources/<id>.verify.md`) whose frontmatter is malformed or whose
  `summary.fail` is not zero; with `--require-verified`, also a spec with no record or with a stale
  one.

It warns, without failing, on two overlays for one id in one layer, on a part whose `cache`
differs from its board's, on a spec with no verification record (`unverified`), and on a record
whose `spec_sha256` no longer matches the spec (`verification stale`). It is stdlib-only: PyYAML when available, otherwise its own parser for the
format's YAML subset, and its last line says which one ran (`parser: pyyaml` or `parser: subset`).
The two agree on the quoting traps above by construction. It does not check URL reachability. CI has
no PyYAML, so it runs the subset parser; run the checker once under a Python that has PyYAML (for
example `uv run --with pyyaml python ...`) to exercise the other path.

## Related documents

- `QUESTIONS.md` — the question catalog and the `Needs decision` protocol shared by every skill
  that produces or consumes specs.
- `VENDOR-GUIDE.md` — how a vendor sets up overlay roots, wraps internal tools as skills, and keeps
  internal material out of public roots.
- `../spec-verifier/SKILL.md` — the verification procedure for every spec kind, with the board-spec
  section this format's *Verification* section points at.
