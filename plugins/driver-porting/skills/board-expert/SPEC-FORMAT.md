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
  SoC, or a companion chip. Cited facts plus pointers to sources, documents, and tools; never source
  code. Distinct from a *driver spec* (`cleanroom-spec`, `anchored-peripheral-spec`), which describes
  one peripheral's programming model for an implementer.
- **Root** — a directory holding a `board-specs.yaml` marker. Every `*.spec.md` below it is a spec.
- **Layer** — a root's position in the merge order: `public`, `ip-vendor`, `soc-vendor`, `product`,
  `local`. Declared in the root marker.
- **Overlay** — a spec file that adds to another spec instead of standing alone (`overlays: <id>`).
  Vendor and bench-local material is always an overlay.
- **Stub** — a short skill named `<board>-expert` whose content is trigger keywords and a spec id. It
  exists so the harness's skill matching finds the board by name and so consumers can call the expert
  by a stable name.
- **Cache** — the out-of-tree directory `~/src/<cache>/` where the expert clones reference source. The
  cache is the encumbered side of the clean-room wall; the spec is the clean side.
- **Provenance tag** — the class of authority behind a fact. `[databook]`, `[standard]`, `[DT]`, and
  `[source-observed]` are `os-investigator`'s; specs add `[doc]` (a project's own public
  documentation, such as Trusted Firmware-A platform pages or a vendor's documentation site; cite the
  page) and `[hardware]` (measured on a live board; say which).

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
kind: board                   # board | soc | chip
id: rpi5                      # kebab-case; unique across every root the reader sees
name: Raspberry Pi 5 / Compute Module 5
triggers: [pi 5, raspberry pi 5, rpi5, cm5, compute module 5]
aliases: []                   # optional: other ids this spec answers to
parts: [bcm2712, rp1]         # board (required) and chip (optional): ids this spec composes
cache: rpi5-resources         # reference material is cloned under ~/src/<cache>/
resources:
  repos:
    - name: linux-rpi
      url: https://github.com/raspberrypi/linux
      ref: rpi-6.12.y
      license: GPL-2.0-only
      files:                  # highest-value paths, relative to the repo root
        - arch/arm64/boot/dts/broadcom/bcm2712-rpi-5-b.dts
      note: the real Pi 5 device trees and drivers; read for behavior, cite the datasheet
  docs:
    - title: RP1 peripherals datasheet
      url: https://datasheets.raspberrypi.com/rp1/rp1-peripherals.pdf
      access: public          # public | internal
      cite: true              # a clean-room authority: cite it, not the kernel
  tools: []                   # usually filled by overlays; see Tools
---
```

Keys by kind:

| Key | board | soc | chip | overlay |
| --- | --- | --- | --- | --- |
| `kind`, `id`, `name`, `triggers` | required | required | required | not used |
| `parts` | required | not yet (IP specs come later) | optional | no |
| `cache` | required | recommended | optional | no; inherited |
| `resources` | optional | optional | optional | optional |
| `overlays` | no | no | no | required |

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

Every fact in `Quick-facts` and `Gotchas` carries a provenance tag. A fact with no public authority is
`[source-observed]` and must also say `TODO (verify on hardware)`. A bullet that records only a gap
(`TODO (verify on hardware)` and nothing else) is not a fact and carries no tag.

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

1. A spec id handed to it by a stub or by the orchestrator (`spec: rpi5`).
2. Otherwise, matching the board, SoC, and chip names in the question against `triggers` and
   `aliases` across every root. A match on an SoC or chip without a board is still a hit; the report
   says the board-level facts are absent.
3. Otherwise, no spec: `board-expert` does its best from public sources, labels the report spec-less,
   and suggests `board-spec-scaffold`.

## Paths and URLs

- A path inside a spec is relative to the checkout that contains the spec. A project may use its own
  label convention (for example a `//src/...` prefix) when its project skill defines it.
- Out-of-tree material is a URL plus, for repositories, the `cache` it is cloned under.
- Nothing in a spec points into a cache by absolute path; caches are per machine.

## Tools

`resources.tools` entries are declarative: what exists and which skill knows how to drive it. The
reader does not invent invocation syntax; it loads the `via:` skill and follows it. Kinds are
free-form; the shipped conventions are `bench` (a target on a lab rig: serial console, power, netboot,
screen), `mcp` (an MCP server or one of its tools), and `script` (a path in the tree). When the `via:`
skill is not loaded, the reader reports the tool as unavailable and continues.

## Clean-room rules for spec content

These are `os-investigator`'s caching rule applied to a file that may sit in the target tree:

- Only facts that are datasheet-, standard-, documentation-, or DT-cited, verifier-PASSed, or
  measured on hardware belong in a spec. `[source-observed]` is allowed only with `TODO (verify on
  hardware)`.
- No source excerpts, no source-invented identifiers, no reconstructed file organization.
- An overlay in a vendor layer may cite NDA documents. Facts from it reach the report tagged with
  their layer, so the clean-room verifier can see that a citation is not publicly checkable. They are
  never copied into a public-layer spec.
- A public-layer root contains no `access: internal` entry, no `via:` naming a private skill, and no
  private hostname. The public-skills repository's privacy rules apply to every public root.

## What the checker enforces

`board-expert/scripts/spec_check.py <root>...` is not shipped yet. When it is, it fails on:

- frontmatter missing a key its kind requires, an unknown `kind` or `layer`, or a duplicate `id`;
- a `parts` or `overlays` reference that resolves to nothing across the given roots;
- `access: internal`, or a `via:` naming a skill outside the public set, under a `public` root;
- a `Quick-facts` or `Gotchas` bullet without a provenance tag (a bullet that is only a
  `TODO (verify on hardware)` gap is exempt), or `[source-observed]` without
  `TODO (verify on hardware)`;
- a stub whose spec id does not resolve.

Until then, review a new spec against this list by hand.
