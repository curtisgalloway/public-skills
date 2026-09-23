<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# QEMU differential validation: an Intel e1000 driver from a spec

Status: **approved design**, 2026-09-22 (user approved; decisions D1–D4 resolved below). No
source has been pinned, no spec written, and nothing has run. This is the design for milestone L02 in the
[implementation plan](IMPLEMENTATION-PLAN.md).

## Terms

- **QEMU** — an open-source machine emulator; its *device models* are software imitations of
  real hardware that a guest operating system drives as if it were the real device.
- **Device model** — here, QEMU's e1000 implementation. It is a third implementation of the
  hardware, written from the same manual, not the silicon.
- **Guest** — the Linux system running inside QEMU.
- **MMIO** — memory-mapped I/O: the driver reads and writes device registers as memory.
- **Register trace** — QEMU's log of every guest read and write to the device's registers.
- **Descriptor ring** — a circular list in host memory through which the driver hands buffers
  to the device and the device reports completed packets (DMA).
- **Differential test** — run the reference driver and the candidate under identical
  scenarios and compare outcomes and register traces.
- **`[emulated]`** — proposed evidence class for a result observed on a QEMU device model.
- **KVM / TCG** — hardware-assisted virtualization / QEMU's slower software emulation.

See the [glossary](../../GLOSSARY.md), the [evidence model](DESIGN.md#evidence-model-what-we-trust-and-why),
and the [L01 result](evidence/L01.md).

## Problem and outcomes

L01 showed that an agent can write a correct-looking ENC28J60 driver from a spec: all 64
critical answer-key requirements implemented, two integration bugs, and two spec defects
caught by the implementer. It left two questions open:

1. **Does the process hold for a harder device?** The ENC28J60 is a small SPI controller with
   no DMA. Most real drivers manage descriptor rings, PCI configuration, DMA ownership, and
   interrupt moderation, where bugs are subtle and ordering matters.
2. **Can the reference comparison run without a bench?** L01's hardware unit is blocked on a
   physical fixture. Every future device would be too.

L02 answers both with the Intel e1000 (82540EM), which has a public programming manual, a
mainline Linux driver, and a long-standing QEMU device model.

| ID | Outcome |
| --- | --- |
| O1 | A verified, source-anchored spec for the e1000 core network path, written by the existing spec skills from the Linux driver and the Intel manual. |
| O2 | A candidate driver written from that spec by an implementer who never read the Linux e1000 driver or the QEMU model. |
| O3 | A scripted QEMU harness that boots a guest, runs the same scenarios against the reference and the candidate driver, and captures outcomes, register traces, and packets. |
| O4 | A differential report: behavior against expectations from the manual, and register-trace divergences classified with the manual as tie-breaker. |
| O5 | Evidence that the tests detect planted defects, and every result folded back into a versioned working copy of the spec. |

## Non-goals

- Correctness on real silicon. A QEMU pass means "consistent with the device model", which is
  weaker than `[hardware]` (see *Evidence class* below).
- Offloads and advanced features: TSO, checksum offload, VLAN filtering, jumbo frames,
  Wake-on-LAN, and 8254x variants other than the 82540EM.
- The e1000e (82574L) and MSI-X. A later milestone may extend the harness to it.
- Performance and throughput tuning.
- A general harness for every device. L02 builds the e1000 case; generalizing it into a skill
  waits for a second device.

## Current state (observed 2026-09-22)

- **Test host** (x86-64, 32 cores, 122 GB RAM, Ubuntu): QEMU 10.2.1 with device models
  `e1000` (alias `e1000-82540em`), `e1000-82544gc`, `e1000-82545em`, and `e1000e`; 142
  `e1000*` trace events; the generic `memory_region_ops_read`/`_write` register-trace events.
  At first check `/dev/kvm` was not accessible to the working user and `make`, `flex`, and
  `bison` were missing; after D1 and D2 the user is in the `kvm` group, a QEMU `q35` machine
  starts with `-accel kvm`, and the build tools plus `libelf-dev` and `libssl-dev` are
  installed. `gcc` 15.2 is present; there is no container runtime.
- **Workstation**: no QEMU installed.
- **Reusable from L01**: the pinned Linux v6.12 source archive and its tree verifier, the
  implementer brief and command-log audit pattern, the review arrangement (reference review,
  requirements review, `review-swarm`, repair review), and the evidence conventions.

## Architecture

```
 Intel manual ─┐                      ┌──> candidate driver ─┐
               ├─> spec (verified) ───┤                      ├─> QEMU harness ─> differential report
 Linux e1000 ──┘                      └──> (reference driver)┘         │                │
                                                                       └── mutations ───┤
                                                               spec working copy <──────┘
```

### 1. Sources and pins

- **Linux v6.12 `drivers/net/ethernet/intel/e1000/`** from the same verified archive L01 used.
- **Intel PCI/PCI-X Family of Gigabit Ethernet Controllers Software Developer's Manual**
  (8254x), edition and SHA-256 pinned at acquisition.
- **The QEMU e1000 model is deliberately *not* a spec source.** If the spec were written from
  the model, the test would share its errors and pass trivially. Keeping the model out of the
  spec keeps the harness an independent check.

### 2. Spec

`cleanroom-spec` with `os-investigator` produce a spec for the core path: PCI discovery and
BAR mapping, reset, EEPROM MAC read, PHY/link, receive and transmit descriptor rings (legacy
format), interrupt cause/mask and throttling, statistics registers, and teardown.
`spec-verifier` runs two fresh readers on the result. The implementer receives the spec and
the manual.

A small **blind requirement list** (about 50 critical rows, written from the manual before
the spec exists) gives a cheap recall check, the lightweight version of the ENC28J60 ledger.

### 3. Implementation

As in L01: a fresh implementer with the spec, the manual, and kernel `include/` and
`Documentation/` only, with `drivers/` withheld (which also withholds every other Intel
driver). It must not read the Linux e1000 driver or any QEMU source; access is checked by
auditing its tool log. Module name `e1000_l02`, so it coexists with the stock module.

### 4. Harness

- **Guest:** an x86-64 Linux v6.12 kernel built with the reference `e1000` as a module and a
  minimal initramfs (a busybox userland plus test scripts). Both modules load in the same guest
  image, one at a time.
- **Machine:** `qemu-system-x86_64 -M q35` with `-device e1000,netdev=...`, KVM if available,
  otherwise TCG.
- **Peer:** a second QEMU guest with a known-good virtio-net device, joined by a
  point-to-point socket network. The peer generates and checks traffic, so results do not
  depend on QEMU's user-mode networking.
- **Capture per run:** the register trace (`memory_region_ops_read/write`, filtered to the
  e1000 BAR, plus the model's `e1000*` events), a packet capture on both sides
  (`filter-dump`), the guest console, and each scenario's pass/fail.
- **Link events:** QEMU's monitor `set_link` toggles the link, which exercises link-change
  interrupts without hardware.

### 5. Scenarios

Probe and MAC address from EEPROM; link up and down; transmit and receive at 60, 61, 1513,
and 1514 bytes; enough packets to wrap both rings several times; a receive flood that
overruns the ring and recovers; 20 stop/start cycles; interface down during traffic; module
unload and reload; interrupt-throttling register programmed and read back.

### 6. Comparison rule

Expected outcomes come from the manual and the spec, not from the reference driver. L01
showed the reference has its own defects (eight in the ENC28J60 driver). Register traces are
normalized (offsets, masked values, per-phase grouping) and compared on required operations,
order, and side effects, not exact equality. Each divergence is classified the way
`reference-driver-review` does: `[bug]`, `[benign]`, `[suspect]`, or `[ref-issue]`, with the
manual as tie-breaker.

### 7. Mutations

Before trusting a test, a planted defect must make it fail. Examples: receive tail written one
descriptor early, transmit descriptor command bits wrong, interrupt mask never restored, ring
length off by one descriptor.

### 8. Feedback

Every `[emulated]` result and every spec gap goes into a versioned working copy of the spec,
following the update loop in the evidence model. The accepted spec is never edited in place.

## Evidence class: `[emulated]` (proposed)

| Trusted for | Assumes | Failure modes |
| --- | --- | --- |
| How a driver behaves against the device model under stated scenarios | The model implements the behavior under test as the manual describes | Models are often lenient (accept wrong programming), omit errata and timing, and may copy the same misreading as the Linux driver. A pass is weaker than `[hardware]`; a failure that the manual explains is strong evidence. |

Adding the class to the format is part of L02, once the first results show how it is used.

## Isolation

The implementer must not read the Linux e1000 driver, other Intel drivers, or QEMU source.
QEMU is installed on the test host as a binary package, not source; the implementer works on
the workstation. The QEMU model and the reference driver are read only by the evaluator side.

## Decisions

| ID | Decision | Resolution (2026-09-22) |
| --- | --- | --- |
| D1 | KVM access on the test host | Working user added to the `kvm` group; KVM verified |
| D2 | Kernel build tools on the test host | `make`, `flex`, `bison`, `libelf-dev`, `libssl-dev` installed and verified |
| D3 | Implementer model | Approved as designed: chosen by the user at launch; a Claude implementer shares the reviewers' model family, which the evidence must say |
| D4 | Blind requirement list | Approved: author the ~50-row list from the manual before the spec exists |

## Risks

- **Model leniency hides bugs.** Mitigated by expectations taken from the manual, register-
  trace review, and mutation checks. Residual risk remains, and the evidence class says so.
- **Scope growth.** The Linux e1000 driver is large and covers many chip variants. The spec
  and the candidate are held to the 82540EM core path.
- **Nondeterminism.** Timer-driven behavior (watchdog, throttling) varies between runs.
  Scenarios assert outcomes, not timing; traces are compared per phase, not by timestamp.
- **Shared blind spots.** The reference driver and the QEMU model may share a misreading of
  the manual. Only the manual, and eventually hardware, can break that tie.

## Acceptance criteria

| ID | Criterion |
| --- | --- |
| A1 | The spec covers the core path, with two verification readings and no unresolved FAIL. |
| A2 | The candidate builds warning-free against the pinned tree, and its command-log audit is clean. |
| A3 | The harness runs every scenario unattended on the test host against both drivers, and stores traces, captures, and verdicts per run. |
| A4 | The reference driver passes the scenarios. Any reference failure is explained by the manual before the candidate is judged. |
| A5 | Every candidate scenario result is recorded; failures are repaired within an agreed repair cap or recorded as open findings. |
| A6 | Each planted defect is detected by at least one scenario or trace check. |
| A7 | The spec working copy records every spec gap and `[emulated]` result, and the evidence file separates spec gaps, spec errors, implementation errors, and model limitations. |

## Verification strategy

The harness is itself tested before it judges anything: the reference driver must pass (A4),
and the planted defects must fail (A6). Spec quality is measured by the blind list's recall
(D4) and the implementer's filed gaps. Driver quality is measured by the scenarios, the
register-trace comparison, and the same independent reviews L01 used.
