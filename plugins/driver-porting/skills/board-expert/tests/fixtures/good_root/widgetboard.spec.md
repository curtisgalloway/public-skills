---
kind: board
id: widgetboard
name: Widget Board
triggers: [widget board, widgetboard]
not_triggers: [widget board mini]
aliases: [wb1]
parts: [widgetsoc]
cache: widget-resources
variants:
  - name: Widget Board Pro
    triggers: [widget board pro]
    shares: [soc, parts, console]
    differs: more DRAM
  - name: Widget Board Fold
    triggers: [widget board fold]
    shares: [soc]
    differs: "only the prebuilt tree's README names it"
    tag: source-observed
    source: prebuilt tree README
resources:
  repos:
    - name: linux
      url: https://example.com/linux
      ref: main
      license: GPL-2.0-only
      status: merged
      verified: 2026-09-18
      fetch: ok
      files:
        - arch/arm64/boot/dts/widget/widgetboard.dts
        - {path: arch/arm64/boot/dts/widget/widgetboard-pro.dts, status: unmerged, note: "in the series"}
      note: >-
        A folded note that spans
        two lines.
  series:
    - title: Add Widget Board Pro
      url: https://lore.example/series/
      message_id: 20260918-widget-v1-0@example.com
      target: linux
      status: unmerged
      fetch: blocked
      fetch_via: /raw with a Wget user agent
      files: [arch/arm64/boot/dts/widget/widgetboard-pro.dts]
      note: "the lore HTML is bot-challenged"
  docs:
    - title: Widget store page
      url: https://example.com/store
      access: public
      fetch: partial
      fetch_via: curl
  tools: []
---

# Widget Board

## Orientation

Synthetic.

## Quick-facts

- **Boot media.** An EEPROM. `[doc]` (Widget boot guide)
- **Power.** `TODO (verify on hardware)`: PMIC not recorded.
- **Prose that names a tag.** Every address here is a decompiled-blob `[DT]` fact, which the
  verifier re-derives. `[DT]` (`widgetboard.dtb`, widget-prebuilts)
- **Angle brackets in code.** The tuple is `<type number flags>`. `[DT]` (`widgetboard.dts`)

## Gotchas

- Console is the second UART. `[DT]` (`widgetboard.dts`)
