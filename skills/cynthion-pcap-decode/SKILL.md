---
name: cynthion-pcap-decode
description: Decode, analyze, and diff USB capture files (.pcap/.pcapng) produced by Packetry and Cynthion. Use when the user mentions a .pcap or .pcapng from Packetry or Cynthion, asks to decode/analyze/read/diff/summarize a USB capture, or has questions about specific endpoints, descriptors, or transfer sequences in a capture file.
---

<!--
Copyright 2026 contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Cynthion pcap decode

Decode USB captures from Packetry/Cynthion into four progressively richer
views: raw packets → transactions → transfers → decoded descriptors and
class-specific content.

## Trigger phrases

- "decode this pcap"
- "analyze / read / summarize a USB capture"
- "what's in this .pcap from Packetry?"
- "diff two USB captures"
- "show me the device descriptor from this capture"
- "what HID reports does this capture contain?"
- "compare capture A and capture B"

## Prerequisites

```bash
# tshark (primary decoder — strongly recommended)
brew install wireshark          # macOS
sudo apt install tshark         # Debian/Ubuntu
# Windows: install Wireshark from https://wireshark.org/download.html

# Python 3.8+ (stdlib only — no extra packages required)
python3 --version
```

tshark is optional but recommended. Without it the native fallback decoder is
used, which covers packets → transactions → transfers and standard descriptors,
but lacks Wireshark's battle-tested USB 2.0 protocol handling.

## Quick start

```bash
cd skills/cynthion-pcap-decode/scripts

# Full decode — JSON output (default)
python3 decode.py capture.pcap

# Human-readable transcript
python3 decode.py capture.pcap --format transcript

# Markdown summary report
python3 decode.py capture.pcap --format markdown

# Enumeration phase only (SET_ADDRESS + descriptor reads)
python3 decode.py capture.pcap --phase enumeration --format transcript

# Filter by device address and endpoint
python3 decode.py capture.pcap --filter address=2 --filter endpoint=1

# Filter by transfer type
python3 decode.py capture.pcap --filter transfer-type=control

# Time window (seconds from start of capture)
python3 decode.py capture.pcap --time-range 0.0,2.5

# Force native Python decoder (no tshark)
python3 decode.py capture.pcap --native

# Diff two captures
python3 diff.py before.pcap after.pcap
python3 diff.py before.pcap after.pcap --endpoint 1 --format markdown
```

## Four-layer model

### Layer 1 — Packets

Individual USB 2.0 wire packets, identified by their PID byte:

| Group     | PIDs                          | Meaning |
|-----------|-------------------------------|---------|
| Token     | SETUP, IN, OUT, SOF           | Address the device/endpoint; start a transaction |
| Data      | DATA0, DATA1, DATA2, MDATA    | Carry the payload; alternate to detect retransmit |
| Handshake | ACK, NAK, STALL, NYET         | Receiver reports success, busy, or error |
| Special   | SPLIT, PING, PRE              | High-speed split transactions and preamble |

SOF (Start of Frame) packets are frame delimiters sent every 1 ms (FS) or
125 µs (HS). The decoder discards them — they are not part of transactions.

### Layer 2 — Transactions

One token + optional data + optional handshake, grouped by address/endpoint:

```
SETUP  addr=0 ep=0  → DATA0 [8 bytes]  → ACK      (control SETUP stage)
IN     addr=0 ep=0  → DATA0 [18 bytes] → ACK      (control data stage)
IN     addr=1 ep=1  → NAK              (device busy, no data yet)
OUT    addr=2 ep=2  → DATA1 [64 bytes] → ACK      (bulk write)
```

Transactions with NAK or STALL handshakes are preserved in the output but
marked accordingly. Transactions with no handshake (timeout/loss) are also
kept and flagged.

DATA0/DATA1 alternation is used to detect retransmissions: if the host
receives no ACK, it retransmits the same DATA0/DATA1. The decoder does not
deduplicate retransmissions — they appear as separate transactions.

### Layer 3 — Transfers

Transactions reassembled into logical USB transfers:

**Control transfers** (always EP0):
1. SETUP stage — 8-byte SETUP packet establishes the request
2. Data stage (optional) — one or more IN or OUT transactions carrying payload
3. Status stage — zero-length packet (ZLP) in the opposite direction, ACKed

**Bulk transfers** — one or more transactions on a non-zero endpoint, each
up to wMaxPacketSize bytes. A short packet (< wMaxPacketSize) signals end of
transfer. The decoder emits each successful data-bearing transaction as its
own transfer (bulk endpoint descriptors are needed for full reassembly).

**Interrupt transfers** — like bulk but polled at a fixed interval. The
decoder cannot distinguish interrupt from bulk without an endpoint descriptor;
it defaults to "bulk". Add `--filter transfer-type=interrupt` if you know the
endpoint type.

**Isochronous transfers** — periodic, no handshake. Not yet fully supported;
raw packets are preserved.

### Layer 4 — Decoded content

Control transfers on EP0 are decoded automatically:

**Standard GET_DESCRIPTOR responses:**

| Descriptor | What it tells you |
|---|---|
| Device (0x01) | VID, PID, USB version, device class, max packet size |
| Configuration (0x02) | Number of interfaces, power draw |
| Interface (0x04) | Class/subclass/protocol (identifies HID, MSC, CDC, etc.) |
| Endpoint (0x05) | Direction, type (bulk/interrupt/iso), max packet size |
| String (0x03) | Manufacturer, product, serial (UTF-16LE) |
| HID (0x21) | HID descriptor metadata |

**Class-specific decoders** (invoked automatically when the request type is
`class`):

| Class | What is decoded |
|---|---|
| HID keyboard (boot protocol) | Modifier bitmask + keycode array from 8-byte reports |
| HID mouse (boot protocol) | Button byte + signed dx/dy/wheel from 3–4 byte reports |
| MSC (SCSI) | CBW: opcode, LUN, transfer length, SCSI CDB; CSW: status |
| CDC-ACM | SET_LINE_CODING (baud/parity/stop/bits), SET_CONTROL_LINE_STATE (DTR/RTS) |
| MIDI | Cable number + MIDI event bytes per USB-MIDI event packet |
| UVC | Stub — raw bytes, length |
| USB Audio | Stub — raw bytes, length |
| Vendor-specific | First 64 bytes as hex |

## JSON output structure

```json
[
  {
    "index": 0,
    "type": "control",
    "addr": 0,
    "endp": 0,
    "direction": "IN",
    "time_s": 0.000003,
    "payload_len": 18,
    "payload_hex": "1201000200000040...",
    "setup": {
      "bmRequestType": "0x80",
      "direction": "IN",
      "type": "standard",
      "recipient": "device",
      "bRequest": 6,
      "wValue": "0x0100",
      "wIndex": 0,
      "wLength": 64
    },
    "decoded": {
      "descriptor_type": 1,
      "descriptor_name": "Device",
      "bLength": 18,
      "bDescriptorType": 1,
      "bcdUSB": "0x0200",
      "bDeviceClass": "0x00",
      "idVendor": "0x1d50",
      "idProduct": "0x615b",
      ...
    }
  }
]
```

## Diff output

`diff.py` aligns the transaction sequences from two captures by
`(addr, endpoint, direction)` and sequence position, then reports:

- **only in A** — transaction present in capture A but not B (e.g. extra
  enumeration step)
- **only in B** — transaction present in B but not A
- **changed** — same position, different payload bytes; changed offsets are
  marked with `*` in the hex dump and listed by offset number

Typical use: compare captures before and after a firmware update to confirm
the device descriptor or HID report format did not change unexpectedly.

## Pitfalls

**Do not use dpkt or scapy directly on these files.**
Packetry writes `LINKTYPE_USB_2_0` (link type 288), which is raw wire-level
USB 2.0 — PID byte followed by packet-specific fields. `dpkt` and many scapy
USB paths expect `LINKTYPE_USB_LINUX` (link type 220, the Linux usbmon format)
and will silently misparse packets or crash. Always use this skill's decoder
or tshark's `usbll` dissector.

**tshark field names differ between `-T json` and `-T ek`.**
`-T json` uses dot-separated names (`usbll.pid`, hex strings like `"0x2d"`).
`-T ek` uses underscore-separated names (`usbll_usbll_pid`, decimal strings
like `"45"`). The scripts use `-T ek` for streaming; do not mix the two
formats when writing custom post-processing.

**Large captures must stream — do not load into memory.**
`decode.py` feeds tshark output through a generator pipeline; no packet list
is held in memory. If you write custom analysis on top of this skill, keep
the generator chain intact rather than collecting into a list up front.

**Packetry/Cynthion knowledge in LLM training data is often stale.**
If you are uncertain about the current pcap format, tshark field names, or
Cynthion gateware behaviour, read the current docs rather than relying on
memory:
- https://cynthion.readthedocs.io
- https://packetry.readthedocs.io
- https://github.com/greatscottgadgets/packetry

**USB 3.x SuperSpeed is not captured.**
Cynthion captures USB 2.0 (HS/FS/LS) only. USB 3.x devices may fall back to
USB 2.0 when connected through Cynthion; the decoder handles the resulting
traffic correctly.

## Sample captures for testing

The Packetry repository includes test fixtures:

```bash
# Mouse (HID, 2182 packets, confirmed link type 288)
curl -L https://raw.githubusercontent.com/greatscottgadgets/packetry/main/tests/mouse/capture.pcap \
     -o mouse.pcap

python3 decode.py mouse.pcap --phase enumeration --format transcript
python3 decode.py mouse.pcap --filter transfer-type=bulk --format markdown
```

Expected enumeration output includes a Device Descriptor with class 0x00
(device class defined at interface), a HID Configuration Descriptor, and
a String Descriptor for the product name.

## When a new Cynthion skill calls this one

`diff.py` is designed to be imported as a library:

```python
from diff import diff_captures
diffs = diff_captures("before.pcap", "after.pcap", endp_filter=1)
```

`decode.py` exposes the full pipeline as importable functions:

```python
from decode import stream_packets, stream_transactions, stream_transfers, Filters
# Build a custom filter, stream transfers, do your own analysis
```
