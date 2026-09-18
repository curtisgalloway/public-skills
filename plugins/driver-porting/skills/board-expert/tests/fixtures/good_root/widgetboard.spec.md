---
kind: board
id: widgetboard
name: Widget Board
triggers: [widget board, widgetboard]
parts: [widgetsoc]
cache: widget-resources
variants:
  - name: Widget Board Pro
    triggers: [widget board pro]
    shares: [soc, boot, console]
    differs: more DRAM
resources:
  repos:
    - name: linux
      url: https://example.com/linux
      ref: main
      license: GPL-2.0-only
      files:
        - arch/arm64/boot/dts/widget/widgetboard.dts
      note: >-
        A folded note that spans
        two lines.
  series:
    - title: Add Widget board
      url: https://example.com/list/series
      target: linux
      status: unmerged
      files: [arch/arm64/boot/dts/widget/widgetboard.dts]
      fetch: blocked
      verified: 2026-09-18
  docs: []
  tools: []
---

# Widget Board

## Orientation

Synthetic.

## Quick-facts

- **Boot media.** An EEPROM. `[doc]` (Widget docs, boot page)
- **Power.** `TODO (verify on hardware)`: PMIC not recorded.

## Gotchas

- Console is the second UART. `[DT]`
