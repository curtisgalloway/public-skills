<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# Implementation task template

## Terms

- **Specification (`spec.md`)** — the supplied hardware description.
- **Fixture-facts sheet** — the supplied board wiring and OS binding information.

See the [glossary](../../../../../GLOSSARY.md) for preparation terminology; this link is outside
the exported task and does not grant an implementer access to the evaluator repository.

Preparation status: do not launch with unresolved bracketed fields. Export only the Task section
after freezing the resource and checkpoint fields; record the exported text's digest separately.
This template is not an implementation skill or an evaluator input packet.

## Task

Implement a Linux v6.12 driver for the ENC28J60 B7 using `spec.md` and the supplied environment.
Support initialization, untagged unicast and broadcast transmit/receive in half duplex,
interrupt handling, interface stop/start, and bounded failure recovery. Jumbo frames,
VLAN-specific behavior, multicast hash filtering, promiscuous-mode qualification,
DMA/checksum offload, power-management optimization, suspend/resume, wake-on-LAN,
performance tuning, and other silicon revisions are outside this task.

Use only the supplied files and build tools. Do not follow citations, fetch device sources,
search for another implementation, or consult external device documentation. You may use
the supplied general Linux API documentation. The fixture-facts sheet records wiring and
binding information supplied separately from the specification.

Keep a log of missing information, assumptions, clarification requests, and blockers, with
links to relevant spec passages. Record a requirement for hardware verification explicitly;
it is not automatically a specification defect. No new hardware facts will be supplied during
this attempt. If a blocker prevents progress, preserve the partial implementation and explain it.

Run the supplied build check and any offline checks you author within the allowed environment.
Hardware access and evaluator tests are unavailable during implementation. Deliver source,
build logs, your checks and their results, and the gap/assumption log. Stop at completion,
an irreducible blocker, or [approved time/token/spending caps], whichever occurs first.
Preserve failures. Save intermediate work according to [approved checkpoint policy].
