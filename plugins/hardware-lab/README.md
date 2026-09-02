# hardware-lab

Bench and USB-analysis skills: capture USB traffic with a Cynthion, decode and diff the
captures, reverse-engineer a proprietary device's protocol, profile a device from its driver
source, drive an MCCI 3411 USB 3.2 test device, poke buses with a Bus Pirate, and control a
Siglent oscilloscope from a script.

```
/plugin install hardware-lab@public-skills
```

Antigravity and other harnesses that read skill directories: link the skill you want from
`plugins/hardware-lab/skills/<name>` into your skills root.

## The Cynthion pipeline

The four Cynthion skills form one pipeline and hand off to each other by name:

1. **`cynthion-setup`** — install and verify the prerequisites once per machine: the `cynthion`
   CLI, the Packetry GUI, `tshark`, and the Linux udev rules. The other Cynthion skills send you
   here when a tool is missing.
2. **`cynthion-capture`** — verify the device, load the analyzer bitstream, wire the host and the
   target, then capture: Packetry for a GUI session, or headless capture to `.pcap` with the
   bundled Rust (`scripts/capture-rs`) or Python (`scripts/capture.py`) tools.
   `scripts/rolling_capture.py` keeps a bounded ring of capture files for long soak runs, and
   `scripts/index_pcap.py` builds a quick index over a capture.
3. **`cynthion-pcap-decode`** — decode, summarize, and diff `.pcap`/`.pcapng` files from Packetry
   or Cynthion: endpoints, descriptors, transfer sequences, and what changed between two
   captures (`scripts/decode.py`, `scripts/diff.py`). Every other skill that reads a capture
   imports this decoder.
4. **`cynthion-reverse-engineer`** — orchestrate a structured protocol reverse-engineering
   session: capture, diff transactions across stimuli (`scripts/diff_transactions.py`), infer the
   command structure (`scripts/infer_commands.py`), write it up
   (`scripts/gen_protocol_doc.py`), then generate a replay script (`scripts/gen_replay.py`) and a
   Facedancer emulation scaffold (`scripts/gen_facedancer_clone.py`). The `example/` directory
   is a worked session. Use `cynthion-pcap-decode` directly for plain capture analysis.

**`usb-device-profile`** feeds the pipeline from the other side: it reads a device's driver
source and writes a device-profile JSON (endpoint transfer types, directions, max packet sizes
per configuration) so the decoder can type endpoints when the enumeration traffic was not
captured.

### How the scripts find each other

`cynthion-capture` and `cynthion-reverse-engineer` import the decoder through a small
`scripts/_sibling.py` shim rather than a hard-coded path. It looks, in order, at
`$CYNTHION_PCAP_DECODE_SCRIPTS`, at a `$PUBLIC_SKILLS_REPO` clone (every `plugins/*/skills/`
tree, then a flat `skills/`), at the sibling directory in the same skills tree, and finally at
the usual per-harness skills roots. Installing the whole theme keeps them siblings, which is the
case that works with no configuration.

## Bench instruments

- **`bus-pirate`** — drive a Bus Pirate 5, 5XL or 6 from its terminal or a host script:
  transaction syntax, mode selection, the IO pinout, the programmable power supply and
  pull-ups, per-pin voltage measurement, the logic analyzer, and the BPIO2 binary scripting
  port. Covers probing, sniffing, scanning, and bit-banging I2C, SPI, UART, 1-Wire, 2-wire,
  3-wire, and JTAG/SWD, dumping EEPROMs and flash, and telling the two serial ports apart.
  Bus Pirate 5 and later only; the classic v3.x firmware is a different device. Detailed
  command references live under `references/`.
- **`mcci-3411`** — operate an MCCI Model 3411 "Merganser" USB 3.2 Gen2 test device: find and
  drive its FTDI control port and on-device RTEMS shell, switch between the loopback, USB-IF
  compliance, and multi-bulk personalities, and run host-side throughput and data-integrity
  tests with `usbiotest` (`scripts/mcci3411.py`). Explains the VID/PID confusion between the
  control and data ports, which is the first thing that goes wrong.
- **`siglent-scope`** — remote-control a Siglent SDS1000X-E series oscilloscope over the
  network: SCPI essentials, screenshots, deep-memory waveform transfer, and the firmware quirks
  that hang naive clients.

## Requirements

Everything here assumes a Unix-like shell. The Cynthion skills need the Cynthion hardware and
the tools `cynthion-setup` installs; `mcci-3411` needs the MCCI device and `usbiotest`;
`bus-pirate` and `siglent-scope` need only the instrument on a serial port or the network.
