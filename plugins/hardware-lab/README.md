# hardware-lab

Bench and USB-analysis skills: capture USB traffic with a Cynthion, decode and diff the
captures, reverse-engineer a proprietary device's protocol, profile a device from its driver
source, drive an MCCI 3411 USB 3.2 test device, poke buses with a Bus Pirate, and control a
Siglent oscilloscope from a script.

## Installing

### Claude Code

```
/plugin marketplace add curtisgalloway/public-skills
/plugin install hardware-lab@curtisg-skills
```

Add the marketplace once per machine. `curtisg-skills` is its name, set in
`.claude-plugin/marketplace.json`. Outside a session, run the same commands as `claude plugin
marketplace add ...` and `claude plugin install ...`. For a local clone, pass its path to
`marketplace add`. Update later with `/plugin marketplace update curtisg-skills`.

### Codex

```
codex plugin marketplace add curtisgalloway/public-skills
codex plugin add hardware-lab@curtisg-skills
```

Update later with `codex plugin marketplace upgrade curtisg-skills`.

### Other agents

For Antigravity and other harnesses that read skill directories, clone the repo and link each
skill you want from `plugins/hardware-lab/skills/<name>` into your skills root. The
[top-level README](../../README.md#installing) has the paths for each harness.

Skip all of this if you installed the `everything` plugin, which already includes these
skills. Installing both loads every skill twice.

## Requirements

A Unix-like shell. The Cynthion skills need the Cynthion hardware and the tools
`cynthion-setup` installs; `mcci-3411` needs the MCCI device and `usbiotest`; `bus-pirate`
and `siglent-scope` need only the instrument, on a serial port or the network.

## The Cynthion pipeline

The four Cynthion skills form one pipeline and hand off to each other by name:

1. **`cynthion-setup`** — install and verify the prerequisites once per machine: the
   `cynthion` CLI, the Packetry GUI, `tshark`, and the Linux udev rules. The other Cynthion
   skills send you here when a tool is missing.
2. **`cynthion-capture`** — verify the device, load the analyzer bitstream, wire the host and
   the target, then capture. Use Packetry for a GUI session, or capture headless to `.pcap`
   with the bundled Rust (`scripts/capture-rs`) or Python (`scripts/capture.py`) tools. For
   long soak runs, `scripts/rolling_capture.py` keeps a bounded ring of capture files;
   `scripts/index_pcap.py` builds a quick index over a capture.
3. **`cynthion-pcap-decode`** — decode, summarize, and diff `.pcap`/`.pcapng` files from
   Packetry or Cynthion: endpoints, descriptors, transfer sequences, and what changed between
   two captures (`scripts/decode.py`, `scripts/diff.py`). Every other skill that reads a
   capture imports this decoder.
4. **`cynthion-reverse-engineer`** — run a structured protocol reverse-engineering session:
   capture, diff transactions across stimuli (`scripts/diff_transactions.py`), infer the
   command structure (`scripts/infer_commands.py`), and write it up
   (`scripts/gen_protocol_doc.py`). Then generate a replay script (`scripts/gen_replay.py`)
   and a Facedancer emulation scaffold (`scripts/gen_facedancer_clone.py`). `example/` holds
   a worked session. For plain capture analysis, use `cynthion-pcap-decode` directly.

**`usb-device-profile`** feeds the pipeline from the other side. It reads a device's driver
source and writes a device-profile JSON (endpoint transfer types, directions, max packet sizes
per configuration), so the decoder can type endpoints when the enumeration traffic was not
captured.

### How the scripts find each other

`cynthion-capture` and `cynthion-reverse-engineer` import the decoder through a small
`scripts/_sibling.py` shim, not a hard-coded path. It looks, in order, at:

1. `$CYNTHION_PCAP_DECODE_SCRIPTS`
2. a `$PUBLIC_SKILLS_REPO` clone (every `plugins/*/skills/` tree, then a flat `skills/`)
3. the sibling directory in the same skills tree
4. the usual per-harness skills roots

Installing the whole theme keeps the skills siblings, which works with no configuration.

## Bench instruments

- **`bus-pirate`** — drive a Bus Pirate 5, 5XL or 6 from its terminal or a host script.
  - Covers transaction syntax, mode selection, the IO pinout, the programmable power supply
    and pull-ups, per-pin voltage measurement, the logic analyzer, and the BPIO2 binary
    scripting port.
  - Probe, sniff, scan, and bit-bang I2C, SPI, UART, 1-Wire, 2-wire, 3-wire, and JTAG/SWD;
    dump EEPROMs and flash; tell the two serial ports apart.
  - Bus Pirate 5 and later only; the classic v3.x firmware is a different device. Detailed
    command references live under `references/`.
- **`mcci-3411`** — operate an MCCI Model 3411 "Merganser" USB 3.2 Gen2 test device: find and
  drive its FTDI control port and on-device RTEMS shell, switch between the loopback, USB-IF
  compliance, and multi-bulk personalities, and run host-side throughput and data-integrity
  tests with `usbiotest` (`scripts/mcci3411.py`). It also explains the VID/PID confusion
  between the control and data ports, which is the first thing that goes wrong.
- **`siglent-scope`** — remote-control a Siglent SDS1000X-E series oscilloscope over the
  network: SCPI essentials, screenshots, deep-memory waveform transfer, and the firmware
  quirks that hang naive clients.
