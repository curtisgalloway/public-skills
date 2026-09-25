#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""QEMU harness for the L02 e1000 differential test.

Boots two guests on the test host from one kernel and one initramfs:

- the DUT, a q35 guest with an emulated e1000 (82540EM) whose driver module is loaded by
  a scenario, with every e1000 register access traced;
- the peer, a q35 guest with a virtio-net device, the known-good end of the link.

The guests share a point-to-point datagram socket network. Each runs guest-init.sh, which
serves shell commands over a second serial port, so scenarios run on the host and can drive
either guest and the QEMU monitor between steps. Everything a run produces lands in its run
directory: consoles, command logs, the raw and filtered register traces, a packet capture
per side, artifact identities, and verdicts.json.

Exit status: 0 every scenario passed; 1 a scenario failed (FAIL: a guest misbehaved,
which a driver can cause); 2 a usage, setup or harness error (ERROR: bad inputs, a
guest that never booted, or an exception in the harness itself).
Stdlib only; Python 3.10 or newer.
"""

from __future__ import annotations

import argparse
import dataclasses
import gzip
import hashlib
import io
import json
import os
import platform
import re
import shutil
import socket
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
DUT_MAC = "52:54:00:12:34:56"
PEER_MAC = "52:54:00:12:34:57"
DUT_IP = "192.0.2.1"
PEER_IP = "192.0.2.2"
TRACE_EVENTS = (
    "memory_region_ops_read",
    "memory_region_ops_write",
    "pci_cfg_read",
    "pci_cfg_write",
    "e1000*",
)
E1000_REGIONS = ("'e1000-mmio'", "'e1000-io'")
# The trace logs absolute addresses; BAR0 is 128 KiB and naturally aligned, so an
# address modulo its size is the register offset. EECD (0x10) and EERD (0x14) are the
# two ways the 82540EM's EEPROM can be read.
E1000_BAR0_SIZE = 0x20000
EEPROM_REGS = (0x10, 0x14)


class HarnessError(Exception):
    """A setup problem: the run cannot start or cannot be judged."""


class GuestError(Exception):
    """A guest stopped answering: timeout, closed channel, or QEMU exit."""


# --- initramfs ------------------------------------------------------------------------


def cpio_newc(entries: list[tuple[str, int, bytes, int, int]]) -> bytes:
    """Returns a newc cpio archive of (name, mode, data, rdevmajor, rdevminor) entries.

    Every mtime, uid and gid is zero, so equal inputs give byte-identical archives.
    """
    out = io.BytesIO()

    def pad4(n: int) -> None:
        out.write(b"\0" * (-n % 4))

    for ino, (name, mode, data, rmaj, rmin) in enumerate(
        entries + [("TRAILER!!!", 0, b"", 0, 0)], start=1
    ):
        raw = name.encode() + b"\0"
        fields = (ino, mode, 0, 0, 1, 0, len(data), 0, 0, rmaj, rmin, len(raw), 0)
        header = b"070701" + b"".join(b"%08X" % f for f in fields)
        out.write(header + raw)
        pad4(len(header) + len(raw))
        out.write(data)
        pad4(len(data))
    return out.getvalue()


def build_initramfs(busybox: Path, modules: list[Path]) -> bytes:
    """Returns the gzip-compressed initramfs shared by both guests."""
    entries = []
    for d in ("bin", "dev", "lib", "lib/modules", "proc", "sys", "tmp"):
        entries.append((d, 0o040755, b"", 0, 0))
    entries.append(("dev/console", 0o020600, b"", 5, 1))
    entries.append(("init", 0o100755, (HERE / "guest-init.sh").read_bytes(), 0, 0))
    entries.append(("bin/busybox", 0o100755, busybox.read_bytes(), 0, 0))
    for m in modules:
        entries.append((f"lib/modules/{m.name}", 0o100644, m.read_bytes(), 0, 0))
    return gzip.compress(cpio_newc(entries), mtime=0)


# --- captures -------------------------------------------------------------------------


@dataclasses.dataclass
class Frame:
    ts: float
    data: bytes


def read_pcap(path: Path) -> list[Frame]:
    """Reads a classic little- or big-endian microsecond pcap file."""
    raw = path.read_bytes()
    if len(raw) < 24:
        return []
    magic = raw[:4]
    if magic == b"\xd4\xc3\xb2\xa1":
        end = "<"
    elif magic == b"\xa1\xb2\xc3\xd4":
        end = ">"
    else:
        raise HarnessError(f"{path}: not a pcap file")
    frames, off = [], 24
    while off + 16 <= len(raw):
        sec, usec, incl, _ = struct.unpack(end + "IIII", raw[off : off + 16])
        off += 16
        frames.append(Frame(sec + usec / 1e6, raw[off : off + incl]))
        off += incl
    return frames


def icmp_echoes(frames: list[Frame]) -> list[tuple[str, str, int, int]]:
    """Returns (src, dst, icmp type, frame length) for each IPv4 ICMP echo frame."""
    found = []
    for f in frames:
        d = f.data
        if len(d) < 14 + 20 + 8 or d[12:14] != b"\x08\x00" or d[23] != 1:
            continue
        # The DUT's frames come from the driver under test, so a header may lie.
        ihl = (d[14] & 0x0F) * 4
        if ihl < 20 or len(d) < 14 + ihl + 8:
            continue
        icmp_type = d[14 + ihl]
        if icmp_type in (0, 8):
            src = ".".join(str(b) for b in d[26:30])
            dst = ".".join(str(b) for b in d[30:34])
            found.append((src, dst, icmp_type, len(d)))
    return found


def empty_trace_counts() -> dict[str, int]:
    return {
        "mmio_read": 0,
        "mmio_write": 0,
        "eeprom": 0,
        "io": 0,
        "pci_cfg": 0,
        "model_event": 0,
    }


def filter_trace(raw_log: Path, out: Path) -> dict[str, int]:
    """Copies e1000 register accesses and e1000 model events to out; returns counts."""
    counts = empty_trace_counts()
    # QEMU 10.2.1 with -msg timestamp=on writes "<ISO time> <event> <args>"; other
    # builds of the log backend write "<pid>@<sec>.<usec>:<event> <args>" or no prefix.
    event = re.compile(r"^(?:\S+Z |\d+@\d+\.\d+:)?(\w+)(?: (\S+))?")
    addr = re.compile(r" addr 0x([0-9a-f]+) ")
    with raw_log.open(errors="replace") as src, out.open("w") as dst:
        for line in src:
            m = event.match(line)
            if not m:
                continue
            name = m.group(1)
            if name.startswith("memory_region_ops_"):
                if E1000_REGIONS[0] in line:
                    counts["mmio_read" if name.endswith("read") else "mmio_write"] += 1
                    a = addr.search(line)
                    if a and int(a.group(1), 16) % E1000_BAR0_SIZE in EEPROM_REGS:
                        counts["eeprom"] += 1
                elif E1000_REGIONS[1] in line:
                    counts["io"] += 1
                else:
                    continue
            elif name.startswith("pci_cfg_"):
                if m.group(2) != "e1000":
                    continue
                counts["pci_cfg"] += 1
            elif name.startswith("e1000"):
                counts["model_event"] += 1
            else:
                continue
            dst.write(line)
    return counts


# --- guests ---------------------------------------------------------------------------


class Guest:
    """One QEMU process and the command channel to its guest-init.sh."""

    def __init__(self, name: str, argv: list[str], rundir: Path):
        self.name = name
        self.argv = argv
        self.rundir = rundir
        self.proc: subprocess.Popen | None = None
        self.sock: socket.socket | None = None
        self.buf = b""
        self.seq = 0
        self.dead: str | None = None
        self.cmdlog = (rundir / f"{name}-cmds.jsonl").open("a")

    def start(self) -> None:
        (self.rundir / f"{self.name}-argv.json").write_text(
            json.dumps(self.argv, indent=1)
        )
        self.proc = subprocess.Popen(
            self.argv,
            stdin=subprocess.DEVNULL,
            stdout=(self.rundir / f"{self.name}-qemu.log").open("w"),
            stderr=subprocess.STDOUT,
        )

    def connect(self, deadline: float) -> None:
        """Connects to the command socket once QEMU has created it."""
        path = str(self.rundir / f"{self.name}-cmd.sock")
        while True:
            self._check_alive()
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.connect(path)
                self.sock = s
                break
            except OSError as e:
                s.close()
                if time.monotonic() > deadline:
                    raise GuestError(
                        f"{self.name}: command socket never appeared"
                    ) from e
                time.sleep(0.1)

    def wait_ready(self, deadline: float) -> None:
        """Waits for a READY line; the guest repeats it until its first command."""
        while not self._readline(deadline).startswith("L02 READY"):
            pass

    def _check_alive(self) -> None:
        if self.dead:
            raise GuestError(self.dead)
        if self.proc and self.proc.poll() is not None:
            self.dead = f"{self.name}: QEMU exited with status {self.proc.returncode}"
            raise GuestError(self.dead)

    def _readline(self, deadline: float) -> str:
        while b"\n" not in self.buf:
            self._check_alive()
            left = deadline - time.monotonic()
            if left <= 0:
                self.dead = f"{self.name}: no answer before the timeout"
                raise GuestError(self.dead)
            self.sock.settimeout(min(left, 0.5))
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            except OSError as e:
                # A reset or broken channel means the guest or its QEMU died, which a
                # driver can cause: a guest failure, not a harness error.
                self._check_alive()
                self.dead = f"{self.name}: command channel failed ({e})"
                raise GuestError(self.dead) from e
            if not chunk:
                self._check_alive()
                self.dead = f"{self.name}: command channel closed"
                raise GuestError(self.dead)
            self.buf += chunk
        line, self.buf = self.buf.split(b"\n", 1)
        return line.decode(errors="replace").rstrip("\r")

    def run(self, cmd: str, timeout: float = 30) -> tuple[int, str]:
        """Runs a shell command in the guest; returns (exit status, output)."""
        if "\n" in cmd:
            raise HarnessError("guest commands are single lines")
        self._check_alive()
        self.seq += 1
        seq = self.seq
        started = time.time()
        deadline = time.monotonic() + timeout
        end = re.compile(rf"^(.*)L02 END {seq} (\d+)$")
        out: list[str] = []
        try:
            try:
                self.sock.sendall(f"{seq} {cmd}\n".encode())
            except OSError as e:
                self.dead = f"{self.name}: command channel failed ({e})"
                raise GuestError(self.dead) from e
            while self._readline(deadline) != f"L02 BEGIN {seq}":
                pass
            while True:
                line = self._readline(deadline)
                m = end.match(line)
                if m:
                    if m.group(1):
                        out.append(m.group(1))
                    rc = int(m.group(2))
                    break
                out.append(line)
        except GuestError as e:
            self._log(seq, cmd, started, None, "\n".join(out), str(e))
            raise
        text = "\n".join(out)
        self._log(seq, cmd, started, rc, text, None)
        return rc, text

    def _log(self, seq, cmd, started, rc, out, error) -> None:
        self.cmdlog.write(
            json.dumps(
                {
                    "seq": seq,
                    "cmd": cmd,
                    "start": started,
                    "end": time.time(),
                    "rc": rc,
                    "out": out,
                    "error": error,
                }
            )
            + "\n"
        )
        self.cmdlog.flush()

    def stop(self, grace: float = 10) -> None:
        """Powers the guest off, or kills QEMU when it does not stop within grace seconds."""
        if self.proc is None:
            return
        if self.proc.poll() is None and self.sock and not self.dead:
            try:
                self.sock.sendall(b"0 poweroff -f\n")
            except OSError:
                pass
        try:
            self.proc.wait(grace)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        if self.sock:
            self.sock.close()
        self.cmdlog.close()


class Qmp:
    """A minimal QMP client for the DUT's monitor socket."""

    def __init__(self, path: Path):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(10)
        self.sock.connect(str(path))
        self.file = self.sock.makefile("rwb")
        self._recv()
        self.execute("qmp_capabilities")

    def _recv(self) -> dict:
        while True:
            msg = json.loads(self.file.readline())
            if "event" not in msg:
                return msg

    def execute(self, command: str, **arguments) -> dict:
        req = {"execute": command}
        if arguments:
            req["arguments"] = arguments
        self.file.write(json.dumps(req).encode() + b"\n")
        self.file.flush()
        reply = self._recv()
        if "error" in reply:
            raise HarnessError(f"QMP {command}: {reply['error']}")
        return reply.get("return", {})

    def close(self) -> None:
        self.file.close()
        self.sock.close()


def qemu_argv(role: str, args, rundir: Path, initrd: Path) -> list[str]:
    r = rundir
    net = {"dut": (DUT_MAC, "e1000"), "peer": (PEER_MAC, "virtio-net-pci")}[role]
    other = "peer" if role == "dut" else "dut"
    argv = [
        args.qemu,
        "-M",
        "q35",
        "-accel",
        args.accel,
        "-m",
        "512",
        "-smp",
        "2",
        "-nodefaults",
        "-no-reboot",
        "-display",
        "none",
        "-msg",
        "timestamp=on",
        "-kernel",
        str(args.kernel),
        "-initrd",
        str(initrd),
        "-append",
        f"console=ttyS0 panic=-1 l02.role={role}",
        "-chardev",
        f"file,id=con,path={r}/{role}-console.log",
        "-serial",
        "chardev:con",
        "-chardev",
        f"socket,id=cmd,path={r}/{role}-cmd.sock,server=on,wait=off",
        "-serial",
        "chardev:cmd",
        "-netdev",
        (
            f"dgram,id=n0,local.type=unix,local.path={r}/{role}-net.sock,"
            f"remote.type=unix,remote.path={r}/{other}-net.sock"
        ),
        "-device",
        f"{net[1]},netdev=n0,mac={net[0]},romfile=",
        "-object",
        f"filter-dump,id=d0,netdev=n0,file={r}/{role}.pcap",
    ]
    if args.accel == "kvm":
        argv += ["-cpu", "host"]
    if role == "dut":
        (r / "trace-events").write_text("\n".join(TRACE_EVENTS) + "\n")
        argv += [
            "-qmp",
            f"unix:{r}/dut-qmp.sock,server=on,wait=off",
            "-trace",
            f"events={r}/trace-events",
            "-D",
            f"{r}/dut-trace-raw.log",
        ]
    return argv


# --- scenarios ------------------------------------------------------------------------


@dataclasses.dataclass
class Ctx:
    dut: Guest
    peer: Guest
    qmp: Qmp
    driver: str
    rundir: Path
    step: int = 0  # 1-based position of the running scenario, for file names


Check = tuple[str, bool, str]


def wait_for(guest: Guest, cmd: str, want: str, timeout: float) -> tuple[bool, str]:
    """Polls cmd once a second until its output equals want; returns (ok, last output)."""
    deadline = time.monotonic() + timeout
    while True:
        rc, out = guest.run(cmd)
        if rc == 0 and out.strip() == want:
            return True, out.strip()
        if time.monotonic() > deadline:
            return False, out.strip()
        time.sleep(1)


def scenario_smoke(c: Ctx) -> list[Check]:
    """Probe, MAC, link, ping both ways, unload.

    The capture checks confirm afterwards that the driver used the EEPROM interface;
    they cannot show that the MAC came from it.
    """
    checks: list[Check] = []
    rc, out = c.dut.run(f"insmod /lib/modules/{c.driver}.ko")
    checks.append(("insmod", rc == 0, out))
    if rc != 0:
        return checks
    rc, out = c.dut.run(f"ls /sys/bus/pci/drivers/{c.driver}/ | grep ':'")
    checks.append(("bound to a PCI device", rc == 0 and out.strip() != "", out.strip()))
    rc, out = c.dut.run("cat /sys/class/net/eth0/address")
    checks.append(("MAC matches QEMU's", out.strip() == DUT_MAC, out.strip()))
    rc, out = c.dut.run(f"ip link set eth0 up && ip addr add {DUT_IP}/24 dev eth0")
    checks.append(("interface up", rc == 0, out))
    ok, out = wait_for(c.dut, "cat /sys/class/net/eth0/carrier", "1", 15)
    checks.append(("carrier within 15 s", ok, out))
    rc, out = c.dut.run(f"ping -c 3 -W 2 {PEER_IP}", timeout=20)
    checks.append(("DUT pings peer", rc == 0 and " 0% packet loss" in out, out))
    rc, out = c.peer.run(f"ping -c 3 -W 2 {DUT_IP}", timeout=20)
    checks.append(("peer pings DUT", rc == 0 and " 0% packet loss" in out, out))
    _, out = c.dut.run("dmesg")
    (c.rundir / f"dut-dmesg-{c.step:02d}-smoke.txt").write_text(out + "\n")
    rc, out = c.dut.run(f"ip link set eth0 down && rmmod {c.driver}")
    checks.append(("rmmod", rc == 0, out))
    return checks


def expect_dead(guest: Guest, cmd: str, timeout: float, *signs: str) -> list[Check]:
    """Runs cmd; passes only if the harness then reports the guest dead with a sign."""
    name = f"guest reported dead ({' or '.join(signs)})"
    if guest.dead:
        return [(name, False, f"already dead before the test: {guest.dead}")]
    try:
        rc, out = guest.run(cmd, timeout=timeout)
    except GuestError as e:
        return [(name, any(s in str(e) for s in signs), str(e))]
    return [(name, False, f"command returned {rc}: {out}")]


def scenario_selftest_hang(c: Ctx) -> list[Check]:
    """Harness self-test: a command that never returns marks the DUT dead.

    Passes when detection works. The DUT is unusable afterwards, so every later
    scenario in the run fails.
    """
    return expect_dead(c.dut, "sleep 600", 5, "no answer before the timeout")


def scenario_selftest_panic(c: Ctx) -> list[Check]:
    """Harness self-test: a guest kernel panic marks the DUT dead.

    Passes when detection works; later scenarios in the run fail.
    """
    rc, out = c.dut.run("cat /proc/sys/kernel/sysrq")
    if rc != 0:
        return [("magic SysRq available", False, out)]
    return expect_dead(
        c.dut,
        "echo c > /proc/sysrq-trigger",
        20,
        "channel closed",
        "channel failed",
        "QEMU exited",
    )


SCENARIOS: dict[str, Callable[[Ctx], list[Check]]] = {
    "smoke": scenario_smoke,
    "selftest-hang": scenario_selftest_hang,
    "selftest-panic": scenario_selftest_panic,
}


def capture_checks(rundir: Path, counts: dict[str, int], pinged: bool) -> list[Check]:
    """Checks that the stored captures hold what the run claims to have exercised."""
    checks: list[Check] = [
        ("register trace has e1000 MMIO writes", counts["mmio_write"] > 0, str(counts)),
        ("register trace has e1000 MMIO reads", counts["mmio_read"] > 0, str(counts)),
        (
            "register trace has EEPROM interface accesses (EECD/EERD)",
            counts["eeprom"] > 0,
            str(counts),
        ),
    ]
    if pinged:
        for side in ("dut", "peer"):
            echoes = icmp_echoes(read_pcap(rundir / f"{side}.pcap"))
            want = {
                (DUT_IP, PEER_IP, 8),
                (PEER_IP, DUT_IP, 0),
                (PEER_IP, DUT_IP, 8),
                (DUT_IP, PEER_IP, 0),
            }
            seen = {(s, d, t) for s, d, t, _ in echoes}
            checks.append(
                (
                    f"{side}.pcap has both pings' requests and replies",
                    want <= seen,
                    f"{len(echoes)} echo frames",
                )
            )
    return checks


# --- run ------------------------------------------------------------------------------


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identities(args, initrd: Path) -> dict:
    files = {"kernel": args.kernel, "initramfs": initrd, "busybox": args.busybox}
    files.update({f"module:{m.name}": m for m in args.module})
    files.update(
        {
            f"harness:{p.name}": p
            for p in (HERE / "l02harness.py", HERE / "guest-init.sh")
        }
    )
    files["qemu"] = args.qemu_path
    return {
        "sha256": {k: sha256(Path(v)) for k, v in files.items()},
        "paths": {k: str(v) for k, v in files.items()},
        "qemu_version": args.qemu_version,
        "host_kernel": platform.release(),
        "python": platform.python_version(),
        "driver": args.driver,
        "accel": args.accel,
        "scenarios": args.scenario,
    }


def resolve_host(args) -> None:
    """Finds the QEMU binary and its version, and picks the accelerator."""
    found = shutil.which(args.qemu)
    if not found:
        raise HarnessError(f"QEMU binary not found: {args.qemu}")
    args.qemu_path = Path(found)
    try:
        out = subprocess.run(
            [found, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        ).stdout
    except (OSError, subprocess.TimeoutExpired) as e:
        raise HarnessError(f"cannot run {found} --version: {e}") from e
    if not out.strip():
        raise HarnessError(f"{found} --version printed nothing")
    args.qemu_version = out.splitlines()[0]
    if args.accel == "auto":
        kvm = os.access("/dev/kvm", os.R_OK | os.W_OK)
        args.accel = "kvm" if kvm else "tcg"
        if not kvm:
            print(
                "note: /dev/kvm is not usable; running under TCG, where the"
                " scenarios' timeouts may be too short",
                file=sys.stderr,
            )


def result(scenario: str, verdict: str, error, start: float, checks) -> dict:
    return {
        "scenario": scenario,
        "verdict": verdict,
        "error": error,
        "start": start,
        "end": time.time(),
        "checks": [{"check": n, "ok": ok, "detail": d} for n, ok, d in checks],
    }


def run(args) -> int:
    rundir = args.out.resolve()
    if rundir.exists():
        raise HarnessError(f"{rundir} exists; each run gets a fresh directory")
    for p in [args.kernel, args.busybox, *args.module]:
        if not p.is_file():
            raise HarnessError(f"missing input: {p}")
    if f"{args.driver}.ko" not in {m.name for m in args.module}:
        raise HarnessError(f"no module named {args.driver}.ko among --module")
    unknown = [s for s in args.scenario if s not in SCENARIOS]
    if unknown:
        raise HarnessError(f"unknown scenario(s): {', '.join(unknown)}")
    resolve_host(args)
    rundir.parent.mkdir(parents=True, exist_ok=True)
    try:
        rundir.mkdir(mode=0o700)
    except FileExistsError as e:
        raise HarnessError(f"{rundir} appeared meanwhile; not sharing it") from e

    initrd = rundir / "initramfs.cpio.gz"
    initrd.write_bytes(build_initramfs(args.busybox, args.module))
    (rundir / "identities.json").write_text(
        json.dumps(identities(args, initrd), indent=1)
    )

    peer = Guest("peer", qemu_argv("peer", args, rundir, initrd), rundir)
    dut = Guest("dut", qemu_argv("dut", args, rundir, initrd), rundir)
    results, qmp = [], None
    started = time.time()
    # FAIL means a guest misbehaved, which a driver can cause. ERROR means the harness or
    # the host did: the DUT loads no driver before the first scenario, so a boot failure
    # is an ERROR, as is any exception other than GuestError, or an interrupt.
    try:
        peer.start()
        dut.start()
        deadline = time.monotonic() + args.boot_timeout
        peer.connect(deadline)
        dut.connect(deadline)
        peer.wait_ready(deadline)
        dut.wait_ready(deadline)
        qmp = Qmp(rundir / "dut-qmp.sock")
        ctx = Ctx(dut, peer, qmp, args.driver, rundir)
    except (Exception, KeyboardInterrupt) as e:  # pylint: disable=broad-exception-caught
        results.append(result("boot", "ERROR", f"{type(e).__name__}: {e}", started, []))
        print(f"ERROR boot ({e})", flush=True)
    else:
        for step, name in enumerate(args.scenario, start=1):
            ctx.step = step
            t0 = time.time()
            try:
                checks = SCENARIOS[name](ctx)
                passed = bool(checks) and all(ok for _, ok, _ in checks)
                verdict = "PASS" if passed else "FAIL"
                results.append(result(name, verdict, None, t0, checks))
            except GuestError as e:
                results.append(result(name, "FAIL", str(e), t0, []))
            except (Exception, KeyboardInterrupt) as e:  # pylint: disable=broad-exception-caught
                err = f"{type(e).__name__}: {e}"
                results.append(result(name, "ERROR", err, t0, []))
            r = results[-1]
            print(
                f"{r['verdict']} {name}" + (f" ({r['error']})" if r["error"] else ""),
                flush=True,
            )
            if r["verdict"] == "ERROR":
                break
    finally:
        if qmp:
            qmp.close()
        dut.stop()
        peer.stop()

    raw = rundir / "dut-trace-raw.log"
    counts = (
        filter_trace(raw, rundir / "dut-regtrace.log")
        if raw.exists()
        else empty_trace_counts()
    )
    if raw.exists():
        with raw.open("rb") as src, gzip.open(str(raw) + ".gz", "wb") as dst:
            dst.writelines(src)
        raw.unlink()
    pinged = any(r["scenario"] == "smoke" and r["verdict"] == "PASS" for r in results)
    if any(r["scenario"] == "smoke" for r in results):
        t0 = time.time()
        try:
            checks = capture_checks(rundir, counts, pinged)
            verdict = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
            results.append(result("capture", verdict, None, t0, checks))
        except Exception as e:  # pylint: disable=broad-exception-caught
            err = f"{type(e).__name__}: {e}"
            results.append(result("capture", "ERROR", err, t0, []))
        print(f"{results[-1]['verdict']} capture", flush=True)
    for p in rundir.glob("*.sock"):
        p.unlink()
    verdicts = {r["verdict"] for r in results}
    if "ERROR" in verdicts or not results:
        overall = "ERROR"
    else:
        overall = "PASS" if verdicts == {"PASS"} else "FAIL"
    (rundir / "verdicts.json").write_text(
        json.dumps(
            {"overall": overall, "trace_counts": counts, "results": results}, indent=1
        )
    )
    print(f"{overall} overall; run directory {rundir}")
    return {"PASS": 0, "FAIL": 1}.get(overall, 2)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="boot both guests and run scenarios")
    r.add_argument("--kernel", type=Path, required=True, help="guest bzImage")
    r.add_argument(
        "--module",
        type=Path,
        action="append",
        required=True,
        help="driver module to place in /lib/modules (repeatable)",
    )
    r.add_argument(
        "--driver",
        required=True,
        help="module and PCI driver name the DUT loads, e.g. e1000",
    )
    r.add_argument("--out", type=Path, required=True, help="fresh run directory")
    r.add_argument(
        "--scenario",
        action="append",
        help=f"scenario to run, in order (default smoke); one of {list(SCENARIOS)}",
    )
    r.add_argument(
        "--busybox",
        type=Path,
        default=Path("/usr/bin/busybox"),
        help="a statically linked busybox",
    )
    r.add_argument("--qemu", default="qemu-system-x86_64")
    r.add_argument(
        "--accel",
        choices=("auto", "kvm", "tcg"),
        default="auto",
        help="auto: KVM when /dev/kvm is usable, otherwise TCG",
    )
    r.add_argument("--boot-timeout", type=float, default=60)
    args = ap.parse_args(argv)
    args.scenario = args.scenario or ["smoke"]
    try:
        return run(args)
    except (HarnessError, OSError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
