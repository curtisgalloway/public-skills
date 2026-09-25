<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# e1000 QEMU harness

Runs a Linux e1000 driver against QEMU's emulated Intel 82540EM and records what happened, so
the reference driver and a candidate written from the spec can be compared
([design](../../../QEMU-DIFFERENTIAL.md), plan units L02d1 and L02d2).

## Terms

- **DUT** (device under test) — the guest whose emulated e1000 is driven by the module being
  tested.
- **Peer** — a second guest with a virtio-net card, the known-good end of the link.
- **Register trace** — QEMU's log of every guest read and write to the e1000's registers.
- **Scenario** — a named sequence of guest commands and checks. Its verdict is PASS, FAIL
  (a guest misbehaved, which a driver can cause) or ERROR (the harness or the host did).
- **Run directory** — one fresh directory per harness run holding everything it produced;
  `--out` must not exist yet.

See the [glossary](../../../../../GLOSSARY.md).

## What it does

`l02harness.py run` builds one initramfs (static busybox, [`guest-init.sh`](guest-init.sh), and
the given modules), boots the DUT and the peer as two `q35` guests joined by a
point-to-point datagram socket, and runs the scenarios in order. Each guest serves shell
commands over its second serial port, so a scenario runs on the host and can drive either
guest, and the DUT's QEMU monitor, between steps. The DUT loads no driver until a scenario
tells it to.

A run directory holds:

| File | Contents |
| --- | --- |
| `verdicts.json` | Overall verdict, per-scenario verdicts with each check, trace counts |
| `identities.json` | SHA-256 of the kernel, initramfs, busybox, modules, harness files and QEMU binary; QEMU version |
| `dut-regtrace.log` | e1000 MMIO, I/O-port and PCI-configuration accesses, and the model's `e1000*` events |
| `dut-trace-raw.log.gz` | The unfiltered QEMU trace |
| `dut.pcap`, `peer.pcap` | Every frame on each side's link, from QEMU's `filter-dump` |
| `*-console.log`, `*-cmds.jsonl` | Each guest's kernel console; every scenario command with its output and host timestamps |
| `dut-dmesg-NN-smoke.txt` | The DUT's kernel log at the end of the smoke scenario in position NN |
| `initramfs.cpio.gz`, `*-argv.json`, `*-qemu.log` | The guests' initramfs, each QEMU command line, and QEMU's own output |

When `smoke` ran, a `capture` pseudo-scenario checks the stored files themselves: the trace
holds e1000 register reads and writes and accesses to the EEPROM interface (EECD or EERD).
When `smoke` passed, it also checks that each packet capture holds the pings in both
directions. The EEPROM check shows that the driver used the EEPROM, not that the MAC came from
it; tying register values to results is L02d2's trace comparison.

Exit status: 0 every scenario passed; 1 a scenario FAILed; 2 bad arguments or inputs, a guest
that never booted (the DUT has no driver loaded then, so it cannot be the driver's fault), or
an exception in the harness (ERROR; the run stops there). A guest that stops answering, whose
command channel breaks, or whose QEMU exits FAILs its scenario and is not used again; the
harness kills any QEMU that does not power off. `verdicts.json` is written in every case
except a setup error found before the run directory exists, a failure to read the inputs or
write the run's own files (a full disk, for example), which also exits 2, or an interrupt
after the scenarios have finished.

## Scenarios

| Name | Checks |
| --- | --- |
| `smoke` | Module loads and binds; the interface's MAC matches the one QEMU was given; carrier within 15 s; three pings each way with no loss; `rmmod` succeeds |
| `selftest-hang` | Harness self-test. PASS when a guest command that never returns gets the DUT reported dead after its timeout; later scenarios in the run then FAIL |
| `selftest-panic` | Harness self-test. PASS when a guest kernel panic (SysRq crash) gets the DUT reported dead; later scenarios then FAIL |

The design's full scenario list and the planted defects arrive in L02d2.

## Running it

On the test host (x86-64 Linux, KVM recommended, QEMU 10.2.1, a static busybox, Python 3.10+), with a
v6.12 kernel built with `CONFIG_E1000=m`, virtio-net, devtmpfs and initrd support:

```bash
python3 l02harness.py run --kernel obj/arch/x86/boot/bzImage \
  --module obj/drivers/net/ethernet/intel/e1000/e1000.ko --driver e1000 --out runs/r001
```

`--driver` names both the module to load and the PCI driver it must bind as; the candidate
is `--module .../e1000_l02.ko --driver e1000_l02`. `--scenario` repeats to choose and order
scenarios. `--accel` defaults to `auto`: KVM when `/dev/kvm` is usable, otherwise TCG with a
warning, since the scenarios' timeouts assume KVM speed. The choice is recorded in
`identities.json`.

The unit tests cover the parts that need no QEMU:
`python3 -m unittest discover -s tests -v`.
