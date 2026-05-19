---
name: cynthion-capture
description: Set up and run USB traffic capture with a Cynthion USB analyzer. Covers device verification, loading the analyzer bitstream, hardware wiring, launching Packetry for GUI capture, and headless (no-GUI) capture to .pcap files using the bundled Rust or Python tools. Use when the user asks to capture USB traffic, analyze a USB device, run headless/automated capture, or start a USB capture session with Cynthion.
---

<!--
Copyright 2026 contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Cynthion USB Capture

Cynthion is a USB analysis platform from Great Scott Gadgets. In analyzer mode it
acts as a man-in-the-middle between a USB host and a USB device, capturing all
traffic to a pcap file or live in the Packetry GUI.

## Trigger phrases

- "capture USB traffic with Cynthion"
- "start a USB capture session"
- "analyze this USB device with Cynthion"
- "run packetry"
- "load the analyzer bitstream"
- "headless capture"
- "capture without a GUI"

## Prerequisites

### Hardware

- **Cynthion** (r1.4 or later) connected to your machine via its **CONTROL** port
  (the USB-C port labeled CONTROL — this is how the host talks to the analyzer)
- A second USB cable for the **TARGET** side (see wiring below)

### Software

Run the `cynthion-setup` skill to install all software prerequisites (`cynthion`
CLI, Packetry, and Linux udev rules) and verify device access. Only continue with
this skill once `cynthion info` reports `Found Apollo stub interface!`.

## Hardware wiring

Cynthion has three USB ports on the board edge:

| Port label | Connector | Role in analyzer mode |
|---|---|---|
| **CONTROL** | USB-C | Connected to the analysis host (your machine). Always required. |
| **HOST-A** | USB-A female | Connected to the USB host you want to observe (or left unconnected for device-only capture). |
| **TARGET-C** | USB-C | Connected to the USB device under test. |

For a typical device capture (e.g., analyzing a USB gadget):

```
[Your machine] ──CONTROL──▶ Cynthion ◀──HOST-A──  [USB host]
                                      ◀──TARGET-C── [USB device under test]
```

Cynthion sits transparently between HOST-A and TARGET-C, intercepting all packets.
If you only want to observe a device plugged into your machine, connect your
machine to both CONTROL and HOST-A, and the device under test to TARGET-C.

**Cable note:** HOST-A is a USB-A female port. If the host machine has a USB-A
port (typical desktop/laptop), you need a **USB-A male-to-male cable** (sold as
"PC-to-PC" or "USB transfer cables"). If the host has USB-C, a standard USB-C
to USB-A cable works.

## Procedure: GUI capture with Packetry

### 1. Load the analyzer bitstream

If `cynthion info` shows the device is already running the USB Analyzer bitstream
(look for `Bitstream: USB Analyzer` in the output), skip this step.

```bash
cynthion run analyzer
```

This flashes the FPGA with the analyzer gateware. The device re-enumerates
after a few seconds. Re-run `cynthion info` to confirm.

### 2. Launch Packetry

```bash
packetry
```

Packetry is a GTK4 GUI application. On first launch it may take a moment to open.

To quickly verify the hardware without starting a full session:

```bash
packetry --test-cynthion
```

### 3. Capture traffic

1. In Packetry, click **Start** (or the record button) to begin capture.
2. Plug in or activate the USB device connected to the TARGET port.
3. Interact with the device to generate traffic.
4. Click **Stop** when done.

### 4. Save the capture

File → Save As → choose a `.pcap` filename.

Packetry saves captures in standard pcap format, which can be opened in
Wireshark with the USB dissector (`usbmon` link type).

## Procedure: Headless capture (no GUI)

Use the bundled `cynthion-capture` tool for scripted, automated, or background
capture without launching Packetry. It writes standard libpcap files
(LINKTYPE\_USB\_2\_0, link type 288) compatible with Wireshark and tshark.

Two implementations are provided in `scripts/`:

- **Rust** (`scripts/capture-rs/`) — recommended; uses `nusb`, which is
  cross-platform: IOUSBHost on macOS (no sudo needed), usbfs on Linux (udev rules
  required for unprivileged access — same rules used by Packetry), WinUSB on
  Windows. Async bulk-in queue gives better throughput at high traffic rates.
- **Python** (`scripts/capture.py`) — simpler to run without a build step; uses
  `pyusb`, which has the same platform access requirements as the Rust tool.

### Build and install the Rust tool

```bash
cd scripts/capture-rs
cargo build --release
# binary at target/release/cynthion-capture
# optionally: cargo install --path .
```

Requires Rust stable (edition 2024). Dependencies: `nusb`, `futures-lite`, `ctrlc`.

### Usage

```
cynthion-capture [OPTIONS] <output.pcap>

Options:
  -d, --duration <seconds>   Stop after N seconds (default: run until Ctrl-C)
  -s, --speed <speed>        auto|hs|fs|ls  (default: auto)
  -h, --help                 Show this help
```

**Speed modes:**
- `auto` — captures all speeds (HS, FS, LS). Use this unless you need to filter.
- `hs` — High Speed (480 Mbps) only
- `fs` — Full Speed (12 Mbps) only
- `ls` — Low Speed (1.5 Mbps) only

**Examples:**

```bash
# Capture all traffic until Ctrl-C
cynthion-capture capture.pcap

# Capture 30 seconds of full-speed traffic only
cynthion-capture -d 30 -s fs capture-fs.pcap

# Capture in background for 60 seconds
cynthion-capture -d 60 output.pcap &
```

### Python alternative

```bash
pip install pyusb
python3 scripts/capture.py capture.pcap
python3 scripts/capture.py -d 30 -s fs capture-fs.pcap
```

Same options as the Rust tool. On Linux without udev rules, prefix with `sudo`.

### Speed field encoding (implementation note)

The Cynthion analyzer control request uses a 1-byte value: `bits[2:1]=speed, bit[0]=enable`.
The speed encoding (confirmed from Packetry source `src/backend/cynthion.rs`) is:

| Value | Speed |
|---|---|
| 0 | HS-only |
| 1 | FS-only |
| 2 | LS-only |
| 3 | **Auto (all speeds)** |

`auto` (speed=3) is the correct default for general captures. It also works
correctly when the device was already enumerated before capture started.

## Offline analysis with Wireshark

```bash
wireshark capture.pcap
```

Useful Wireshark filters for USB captures:

| Filter | What it shows |
|---|---|
| `usb.transfer_type == 0x01` | Isochronous transfers |
| `usb.transfer_type == 0x02` | Bulk transfers |
| `usb.transfer_type == 0x03` | Interrupt transfers |
| `usb.bmRequestType` | Control transfers (setup packets) |
| `usb.data_len > 0` | Packets with payload data |

## Switching back to other modes

To load the Facedancer (USB emulation) bitstream instead:

```bash
cynthion run facedancer
```

To update firmware and bitstreams to the latest installed version:

```bash
cynthion update
```

## Troubleshooting

**`cynthion info` shows no device found**
- Check that the CONTROL port cable is connected and is a data cable (not charge-only)
- Try a different USB port on the host
- On Linux: confirm udev rules are installed (see Prerequisites above) and that you unplugged and replugged the device after installing them

**Packetry shows no capture data**
- Confirm the analyzer bitstream is loaded (`cynthion info` → `Bitstream: USB Analyzer`)
- Check that the TARGET cable is connected to the device under test
- Verify the device under test is powered and enumerating

**Headless capture: "No Cynthion USB Analyzer found"**
- Run `cynthion run analyzer` to load the analyzer bitstream first
- On macOS: no sudo needed with the Rust tool (uses IOUSBHost)
- On Linux: confirm udev rules grant access, or run with `sudo`

**Device enumerates at wrong speed**
- Cynthion captures USB 2.0 (HS/FS/LS). USB 3.x SuperSpeed traffic is not captured.
- For USB 3.x devices, the device may fall back to USB 2.0 when connected through Cynthion — this is expected.
