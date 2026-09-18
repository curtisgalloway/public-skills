<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Vendor guide: overlay roots, internal tools, and the wall

For an engineer inside an organization that holds material the public specs cannot: NDA databooks,
internal BSP trees, lab rigs, errata trackers. Nothing here assumes you have read the rest of this
repository; `SPEC-FORMAT.md` is the reference when a term below needs its full definition.

## Terms

- **Public spec** — a board, SoC, chip, or IP spec under a root whose layer is `public`. Everything
  in it is citable from the public internet.
- **Overlay** — a file that adds to a public spec (`overlays: <id>`) without copying it. Your
  internal facts, documents, and tools live in overlays.
- **Root** — a directory with a `board-specs.yaml` marker declaring its `layer`. Overlays live under
  your roots; the reader finds roots only through pointers, never by searching.
- **Layer** — the merge position of a root: `public` < `ip-vendor` < `soc-vendor` < `product` <
  `local`. Later layers win on conflicting scalars; lists concatenate; body sections append under a
  heading naming the layer.
- **Vendor skill** — `<vendor>-board-tools`: the one skill that knows how to reach your internal
  resources and declares your roots. The expert loads it beside `board-expert`.
- **`via:`** — the key on a resource entry naming the skill that knows how to reach it.

## 1. Pick your layers

| You are | Layer | Typical overlay targets |
| --- | --- | --- |
| The maker of an IP block (a USB controller, a UART core) | `ip-vendor` | `ip` specs: `dwc3`, `dw-apb-uart` |
| The maker of an SoC | `soc-vendor` | `soc` specs, and `ip` specs for blocks you configured |
| The maker of a product built on someone's SoC, or on your own | `product` | `board` specs, plus `soc` specs if the SoC is yours |
| One engineer's bench | `local` | `board` specs: rig target names, serial adapter, power switch |

One organization can be more than one of these. A phone maker with its own SoC has a `soc-vendor`
root for the SoC and a `product` root for the phones, two markers, two directories, and one vendor
skill that declares both. Do not put everything in one root at the highest layer: the layer is what
lets an IP-vendor overlay and yours compose without either editing the other.

## 2. Lay out a root

```
vendor/<vendor>/board-specs/            any directory you control
  board-specs.yaml                      layer: product
                                        name: <vendor>-product
  pixel-10.spec.md                      overlays: pixel-10
  tensor-g5.spec.md                     overlays: tensor-g5       (only if the SoC is yours: soc-vendor root instead)
```

- One overlay file per spec id. The file carries only `overlays: <id>` and what you add; never copy
  the public spec's content in.
- In a source tree, the root can be the vendor directory itself so the overlay sits next to the
  vendor's board code and lands in the same review.
- Two overlays for the same id in the same layer produce a checker warning and an undefined order.
  Merge them.

## 3. Write the vendor skill

Copy `board-spec-scaffold/templates/vendor-board-tools-SKILL.md` to `<vendor>-board-tools/SKILL.md`
in your internal skills repository, and fill in:

- **Overlay roots.** One `board-spec root: <path>` line per root. Paths are relative to the checkout
  root of the tree that holds them, or absolute for a separate internal spec repository.
- **Document portal.** How to authenticate, how to search by part number, what a citation looks
  like (title, revision, section). The expert cites internal documents by title and section exactly
  as it cites public ones.
- **Code search and repositories.** How to check out the internal BSP or kernel, which branch is
  the product branch, and the cache path convention (`~/src/<cache>/` from the board spec; your
  internal trees go in the same cache under their own subdirectory).
- **Lab rig.** How to find the target for a board id and how to drive it. If the rig has its own
  skill, name it and say nothing else; the overlay's `tools:` entry points at it with `via:`.
- **Errata and bug tracker.** How to query errata for a part; how to cite an erratum.
- **Classification.** See section 5.

The skill's description must say it is internal and must name the vendor, so the harness's skill
matching offers it for your boards and never installs it elsewhere.

## 4. Wrap a tool

A tool is declared in the overlay and driven by a skill. The overlay says the tool exists:

```yaml
tools:
  - kind: bench
    name: lab-pixel10-3
    via: skill:<vendor>-board-tools
    note: serial, power, fastboot; no display capture
```

The skill named by `via:` owns invocation, authentication, and safety rules. `board-expert` never
invents a command line for a tool; it loads the skill and follows it. If that skill is not loaded in
the session, the reader reports the tool as unavailable and continues.

Kinds are free-form. The public conventions are `bench` (a target on a rig: serial console, power,
netboot, screen), `mcp` (an MCP server or tool), and `script` (a path in the tree). Add your own
kinds freely; the reader only cares about `via:`.

## 5. Classify what may leave

The expert runs in a subagent and returns a report. Decide, in the vendor skill, what may appear in
that report:

- **May leave:** hardware facts, addresses, sequences, and mechanism prose, each cited to the
  internal document by title and section. These are what the report is for.
- **May not leave:** document text beyond a phrase, internal hostnames and URLs in any artifact
  that could become public, tool credentials, and anything the document's own classification
  forbids.
- **Tagging:** every fact from your roots reaches the report tagged with its layer, so a downstream
  clean-room verifier can see that a citation is not publicly checkable. Facts from an NDA databook
  keep the `[databook]` tag; the layer says it is internal.
- **The one-way rule:** nothing from a vendor or local root is ever copied into a public-layer spec.
  If a fact turns out to be publicly documented, cite the public document and add it to the public
  spec on its own merits.

## 6. Install and test

1. Link or install `<vendor>-board-tools` wherever the expert subagent's skills come from.
2. Optionally add your roots to `~/.config/board-specs/board-specs.yaml` under `roots:` so they are
   found even in a session where the vendor skill is not loaded.
3. Ask a question that only an overlay can answer, through the orchestrator, and read the report's
   **Spec provenance** block: it must list your overlay file, its layer, and the internal documents
   it cited. If the overlay is missing from that block, the root pointer is wrong; if the facts are
   there but untagged by layer, the merge went wrong. File either as a bug against `board-expert`.

## 7. Coexisting with other vendors

An IP vendor's overlay on `dwc3` and your product overlay on `pixel-10` compose without contact: the
reader resolves the board, its SoC, its instances, and the IP each instance names, then applies every
overlay for every id in that composition in layer order. You never edit their files and they never
edit yours. When both overlay the same id, the higher layer wins on scalars, and both sets of facts
appear in the body under their own layer headings.
