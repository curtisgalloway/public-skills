# Cynthion Pipeline — Architecture Decisions

Decisions reached during design sessions for the hardening and expansion of the
Cynthion USB capture/analysis pipeline. This document records what was settled,
what was deferred, and the reasoning behind each call. It is a living record —
update it as decisions change, noting what changed and why.

---

## Scope

The pipeline consists of three layers of sibling skills in `public-skills`:

- **`cynthion-capture`** — USB capture, rotation, indexing, clock sync
- **`cynthion-pcap-decode`** — shared USB decoder (one decoder, multiple consumers)
- **`cynthion-anomaly-analysis`** — stuck-device fault analysis (new, not yet built)
- **`cynthion-reverse-engineer`** — contrast-based protocol inference (existing)
- **`usb-device-profile`** — generates per-device endpoint configuration profiles

---

## Capture layer (`cynthion-capture`)

### SOF handling — keep all data

SOF tokens (PID 0xA5) **must not be dropped at capture time**. Dropping them was
implemented as a storage optimization but is incorrect for this use case: SOF
cessation is a primary host-controller-hang signature, and the analysis pipeline
needs the raw wire data. The unconditional SOF drop added in the session of
2026-05-23 must be reverted.

The SOF liveness track (A4 in the hardening doc) — a cheap downsampled
last-SOF-timestamp-per-millisecond sidecar alongside each segment — remains
valuable as a derived signal and should still be implemented. It gives the anomaly
skill a pre-computed controller-liveness signal without forcing it to scan every
packet. But it is a *derived* product, not a replacement for the raw data.

If storage is a concern in specific deployments, a `--no-sof` flag is acceptable
as an opt-in, but the default must be to retain SOFs.

### Compression

gzip compression of segment files (`.pcap.gz`) is correct and stays. Wireshark
and tshark read these natively. The `--no-compress` escape hatch is acceptable
but not currently implemented.

### Clock synchronization

`--target-host [USER@]HOST` is implemented: SSHes to the target at capture start,
runs 5 minimum-RTT probes (`date +%s%N`), stores `offset_s` / `uncertainty_s` /
`rtt_s` in `manifest.json` under `clock_sync`. Sign convention:
`offset_s = target_clock - capture_clock` (positive → target is ahead). Subtract
`offset_s` from target syslog timestamps, or add it to pcap timestamps, to align
both timelines.

### Hardware timestamps (deferred)

The per-frame hardware timestamp (`ts_be`, 16-bit big-endian) is currently
discarded; records are stamped with `time.time()` at parse time, introducing
buffering and gzip jitter. Fixing this (A3 in the hardening doc) requires
confirming tick units and rollover width from Packetry's `cynthion.rs` before
implementation. Deferred until the decoder replacement (B) is underway, since
that work requires reading the same source.

---

## Decoder replacement (`cynthion-pcap-decode`)

### Fork Packetry; subprocess binding

The current `decode.py` is hand-rolled and discards failed/incomplete transactions
(NAKs, STALLs, NYETs, never-completed transfers), making it unfit for fault
analysis. The decoder will be replaced with a binding driving Packetry's decode
core (`decoder.rs`, `usb.rs`, enough of `capture.rs` to read a pcap).

**Binding approach: subprocess, not PyO3.** The Rust binary reads a `.pcap.gz`
segment, runs the Packetry decoder, and writes newline-delimited JSON to stdout.
Python `stream_*` wrappers read that stream and yield objects compatible with
today's `Packet` / `Transaction` / `Transfer` interface. Rationale: the use case
is per-segment batch processing, not real-time streaming. A subprocess keeps the
Rust build step out of the Python skill install, avoids Python-version coupling,
and preserves a clean boundary between the decode core and all consumers. The
performance cost of JSON-per-transfer is negligible because consumers iterate
transfers, not raw packets — the count difference is orders of magnitude.

**Architecture: Rust decodes, Python orchestrates.** The decode core (Packetry
fork) is in Rust; all consumers (index_pcap.py, reverse-engineer scripts, anomaly
skill) stay in Python. This is intentional: different consumers have very different
use cases (payload-centric reverse engineering vs. status-centric fault analysis)
and keeping the decode layer neutral serves both.

**The pure-Python decoder stays as a labelled fallback** but must not be the
analysis path.

### Requirements for the new decoder

- Failed and incomplete transactions surface as first-class results with status
  (NAK, STALL, NYET, no-handshake). These must not be filtered.
- Transfer and Transaction objects carry: completion status, handshake PID, retry
  and NAK counts, short-packet flag, raw PIDs.
- Correct transfer typing (bulk vs. interrupt) from the device profile endpoint
  map rather than hardcoded guesses.
- Device profile seeding before packet processing so enumeration-free segments
  decode correctly.
- Absolute timestamps from hardware-derived per-frame timestamps (A3).
- Contract violation flagging: on-wire behavior contradicting the device profile
  (wrong endpoint direction, impossible packet size) is recorded as a flagged
  event, not silently ignored.

### Segment boundary state

A transfer straddling a rotation boundary looks identical to a never-completed
transfer to a cold-started per-segment decoder. The decoder/index must record
boundary state (transfers open at end-of-segment, transfers partial at
start-of-segment) into the index and manifest. Reconciliation of these boundary
artifacts is the anomaly skill's responsibility, not the decoder's.

---

## Device profile (`cynthion-device-profile`)

### Purpose

A device profile is a JSON file that encodes the static structural knowledge about
a USB device's endpoint configuration. Its sole purpose is to seed the decoder
with endpoint type information when the capture does not include the enumeration
phase (SET_CONFIGURATION + descriptor exchange). It is *not* a behavioral contract;
it contains no expectations about NAK rates, latency, or error frequency.

Behavioral expectations may be added in a separate section later. Do not mix
structural facts and learned baselines in the same file.

### Format

```json
{
  "device": {
    "vid": 6353,
    "pid": 43981,
    "name": "Codename",
    "speed": "full"
  },
  "configurations": [
    {
      "index": 1,
      "description": "Normal operation",
      "interfaces": [
        {
          "number": 0,
          "class": 255,
          "description": "Vendor bulk data",
          "endpoints": [
            { "address": 1,   "direction": "out", "type": "bulk",      "max_packet_size": 512 },
            { "address": 129, "direction": "in",  "type": "bulk",      "max_packet_size": 512 },
            { "address": 130, "direction": "in",  "type": "interrupt", "max_packet_size": 8   }
          ]
        }
      ]
    },
    {
      "index": 2,
      "description": "DFU mode",
      "interfaces": []
    }
  ]
}
```

**Field notes:**

- All numeric values are integers. `address` follows USB encoding: bit 7 set (≥128)
  means IN; bit 7 clear (<128) means OUT. `direction` is redundant with `address`
  but kept explicit for readability and validation.
- `type` is one of `"control"`, `"bulk"`, `"interrupt"`, `"isochronous"`.
- `speed` is one of `"low"`, `"full"`, `"high"`.
- `class` is the USB interface class code as an integer (255 = vendor-specific).

### Endpoint numbers are guidance, not authoritative

In Fuchsia, endpoint addresses are allocated dynamically by `usb-peripheral` across
loaded functions. In CircuitPython, they are assigned in interface registration
order. In both cases, the address in the profile is the expected value derived from
source analysis, but the active configuration might use different addresses if the
dynamic allocator assigned them differently.

The decoder uses profile endpoint numbers as a prior for pre-seeding. When
enumeration is captured, the observed addresses take precedence. When enumeration is
missed, the profile addresses are used as-is. The inference step (which scores
observed traffic against configurations to determine which is active) is not yet
implemented; the profile format is designed to support it.

### Multiple configurations

The `configurations` array supports devices with more than one USB configuration.
Configurations that differ in structure (endpoint count, transfer types) are
distinguishable from traffic alone. Configurations that differ only in endpoint
addresses may be ambiguous without an observed SET_CONFIGURATION. The profile
should include all known configurations regardless.

---

## Anomaly analysis (`cynthion-anomaly-analysis`)

Not yet implemented. Defined as a new sibling skill, separate from both
`index_pcap.py` (lightweight per-segment index) and `cynthion-reverse-engineer`
(contrast-based, payload-centric). The anomaly skill is single-capture, temporal,
and status-centric: NAK rates, never-completed transfers, SOF cessation, gap
statistics, device-vs-controller discriminator.

It consumes the fixed decoder via `_sibling.import_decode()` and the device
profile for endpoint semantics and (eventually) behavioral contract validation.

---

## What is deferred

- **Behavioral expectations in the device profile.** An `expectations` section may
  be added later for per-endpoint NAK rate bounds, normal latency ranges, etc. Do
  not add it until the anomaly skill has a concrete need.
- **Hardware timestamp anchoring (A3).** Requires confirming Cynthion tick units
  from `cynthion.rs`. Do after starting the decoder replacement.
- **SOF liveness track (A4).** Implement alongside or after A3 since it depends on
  hardware timestamps.
- **Reader/writer thread split in rolling_capture.py (A1).** Highest priority
  capture hardening item, but not yet started.
- **Configuration inference.** Matching observed traffic to a configuration when
  SET_CONFIGURATION was not captured. The profile format supports it; the logic
  belongs in the anomaly skill or decoder, not the profile generator.
- **Alternate interface settings.** USB SET_INTERFACE / alternate settings not yet
  in the profile format. Add when a device under test requires them.
