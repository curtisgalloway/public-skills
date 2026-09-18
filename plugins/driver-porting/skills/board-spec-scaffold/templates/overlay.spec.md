---
overlays: <id>
resources:
  repos:
    - name: <internal repo short name>
      url: <internal URL>
      ref: <branch>
      license: <as applicable>
      access: internal
      via: skill:<vendor>-board-tools
      note: <what it adds over the public sources>
  docs:
    - title: <internal document, for example the NDA TRM>
      url: <internal URL>
      access: internal
      via: skill:<vendor>-board-tools
      cite: true
  tools:
    - kind: bench
      name: <target name on the lab rig>
      via: skill:<vendor>-board-tools
      note: <serial, power, netboot, screen available?>
---

<!-- license header per the vendor repo's convention -->

# <Hardware display name> — <vendor> overlay

## Quick-facts

<Facts the public spec cannot carry: values from NDA documents, internal errata, behavior measured on
the lab rig. Every bullet ends with a tag; cite the internal document by title and section.>

- **<Fact.>** `[databook]` (<internal document title>, §<section>)

## Gotchas

- **<Internal-only gotcha.>** `[doc]` (<internal page>)
