---
kind: soc
id: widgetsoc
name: Widget SoC
triggers: [widgetsoc]
cache: widget-resources
instances:
  - name: uart0
    ip: widgetuart
    reg: 0xfe201000
    irq: {kind: SPI, number: 121, intid: 153, trigger: level-high, note: shared}
    clocks: [uartclk]
    role: debug console
    note: "quoted: colon inside"
resources:
  repos: []
  docs: []
---

# Widget SoC

## Quick-facts

- **Addressing.** Flat. `[DT]`
- **Timer.** 24 MHz. `[standard]`, `[hardware]`
- **Ordering.** Reset before clock. `[source-observed]` `TODO (verify on hardware)`: confirm the order.
- **GPU.** Widget-G1 per press. `[press]` `TODO (verify on hardware)`: the part number.

## Gotchas

- Enter at EL2. `[doc]` (Widget boot guide)
