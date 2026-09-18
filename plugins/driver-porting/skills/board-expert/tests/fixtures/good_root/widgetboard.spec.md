---
kind: board
id: widgetboard
name: Widget Board
triggers: [widget board, widgetboard]
parts: [widgetsoc]
cache: widget-resources
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
  docs: []
  tools: []
---

# Widget Board

## Orientation

Synthetic.

## Quick-facts

- **Boot media.** An EEPROM. `[doc]`
- **Power.** `TODO (verify on hardware)`: PMIC not recorded.

## Gotchas

- Console is the second UART. `[DT]`
