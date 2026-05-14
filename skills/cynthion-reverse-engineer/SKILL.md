---
name: cynthion-reverse-engineer
description: Orchestrate a structured USB protocol reverse-engineering session using Cynthion hardware. Guides the user through capturing, diffing, and inferring command structure for a proprietary USB device, then generates replay and Facedancer emulation scaffolds. Use when the user wants to reverse-engineer a USB device's protocol, understand what commands a proprietary USB device sends, build a clone or replay of a USB device, or make a device emulator with Facedancer. Do NOT trigger on generic "analyze a USB capture" requests — use cynthion-pcap-decode for that.
---

<!--
Copyright 2026 contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Cynthion Reverse Engineer

An iterative playbook for reverse-engineering proprietary USB device protocols
using Cynthion + Packetry captures and a set of analysis scripts. Each step
produces an artifact the user reviews before proceeding.

**Ethics note:** Always confirm with the user what device they are working on
and that they have the right to reverse-engineer it (own it, it is their
device, it is for research/interoperability, etc.). Do not automate cloning
without this confirmation.

## Trigger phrases

- "reverse engineer this USB device"
- "figure out what protocol this USB device uses"
- "decode a proprietary USB protocol"
- "make a replay / clone of this USB device"
- "build a Facedancer emulator for this device"
- "what commands does this USB device send?"

## Sibling skills

| Skill | Role |
|---|---|
| `cynthion-setup` | Install cynthion CLI, Packetry, udev rules |
| `cynthion-capture` | Drive Cynthion + Packetry to produce pcap files |
| `cynthion-pcap-decode` | Decode a single pcap; required by this skill |

`cynthion-pcap-decode` must be installed for the analysis scripts to work.
The scripts look for it at `~/.claude/skills/cynthion-pcap-decode/scripts/`
and also as a sibling in the same skills tree. If not found, they fail with
a clear message pointing to the install location.

## Prerequisites

- Cynthion hardware set up (run `/cynthion-setup` if needed)
- `cynthion-pcap-decode` skill installed
- Python 3.8+ (stdlib only for analysis scripts)
- `tshark` recommended for pcap decoding (see `cynthion-pcap-decode`)
- `libusb1` Python package for running the generated replay script:
  `uv tool install libusb1` or `pip install libusb1`
- `facedancer` Python package for the clone script (Linux only):
  `pip install facedancer`

## The seven-step workflow

### Step 1 — Capture baseline and variant sessions

Use `cynthion-capture` (or Packetry directly) to record the device doing
**different things** — idle vs. active, button A vs. button B, command X vs.
command Y. Name captures descriptively.

```
idle.pcap          ← device plugged in, no interaction
button_press.pcap  ← user pressed the physical button
```

Minimum: two captures. More labels → sharper opcode inference.

Ask the user: *"What actions should we contrast? I need at least two captures
with the device behaving differently."*

### Step 2 — Decode each capture

```bash
python3 ~/.claude/skills/cynthion-pcap-decode/scripts/decode.py \
    idle.pcap --format json > idle.json

python3 ~/.claude/skills/cynthion-pcap-decode/scripts/decode.py \
    button_press.pcap --format json > button_press.json
```

Or pass `.pcap` files directly to the analysis scripts — they decode
internally via the same pipeline.

Check the enumeration phase for device identity:

```bash
python3 ~/.claude/skills/cynthion-pcap-decode/scripts/decode.py \
    idle.pcap --phase enumeration --format transcript
```

### Step 3 — Diff transaction streams

```bash
python3 scripts/diff_transactions.py \
    idle.json button_press.json \
    --label idle button_press --format text
```

Output classifies each byte offset per endpoint:

| Marker | Class | Interpretation |
|--------|-------|----------------|
| `.` | constant | Fixed field (magic, version, reserved) |
| `^` | monotonic | Sequence counter or frame counter |
| `!` | varying | Opcode, argument, payload, CRC, or nonce |
| `?` | missing | Packet absent in one capture |

**Known limitation:** with exactly two captures, a byte that differs by
exactly 1 between them is labelled "monotonic" even if it is an opcode.
Use `infer_commands.py` (step 4) for the authoritative classification — it
compares values across labels rather than pairwise.

Present the diff to the user and ask: *"These bytes vary between captures —
which endpoint looks most interesting?"*

### Step 4 — Infer command structure

```bash
python3 scripts/infer_commands.py \
    idle.json button_press.json \
    --label idle button_press --format markdown
```

Heuristics applied:
- **opcode**: byte takes a small set of values (≤ 16 distinct), each
  correlated with a label — i.e., value A always appears in label "idle"
  and value B always in "button_press"
- **counter**: strictly incrementing by 1 across samples within a label
- **constant**: identical across all labels
- **varying**: no discernible pattern (candidate for CRC/nonce)

Produces a JSON hypothesis document:

```bash
python3 scripts/infer_commands.py idle.json button_press.json \
    --label idle button_press > hypothesis.json
```

Review the hypothesis with the user. Common outcomes at this point:
- Clear opcode at byte 0 → proceed to step 5
- Multiple candidate opcodes → capture more labeled sessions
- All bytes vary → the device may use encryption or the frame format
  is not fixed-length (check for length prefixes)

### Step 5 — Generate replay script

```bash
python3 scripts/gen_replay.py hypothesis.json idle.json -o replay.py
```

The generated script (`replay.py`):
- Opens the device by VID/PID using `libusb1` (pyusb fallback if not installed)
- Claims interface 0
- Replays the enumeration control transfers
- Replays the observed bulk/interrupt transactions (up to `--max-bulk`, default 20)

Run against the real device:

```bash
pip install libusb1
python3 replay.py
```

On Linux/macOS without root, udev/system permissions may need adjusting.
Ask the user to confirm the replay produces expected device behaviour before
continuing.

### Step 6 (optional) — Generate Facedancer device clone

**Linux only.** Facedancer 3.x device emulation does not work on macOS or Windows.

```bash
python3 scripts/gen_facedancer_clone.py idle.json -o clone.py
BACKEND=cynthion python3 clone.py
```

The generated script uses the confirmed Facedancer 3.x
`@use_inner_classes_automatically` class syntax with nested
Configuration/Interface/Endpoint inner classes. Endpoint `handle_data_requested`
stubs return zeroed bytes — the user fills these in based on observed responses.

Vendor/class control request handlers are provided as commented stubs. Add them
using:

```python
@vendor_request_handler(number=0x01, direction=USBDirection.IN)
@to_device
def handle_vendor_in(self, request: USBControlRequest):
    request.reply(b"\x00")
```

Ask the user: *"Do you want to emulate the device (Facedancer clone) or replay
traffic at the host (replay script)? Or both?"*

### Step 7 — Generate protocol document

```bash
python3 scripts/gen_protocol_doc.py hypothesis.json \
    --capture idle.json idle \
    --capture button_press.json button_press \
    -o protocol.md
```

Produces a structured Markdown document:
- Device identity (VID/PID, USB spec version)
- Capture summary table
- Control transfer map (EP0 requests)
- Endpoint map with frame sizes and roles
- Inferred command table with example payloads
- Byte-role breakdown per endpoint
- Open questions checklist

Save this as the protocol reference and iterate — each new capture adds rows
to the command table and resolves open questions.

## Script reference

All scripts are in `scripts/` relative to this skill directory. They accept
`.pcap` or `.json` (from `decode.py --format json`) as inputs.

| Script | Input | Output |
|--------|-------|--------|
| `diff_transactions.py A B` | two captures | byte classification table |
| `infer_commands.py A B …` | N labelled captures | hypothesis JSON / Markdown |
| `gen_replay.py hyp.json cap.json` | hypothesis + capture | runnable libusb1 script |
| `gen_facedancer_clone.py cap.json` | decoded capture | Facedancer 3.x Python script |
| `gen_protocol_doc.py hyp.json` | hypothesis + captures | Markdown protocol doc |

## Worked example

`example/` contains a fully self-contained walkthrough using a synthetic
vendor device (no hardware required):

```bash
cd example/
python3 generate_synthetic.py          # creates status_query.json + set_brightness.json
python3 ../scripts/diff_transactions.py status_query.json set_brightness.json \
    --label status_query set_brightness --format text
python3 ../scripts/infer_commands.py   status_query.json set_brightness.json \
    --label status_query set_brightness > hypothesis.json
python3 ../scripts/gen_replay.py       hypothesis.json status_query.json -o replay.py
python3 ../scripts/gen_facedancer_clone.py status_query.json -o clone.py
python3 ../scripts/gen_protocol_doc.py hypothesis.json \
    --capture status_query.json status_query \
    --capture set_brightness.json set_brightness -o protocol.md
```

See `example/README.md` for annotated output and interpretation notes.

## Pitfalls

**Do not trust LLM memory for Facedancer or Cynthion API details.**
The v2 → v3 Facedancer API changed significantly. Always check current docs:
- https://facedancer.readthedocs.io
- https://cynthion.readthedocs.io
- https://github.com/greatscottgadgets/facedancer/blob/main/examples/template.py

**Facedancer 3.x is Linux-only.**
macOS has limited and unreliable support; Windows is unsupported. The clone
generator always emits this caveat in the output file header.

**`BACKEND=cynthion` must be set at runtime, not in the script.**
Setting it as an environment variable before the Python invocation is the
correct pattern. Hardcoding it inside the script doesn't work.

**Two captures is the minimum, not the ideal.**
With only two captures the diff cannot distinguish "opcode that changes"
from "counter that happens to increment by 1". Capture 3–5 labelled
sessions for reliable opcode inference, especially for multi-byte commands.

**Fixed-length frame assumption.**
`infer_commands.py` groups transactions by dominant payload length. Devices
that use variable-length framing (length prefix, TLV, etc.) need manual
analysis — the inferred command table will be sparse or misleading.

**The replay script replays observations, not a protocol understanding.**
It is a starting point. The user will need to parameterise commands, handle
responses, and add error handling before the script is useful for anything
beyond a simple smoke test.
