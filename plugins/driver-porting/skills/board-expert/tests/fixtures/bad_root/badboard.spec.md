---
kind: board
id: badboard
name: Bad Board
triggers: [bad board]
parts: [missingsoc]
resources:
  docs:
    - title: Secret TRM
      url: https://intranet.example/trm
      access: internal
      via: skill:acme-board-tools
---

# Bad Board

## Quick-facts

- **Boot media.** An EEPROM with no tag.
- **Ordering.** Reset before clock. `[source-observed]`

## Gotchas

- Fine. `[DT]`
