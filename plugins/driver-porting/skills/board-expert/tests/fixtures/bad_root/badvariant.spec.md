---
kind: board
id: badvariant
name: Bad Variant Board
triggers: [bad variant]
not_triggers: not-a-list
aliases: [Bad_Alias, ok-alias]
parts: []
cache: badvariant-resources
variants:
  - name: Bad Variant Pro
    triggers: [bad variant pro]
    shares: [soc]
    differs: nothing
    tag: rumor
    source: 7
resources:
  docs:
    - title: Partially readable page
      url: https://example.com/partial
      access: public
      fetch: partial
      fetch_via: 7
---

# Bad Variant Board

## Quick-facts

- **Console.** On the SoC. `[DT]` (`badvariant.dts`)
