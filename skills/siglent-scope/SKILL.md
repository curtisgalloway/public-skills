---
name: siglent-scope
description: Remote-control a Siglent SDS1000X-E series oscilloscope (SDS1104X-E, SDS1204X-E, etc.) over the network — SCPI command essentials, screenshots, deep-memory waveform transfer, and the firmware quirks that hang naive clients. Use when the user wants to talk to, automate, screenshot, or pull waveform data from a Siglent SDS1000X-E-series scope.
---

<!--
Copyright 2026 contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

# siglent-scope

Remote control and data transfer for Siglent SDS1000X-E series scopes
(verified on an SDS1104X-E, firmware 6.1.37R17). No VISA stack needed —
everything below works over a plain TCP socket.

## Finding and reaching the scope

Resolve the address in this order:

1. An explicit address from the user, a local companion skill, or
   project docs.
2. `$SCOPE_HOST` env var.
3. The bare hostname **`scope`** — the default convention; it resolves
   via the local DNS search domain when the scope has a DNS entry.
   Verify with the sanity check below before assuming.
4. Otherwise ask the user. The scope shows its IP under
   Utility → I/O → LAN.

Endpoints (ports are fixed):

- **:5025** — raw SCPI socket (preferred; one client at a time)
- :5024 — telnet SCPI
- VXI-11 (works with pyvisa `TCPIP::<host>::INSTR`)
- :80 — embedded web UI / virtual front panel (4-channel models)

Sanity check:

```bash
printf '*IDN?\n' | nc -w 3 <scope-host> 5025
```

## SCPI essentials (LeCroy-derived dialect)

- Send `CHDR OFF` first — strips echoed headers from query replies.
  Persists on the instrument across connections.
- Common queries: `*IDN?`, `TDIV?`, `SARA?` (sample rate), `C1:VDIV?`,
  `C1:OFST?`, `SANU? C1` (acquired points), `TRMD?`, `MSIZ?`. Settings are
  the same commands with a value (`TDIV 1MS`, `C1:TRLV 1.5V`, `MSIZ 14M`).
- **Screenshot**: `SCDP` returns a raw 800×480 BMP — no length prefix;
  parse the file size from BMP header bytes 2–5 (little-endian), then one
  trailing `\n`.
- **Waveform**: `WFSU SP,0,NP,0,FP,0` (all points) then `C1:WF? DAT2`.
  The reply embeds `#9<nine ASCII digits = byte count><int8 payload>`
  followed by exactly two `\n` bytes.
  Volts = code × (VDIV/25) − OFST; time axis from `SARA?`.

## Firmware quirks (observed on 6.1.37R17 — these WILL hang naive clients)

- **`SAST?` never replies while trigger mode is STOP** — the connection
  hangs forever, no error. Poll `INR?` bit 0 instead (latched
  acquisition-done flag, clears on read; read once before arming to
  discard stale state).
- **`ARM` force-starts a sweep immediately** — it does NOT merely arm.
  `TRMD SINGLE` alone is how you arm and wait for a real trigger.
- **`FRTR` (force trigger) is a no-op while armed in SINGLE mode.** To
  force a stuck single acquisition, send `ARM`.
- **Any `MSIZ` write clamps `TDIV` to 1 ns/div** — even rewriting the
  value MSIZ already has — and the clamp can land asynchronously AFTER a
  subsequent `TDIV` write. Round-trip any query after `MSIZ`, then set
  `TDIV` and verify the read-back in a retry loop until it sticks.

## Hardware facts (X-E series)

- Channels share ADCs in pairs (CH1/CH2 and CH3/CH4 on 4-ch models).
  Full sample rate (1 GSa/s) and full memory (14 Mpts) per channel only
  when ≤1 channel of each pair is active — for two-channel work use
  **C1 + C3**.
- 14 Mpts @ 1 GSa/s = 14 ms record; a 14 Mpts × 2-channel pull over the
  :5025 socket takes ~4.5 s (~6.4 MB/s), delivered as a single `WF?`
  block — no chunking required.
- 100/200 MHz analog bandwidth: fine for USB low/full-speed signal
  integrity work; not usable for USB high speed (480 Mb/s).

## Reference

[SDS1000X-E Programming Guide](https://www.batterfly.com/PDF/Siglent/SDS1000X-E/SDS1000X-E_programmingguide_EN.pdf)
— full command set. Where this skill's quirks list conflicts with the
guide, trust the quirks list; it was verified on the wire.
