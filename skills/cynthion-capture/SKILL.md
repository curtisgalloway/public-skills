---
name: cynthion-capture
description: Set up and run USB traffic capture with a Cynthion USB analyzer. Covers device verification, loading the analyzer bitstream, hardware wiring, launching Packetry for capture, and saving captures as .pcap files for offline analysis. Use when the user asks to capture USB traffic, analyze a USB device, or start a USB capture session with Cynthion.
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

## Prerequisites

### Hardware

- **Cynthion** (r1.4 or later) connected to your machine via its **CONTROL** port
  (the USB-C port labeled CONTROL — this is how the host talks to the analyzer)
- A second USB cable for the **TARGET** side (see wiring below)

### Software

**`cynthion` CLI** (all platforms):

```bash
uv tool install cynthion
```

**Packetry GUI** — install method depends on platform:

| Platform | Install |
|---|---|
| macOS | `brew install packetry` |
| Linux | Download the binary from [github.com/greatscottgadgets/packetry/releases](https://github.com/greatscottgadgets/packetry/releases) |
| Windows | Download `Packetry-Installer-for-Windows.zip` from the same releases page and run the installer |

**Linux only — udev rules:**

Without the udev rules, the Cynthion device is only accessible as root. Install them
from the Cynthion package:

```bash
sudo cp ~/.local/share/uv/tools/cynthion/lib/python*/site-packages/cynthion/assets/54-cynthion.rules \
    /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then unplug and replug the Cynthion.

Verify the device is visible:

```bash
cynthion info
```

Expected output includes `Found Apollo stub interface!` with a vendor ID of `1d50`.

## Hardware wiring

Cynthion has three USB ports on the board edge:

| Port label | Role in analyzer mode |
|---|---|
| **CONTROL** | Connected to the analysis host (your machine). Always required. |
| **HOST** | Connected to the USB host you want to observe (or left unconnected for device-only capture). |
| **TARGET** | Connected to the USB device under test. |

For a typical device capture (e.g., analyzing a USB gadget):

```
[Your machine] ──CONTROL──▶ Cynthion ◀──TARGET── [USB device under test]
                                      ◀──HOST───  [USB host, if needed]
```

Cynthion sits transparently between HOST and TARGET, intercepting all packets.
If you only want to observe a device plugged into your machine, connect your
machine to both CONTROL and HOST, and the device under test to TARGET.

## Procedure

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

**Device enumerates at wrong speed**
- Cynthion captures USB 2.0 (HS/FS/LS). USB 3.x SuperSpeed traffic is not captured.
- For USB 3.x devices, the device may fall back to USB 2.0 when connected through Cynthion — this is expected.
