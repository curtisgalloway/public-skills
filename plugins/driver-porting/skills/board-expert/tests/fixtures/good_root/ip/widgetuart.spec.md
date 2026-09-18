---
kind: ip
id: widgetuart
name: Widget UART
triggers: [widgetuart]
cache: widgetuart-resources
resources:
  repos:
    - name: linux
      url: https://example.com/linux
      ref: master
      license: GPL-2.0-only
      files: [drivers/tty/serial/widget.c]
  docs:
    - title: Widget UART TRM
      url: https://example.com/trm
      access: public
      cite: true
---

# Widget UART

## Standards and databook

- Register map per the TRM. `[databook]`

## Programming model

- **Enable.** Disable, program, enable. `[databook]`

## Known variants and quirks

- FIFO depth varies. `[databook]`

## Gotchas

- Latch by writing LCR. `[databook]`
