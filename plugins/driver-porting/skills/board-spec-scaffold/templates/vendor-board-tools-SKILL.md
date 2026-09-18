---
name: <vendor>-board-tools
description: >-
  <Vendor>-internal resources for board bring-up: how to reach the internal document portal, code
  search and repositories, lab rigs, and the errata tracker that <vendor>'s board-spec overlays name
  with `via:`; declares the <vendor> overlay roots. Use whenever board-expert resolves a spec with a
  <vendor> overlay, or a hardware question concerns a <vendor> board, SoC, or IP block and internal
  resources apply. Internal only: never installed outside <vendor>.
---

<!-- license header per the vendor repo's convention -->

# <Vendor> board tools

You give `board-expert` access to what <vendor> holds privately. This skill is the *how* for every
<vendor> resource; the per-hardware *what* is in the overlay specs under the roots below. Load this
skill alongside `board-expert` and `os-investigator` in the expert subagent, never in the main agent.

## Overlay roots

One line per root; `board-expert` reads these. The layer comes from each root's `board-specs.yaml`.

- board-spec root: <path in the source tree, for example vendor/<vendor>/board-specs> (layer `product`)
- board-spec root: <absolute path to a checkout of the internal spec repository> (layer `soc-vendor` or `ip-vendor`)

## Classification

- <What may leave this skill's context in a report: facts, addresses, and mechanism prose, cited to
  the internal document by title. What may not: document text, internal hostnames in public
  artifacts.>
- Facts from these roots reach reports tagged with their layer. They are never copied into a
  public-layer spec.

## Document portal

- <URL pattern; how to authenticate; how to search by part number; what to cite (title, revision,
  section).>

## Code search and internal repositories

- <How to check out the internal BSP or kernel; which branch is the product branch; the cache path
  convention.>

## Lab rig

- <How to find the target that corresponds to a board id; how to drive it (serial console, power,
  netboot, screen); which skill or tool wraps it.>

## Errata and bug tracker

- <How to query errata for a part; how to cite an erratum.>

## Install

- Link this skill into the expert's skills root, or install the internal plugin that ships it.
- Optionally add the roots above to `~/.config/board-specs/board-specs.yaml` under `roots:` so they
  are found even when this skill is not loaded.
