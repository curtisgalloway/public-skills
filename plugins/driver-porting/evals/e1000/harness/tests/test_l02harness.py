# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Unit tests for the parts of l02harness.py that run without QEMU."""

import gzip
import socket
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import l02harness as h  # pylint: disable=wrong-import-position


def parse_newc(archive: bytes) -> list[tuple[str, int, bytes, int, int]]:
    """An independent newc reader: (name, mode, data, rdevmajor, rdevminor)."""
    out, off = [], 0
    while True:
        assert archive[off : off + 6] == b"070701", off
        f = [int(archive[off + 6 + 8 * i : off + 14 + 8 * i], 16) for i in range(13)]
        namesize, filesize = f[11], f[6]
        name_start = off + 110
        name = archive[name_start : name_start + namesize - 1].decode()
        data_start = name_start + namesize + (-(110 + namesize) % 4)
        data = archive[data_start : data_start + filesize]
        off = data_start + filesize + (-filesize % 4)
        if name == "TRAILER!!!":
            return out
        out.append((name, f[1], data, f[9], f[10]))


def pcap(frames: list[bytes]) -> bytes:
    head = struct.pack("<IHHiIII", 0xA1B2C3D4, 2, 4, 0, 0, 65535, 1)
    body = b"".join(
        struct.pack("<IIII", 1, i, len(fr), len(fr)) + fr for i, fr in enumerate(frames)
    )
    return head + body


def echo_frame(src: str, dst: str, icmp_type: int, payload: int = 56) -> bytes:
    eth = b"\x52\x54\x00\x12\x34\x57" + b"\x52\x54\x00\x12\x34\x56" + b"\x08\x00"
    ip = bytes([0x45, 0, 0, 0, 0, 0, 0, 0, 64, 1, 0, 0])
    ip += bytes(int(x) for x in src.split(".")) + bytes(int(x) for x in dst.split("."))
    return eth + ip + bytes([icmp_type, 0, 0, 0, 0, 1, 0, 1]) + b"\0" * payload


class CpioTest(unittest.TestCase):

    def test_round_trip_and_alignment(self):
        entries = [
            ("bin", 0o040755, b"", 0, 0),
            ("dev/console", 0o020600, b"", 5, 1),
            ("init", 0o100755, b"#!/bin/sh\n", 0, 0),
            ("odd", 0o100644, b"abcde", 0, 0),
        ]
        archive = h.cpio_newc(entries)
        self.assertEqual(len(archive) % 4, 0)
        self.assertEqual(parse_newc(archive), entries)

    def test_reproducible(self):
        entries = [("init", 0o100755, b"x", 0, 0)]
        self.assertEqual(h.cpio_newc(entries), h.cpio_newc(entries))

    def test_initramfs_carries_init_busybox_and_modules(self):
        with tempfile.TemporaryDirectory() as d:
            bb, ko = Path(d, "busybox"), Path(d, "e1000.ko")
            bb.write_bytes(b"BB")
            ko.write_bytes(b"KO")
            archive = gzip.decompress(h.build_initramfs(bb, [ko]))
        names = {n: (m, data) for n, m, data, _, _ in parse_newc(archive)}
        self.assertEqual(names["bin/busybox"], (0o100755, b"BB"))
        self.assertEqual(names["lib/modules/e1000.ko"], (0o100644, b"KO"))
        self.assertTrue(names["init"][1].startswith(b"#!/bin/busybox sh"))
        self.assertIn("dev/console", names)


class PcapTest(unittest.TestCase):

    def test_echo_frames_found_with_lengths(self):
        frames = [
            echo_frame("192.0.2.1", "192.0.2.2", 8),
            echo_frame("192.0.2.2", "192.0.2.1", 0),
            b"\xff" * 60,
            # IPv4 ICMP whose IHL claims 60 bytes of header in a 42-byte frame.
            echo_frame("192.0.2.1", "192.0.2.2", 8, payload=0)[:14]
            + b"\x4f"
            + echo_frame("192.0.2.1", "192.0.2.2", 8, payload=0)[15:],
        ]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "x.pcap")
            p.write_bytes(pcap(frames))
            echoes = h.icmp_echoes(h.read_pcap(p))
        self.assertEqual(
            echoes,
            [("192.0.2.1", "192.0.2.2", 8, 98), ("192.0.2.2", "192.0.2.1", 0, 98)],
        )

    def test_empty_file_has_no_frames(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "x.pcap")
            p.write_bytes(b"")
            self.assertEqual(h.read_pcap(p), [])

    def test_not_a_pcap_is_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "x.pcap")
            p.write_bytes(b"\0" * 40)
            with self.assertRaises(h.HarnessError):
                h.read_pcap(p)


class TraceTest(unittest.TestCase):

    LINES = [
        "2026-09-24T23:20:21.497100Z memory_region_ops_write cpu 0 mr 0x1 addr 0x70"
        " value 0x8f size 1 name 'rtc-index'\n",
        "2026-09-24T23:20:22.000001Z memory_region_ops_write cpu 0 mr 0x2 addr"
        " 0xfeb80000 value 0x4000000 size 4 name 'e1000-mmio'\n",
        "2026-09-24T23:20:22.000002Z memory_region_ops_read cpu 0 mr 0x2 addr"
        " 0xfeb80008 value 0x80080783 size 4 name 'e1000-mmio'\n",
        "2026-09-24T23:20:22.000003Z memory_region_ops_read cpu 0 mr 0x3 addr 0xc000"
        " value 0x0 size 4 name 'e1000-io'\n",
        "2026-09-24T23:20:22.000004Z pci_cfg_write e1000 00:01.0 @0x4 <- 0x107\n",
        "2026-09-24T23:20:22.000005Z pci_cfg_write virtio-net-pci 00:01.0 @0x4 <- 0x7\n",
        "2026-09-24T23:20:22.000006Z e1000x_link_negotiation_done Auto negotiation"
        " is completed\n",
        "memory_region_ops_write cpu 0 mr 0x2 addr 0xfeb80000 value 0x0 size 4"
        " name 'e1000-mmio'\n",
        "12345@1695600000.123456:memory_region_ops_read cpu 0 mr 0x2 addr 0xfeb80010"
        " value 0x0 size 4 name 'e1000-mmio'\n",
        "2026-09-24T23:20:22.000007Z memory_region_ops_write cpu 0 mr 0x2 addr"
        " 0xfeb80014 value 0x1 size 4 name 'e1000-mmio'\n",
    ]

    def test_counts_and_keeps_only_e1000_lines(self):
        with tempfile.TemporaryDirectory() as d:
            raw, out = Path(d, "raw.log"), Path(d, "out.log")
            raw.write_text("".join(self.LINES))
            counts = h.filter_trace(raw, out)
            kept = out.read_text().splitlines(keepends=True)
        self.assertEqual(
            counts,
            {
                "mmio_read": 2,
                "mmio_write": 3,
                "eeprom": 2,
                "io": 1,
                "pci_cfg": 1,
                "model_event": 1,
            },
        )
        self.assertEqual(kept, [self.LINES[i] for i in (1, 2, 3, 4, 6, 7, 8, 9)])


class GuestChannelTest(unittest.TestCase):

    def _guest(self, d: str):
        g = h.Guest("dut", ["true"], Path(d))
        g.sock, other = socket.socketpair()
        return g, other

    def test_broken_channel_is_a_guest_death_and_is_logged(self):
        with tempfile.TemporaryDirectory() as d:
            g, other = self._guest(d)
            other.close()
            with self.assertRaises(h.GuestError):
                g.run("true", timeout=2)
            self.assertIn("command channel failed", g.dead)
            g.sock.close()
            g.cmdlog.close()
            logged = Path(d, "dut-cmds.jsonl").read_text()
        self.assertIn('"cmd": "true"', logged)

    def test_self_test_on_an_already_dead_guest_fails(self):
        with tempfile.TemporaryDirectory() as d:
            g, other = self._guest(d)
            g.dead = "dut: no answer before the timeout"
            checks = h.expect_dead(g, "sleep 600", 5, "no answer before the timeout")
            other.close()
            g.sock.close()
            g.cmdlog.close()
        self.assertEqual(len(checks), 1)
        self.assertFalse(checks[0][1])


class RunValidationTest(unittest.TestCase):

    def _args(self, d: Path, **over):
        k, bb, ko = Path(d, "bzImage"), Path(d, "busybox"), Path(d, "e1000.ko")
        for p in (k, bb, ko):
            p.write_bytes(b"x")
        argv = ["run", "--kernel", str(k), "--busybox", str(bb), "--module", str(ko)]
        argv += ["--driver", over.get("driver", "e1000"), "--out", str(Path(d, "run"))]
        argv += ["--qemu", over.get("qemu", "qemu-system-x86_64")]
        for s in over.get("scenarios", []):
            argv += ["--scenario", s]
        return argv

    def test_driver_without_module_is_a_setup_error(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(h.main(self._args(Path(d), driver="e1000_l02")), 2)
            self.assertFalse(Path(d, "run").exists())

    def test_unknown_scenario_is_a_setup_error(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertEqual(h.main(self._args(Path(d), scenarios=["nope"])), 2)

    def test_existing_run_directory_is_refused_even_empty(self):
        with tempfile.TemporaryDirectory() as d:
            Path(d, "run").mkdir()
            self.assertEqual(h.main(self._args(Path(d))), 2)
            self.assertEqual(list(Path(d, "run").iterdir()), [])

    def test_missing_qemu_is_a_setup_error_before_the_run_directory(self):
        with tempfile.TemporaryDirectory() as d:
            argv = self._args(Path(d), qemu=str(Path(d, "no-such-qemu")))
            self.assertEqual(h.main(argv), 2)
            self.assertFalse(Path(d, "run").exists())


if __name__ == "__main__":
    unittest.main()
