---
name: cynthion-setup
description: Install and verify the software prerequisites for Cynthion skills (cynthion CLI, Packetry GUI, tshark, Linux udev rules). Run this once on a new machine before using any other Cynthion skill. Use when the user asks to set up Cynthion, install Cynthion software, or when a Cynthion skill fails due to missing tools.
---

<!--
Copyright 2026 contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->

# Cynthion Setup

Installs and verifies the software needed by Cynthion skills. Run this once on
a new machine. Covers all platforms (macOS, Linux, Windows).

## Trigger phrases

- "set up Cynthion"
- "install Cynthion software"
- "Cynthion setup"
- `/cynthion-setup`

## What this skill installs

| Component | Purpose | Required by |
|---|---|---|
| `cynthion` CLI | Device management, bitstream loading | all Cynthion skills |
| Packetry | USB capture GUI | `cynthion-capture` |
| tshark (Wireshark CLI) | Preferred USB pcap decoder | `cynthion-pcap-decode`, `cynthion-reverse-engineer` |
| udev rules (Linux only) | Non-root USB device access | all Cynthion skills |

## Procedure

### 1. Detect the platform

```bash
uname -s   # Darwin = macOS, Linux = Linux; Windows shows up as MINGW*/MSYS*/CYGWIN*
```

Tailor the steps below to the result.

### 2. Check for `uv`

```bash
uv --version
```

If not found, direct the user to install it first:

- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install --id=astral-sh.uv` or the installer at https://docs.astral.sh/uv/getting-started/installation/

Do not proceed until `uv --version` succeeds.

### 3. Install or upgrade the `cynthion` CLI

Check whether it is already installed and at what version:

```bash
uv tool list
cynthion --version 2>/dev/null || echo "not installed"
```

Install or upgrade:

```bash
uv tool install cynthion          # first install
uv tool upgrade cynthion          # if already installed
```

Confirm:

```bash
cynthion --version
```

### 4. Install Packetry

**macOS:**

```bash
brew install packetry
```

If Homebrew is not installed, direct the user to https://brew.sh before continuing.

**Linux:**

Packetry is not in common distro package managers. Download the latest release binary
from https://github.com/greatscottgadgets/packetry/releases, then make it executable:

```bash
chmod +x packetry
sudo mv packetry /usr/local/bin/
```

Or install to `~/.local/bin/` if the user prefers not to use sudo.

**Windows:**

Download `Packetry-Installer-for-Windows.zip` from
https://github.com/greatscottgadgets/packetry/releases, unzip it, and run the
installer. The installer adds `packetry` to `PATH`.

After installation on any platform, confirm:

```bash
packetry --version
```

### 5. Install tshark (Wireshark CLI)

`tshark` is the preferred USB pcap decoder for `cynthion-pcap-decode` and the
analysis steps in `cynthion-reverse-engineer`. The bundled Python fallback is
best-effort and not sufficient for most real captures, so treat tshark as
required.

**macOS:**

```bash
brew install wireshark
```

The Wireshark formula ships `tshark`. If you already have Wireshark.app
installed via the .dmg, ensure its `tshark` is on PATH, or install
`wireshark` via brew to get a CLI symlink.

**Linux:**

```bash
sudo apt install tshark           # Debian/Ubuntu
sudo dnf install wireshark-cli    # Fedora
```

The Debian/Ubuntu postinst asks whether non-root users may capture live
traffic. The Cynthion skills only need tshark to read pcap files (not live
capture), so answer **No** — it's the safer default.

**Windows:**

Download Wireshark from https://wireshark.org/download.html and run the
installer. Make sure the "TShark" component is selected; the installer adds
it to PATH.

After installation on any platform, confirm:

```bash
tshark --version
```

### 6. Install udev rules (Linux only)

Skip this step on macOS and Windows.

Without udev rules the Cynthion device is only accessible as root. The rules file
is bundled with the `cynthion` package:

```bash
sudo cp ~/.local/share/uv/tools/cynthion/lib/python*/site-packages/cynthion/assets/54-cynthion.rules \
    /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then ask the user to unplug and replug the Cynthion before continuing.

### 7. Verify device access

Plug in the Cynthion via its CONTROL port, then:

```bash
cynthion info
```

Expected output:

```
Cynthion version: <x.y.z>
Apollo version: <x.y.z>

Found Apollo stub interface!
    Vendor ID: 1d50
    ...
```

If this succeeds, the environment is ready for all Cynthion skills.

## Troubleshooting

**`uv tool install cynthion` fails**
- Confirm Python 3.9+ is available: `python3 --version`
- Try `uv tool install --python 3.12 cynthion` to pin a known-good version

**`cynthion info` reports no device found after install**
- Check the cable is data-capable (not charge-only) and connected to the CONTROL port
- On Linux: confirm the udev rules were installed and the device was replugged
- Try a different USB port

**`packetry --version` fails on Linux after install**
- Confirm the binary is on `PATH`: `which packetry`
- GTK4 must be installed: `sudo apt install libgtk-4-1` (Debian/Ubuntu) or equivalent

**`tshark --version` not found after install**
- Confirm `tshark` is on `PATH`: `which tshark`
- On some distros `tshark` ships in a separate package from `wireshark-common`;
  install the explicit `tshark` package
- On macOS, if Wireshark was installed via .dmg rather than brew, `tshark` may
  live inside `/Applications/Wireshark.app/Contents/MacOS/` and not be on PATH

## When a new Cynthion skill is added

If a new Cynthion skill introduces additional prerequisites, update the
"What this skill installs" table above and add the relevant install steps to the
procedure. Other Cynthion skills should reference this skill rather than
duplicating install instructions.
