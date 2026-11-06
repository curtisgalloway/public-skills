# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for dps150.py against a simulated supply; no hardware or pyserial."""

import contextlib
import io
import pathlib
import struct
import sys
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import dps150  # pylint: disable=wrong-import-position


def rx(cmd, payload, start=0xA1):
    body = bytes([cmd, len(payload)]) + payload
    return bytes([0xF0, start]) + body + bytes([sum(body) & 0xFF])


class FakeSupply:
    """Answers the protocol the way the real unit did on the wire."""

    def __init__(
        self,
        model=b"DPS-150",
        upper_limit=4.93,
        upper_limit_a=5.1,
        firmware=b"V1.0",
        ignore_writes=False,
    ):
        self.model = model
        self.upper_limit = upper_limit
        self.upper_limit_a = upper_limit_a
        self.firmware = firmware
        self.ignore_writes = ignore_writes
        self.volts = 3.0
        self.amps = 0.5
        self.output = False
        self.pending = b""
        self.writes = []
        self.closed = False

    @property
    def in_waiting(self):
        return len(self.pending)

    def read(self, size):
        chunk, self.pending = self.pending[:size], self.pending[size:]
        return chunk

    def reset_input_buffer(self):
        self.pending = b""

    def close(self):
        self.closed = True

    def status_payload(self):
        data = bytearray(dps150.STATUS_LENGTH)
        out_v = self.volts if self.output else 0.0
        struct.pack_into("<7f", data, 0, 5.13, self.volts, self.amps, out_v, 0, 0, 27.4)
        struct.pack_into("<5f", data, 76, 30.0, 5.1, 150.0, 80.0, 5.0)
        data[107] = 1 if self.output else 0
        data[109] = 1
        struct.pack_into("<2f", data, 111, self.upper_limit, self.upper_limit_a)
        return bytes(data)

    def write(self, raw):
        self.writes.append(raw)
        start, cmd = raw[1], raw[2]
        payload = raw[4:-1]
        push = rx(0xC3, bytes(12))
        if start == 0xA1 and cmd == dps150.CMD_READY:
            self.pending += push + rx(0xE1, b"\x01")
        elif start == 0xA1 and cmd == dps150.CMD_MODEL:
            self.pending += push + rx(0xDE, self.model)
        elif start == 0xA1 and cmd in (dps150.CMD_VERSION_DF, dps150.CMD_VERSION_E0):
            self.pending += push + rx(cmd, self.firmware)
        elif start == 0xA1 and cmd == dps150.CMD_STATUS:
            self.pending += push + rx(0xFF, self.status_payload())
        elif start == 0xB1 and not self.ignore_writes:
            if cmd == dps150.CMD_SET_VOLTS:
                self.volts = struct.unpack("<f", payload)[0]
            elif cmd == dps150.CMD_SET_AMPS:
                self.amps = struct.unpack("<f", payload)[0]
            elif cmd == dps150.CMD_OUTPUT:
                self.output = payload == b"\x01"

    def set_writes(self):
        return [w for w in self.writes if w[1] == 0xB1]


class FrameTest(unittest.TestCase):

    def test_documented_voltage_frame(self):
        frame = dps150.frame(0xB1, 0xC1, struct.pack("<f", 12.0))
        self.assertEqual(frame.hex(), "f1b1c104000040" + "4146")

    def test_documented_model_query(self):
        self.assertEqual(dps150.query(0xDE).hex(), "f1a1de0100df")

    def test_parses_captured_model_reply(self):
        raw = bytes.fromhex("f0a1de074450532d3135308f")
        frames, rest = dps150.parse_frames(raw)
        self.assertEqual(frames, [(0xDE, b"DPS-150")])
        self.assertEqual(rest, b"")

    def test_keeps_a_partial_frame(self):
        raw = rx(0xDE, b"DPS-150")
        frames, rest = dps150.parse_frames(raw[:6])
        self.assertEqual(frames, [])
        frames, _ = dps150.parse_frames(rest + raw[6:])
        self.assertEqual(frames, [(0xDE, b"DPS-150")])

    def test_skips_noise_and_bad_checksums(self):
        bad = bytearray(rx(0xC3, bytes(12)))
        bad[-1] ^= 0xFF
        good = rx(0xDE, b"DPS-150")
        frames, _ = dps150.parse_frames(b"\x00\x11" + bytes(bad) + good)
        self.assertEqual(frames, [(0xDE, b"DPS-150")])


class DecodeTest(unittest.TestCase):

    def test_named_fields(self):
        status = dps150.decode_status(FakeSupply().status_payload())
        self.assertEqual(status["input_v"], 5.13)
        self.assertEqual(status["temperature_c"], 27.4)
        self.assertEqual(status["upper_limit_v"], 4.93)
        self.assertEqual(status["ovp_v"], 30.0)
        self.assertEqual(status["mode"], "CV")
        self.assertEqual(status["protection"], "none")
        self.assertFalse(status["output_on"])

    def test_short_payload_is_an_unknown_outcome(self):
        with self.assertRaises(dps150.ToolError) as caught:
            dps150.decode_status(bytes(10))
        self.assertEqual(caught.exception.code, 22)


class CheckLimitsTest(unittest.TestCase):

    def status(self, **changes):
        return {"input_v": 5.13, "upper_limit_v": 4.93, "upper_limit_a": 5.1, **changes}

    def test_unusable_limits_are_refused(self):
        for name in ("upper_limit_v", "upper_limit_a"):
            for bad in (float("nan"), float("inf"), float("-inf"), -1.0):
                with self.subTest(name=name, bad=bad):
                    with self.assertRaises(dps150.ToolError) as caught:
                        dps150.check_limits(self.status(**{name: bad}), 1.0, 0.5)
                    self.assertEqual(caught.exception.code, 3)

    def test_non_finite_setpoints_are_refused(self):
        for bad in (float("nan"), float("inf")):
            for volts, amps in ((bad, 0.5), (1.0, bad)):
                with self.subTest(volts=volts, amps=amps):
                    with self.assertRaises(dps150.ToolError) as caught:
                        dps150.check_limits(self.status(), volts, amps)
                    self.assertEqual(caught.exception.code, 3)

    def test_requests_within_the_limits_pass(self):
        dps150.check_limits(self.status(), 4.93, 5.1)
        dps150.check_limits(self.status(), None, None)


class PrintableTextTest(unittest.TestCase):

    def test_model_string_is_unchanged(self):
        self.assertEqual(dps150.printable_text(b"DPS-150"), "DPS-150")

    def test_control_and_high_bytes_are_replaced(self):
        self.assertEqual(
            dps150.printable_text(b"V1\x1b[2J\x07\r\n\x7f\xff"), "V1?[2J?????"
        )

    def test_length_is_bounded(self):
        text = dps150.printable_text(b"A" * 255)
        self.assertEqual(text, "A" * dps150.MAX_TEXT_LENGTH)


class CommandTest(unittest.TestCase):

    def run_tool(self, supply, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(dps150, "open_port", return_value=supply):
            with mock.patch.object(dps150.time, "sleep"):
                with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                    code = dps150.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_status_sends_no_writes(self):
        supply = FakeSupply()
        code, out, _ = self.run_tool(supply, "--json", "status")
        self.assertEqual(code, 0)
        self.assertIn('"input_v": 5.13', out)
        self.assertEqual(supply.set_writes(), [])

    def test_session_always_ends(self):
        supply = FakeSupply()
        self.run_tool(supply, "status")
        self.assertEqual(supply.writes[-1], dps150.SESSION_CLOSE)
        self.assertTrue(supply.closed)

    def test_set_writes_and_reads_back(self):
        supply = FakeSupply()
        code, _, _ = self.run_tool(supply, "set", "--volts", "1.5", "--amps", "0.2")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(supply.volts, 1.5)
        self.assertAlmostEqual(supply.amps, 0.2, places=5)

    def test_live_set_above_upper_limit_writes_nothing(self):
        supply = FakeSupply()
        supply.output = True
        code, _, err = self.run_tool(supply, "set", "--volts", "12")
        self.assertEqual(code, 3)
        self.assertIn("USB-C", err)
        self.assertEqual(supply.set_writes(), [])

    def test_preset_above_upper_limit_is_stored_while_off(self):
        supply = FakeSupply()
        code, _, _ = self.run_tool(supply, "set", "--volts", "12")
        self.assertEqual(code, 0)
        self.assertAlmostEqual(supply.volts, 12.0)

    def test_set_outside_device_range_is_usage(self):
        code, _, _ = self.run_tool(FakeSupply(), "set", "--volts", "31")
        self.assertEqual(code, 2)

    def test_set_needs_a_value(self):
        code, _, _ = self.run_tool(FakeSupply(), "set")
        self.assertEqual(code, 2)

    def test_ignored_write_is_reported(self):
        supply = FakeSupply(ignore_writes=True)
        code, _, _ = self.run_tool(supply, "set", "--volts", "1.5")
        self.assertEqual(code, 21)

    def test_dry_run_does_not_open_the_port(self):
        out = io.StringIO()
        with mock.patch.object(dps150, "open_port") as opened:
            with contextlib.redirect_stdout(out):
                code = dps150.main(["output", "on", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("would turn output on", out.getvalue())
        opened.assert_not_called()

    def test_output_on_needs_yes(self):
        supply = FakeSupply()
        code, _, err = self.run_tool(supply, "output", "on")
        self.assertEqual(code, 2)
        self.assertIn("--yes", err)
        self.assertEqual(supply.writes, [])

    def test_output_on_warns_it_persists(self):
        supply = FakeSupply()
        code, _, err = self.run_tool(supply, "output", "on", "--yes")
        self.assertEqual(code, 0)
        self.assertTrue(supply.output)
        self.assertIn("stays on", err)

    def test_output_on_refused_when_setpoint_is_unreachable(self):
        supply = FakeSupply()
        supply.volts = 12.0
        code, _, _ = self.run_tool(supply, "output", "on", "--yes")
        self.assertEqual(code, 3)
        self.assertFalse(supply.output)

    def test_output_off_is_allowed_above_the_limit(self):
        supply = FakeSupply()
        supply.volts = 12.0
        supply.output = True
        code, _, _ = self.run_tool(supply, "output", "off")
        self.assertEqual(code, 0)
        self.assertFalse(supply.output)

    def test_live_set_with_nan_limit_writes_nothing(self):
        for limits in ({"upper_limit": float("nan")}, {"upper_limit_a": float("nan")}):
            with self.subTest(limits=limits):
                supply = FakeSupply(**limits)
                supply.output = True
                code, _, err = self.run_tool(
                    supply, "set", "--volts", "1.5", "--amps", "0.2"
                )
                self.assertEqual(code, 3)
                self.assertIn("nan", err)
                self.assertEqual(supply.set_writes(), [])

    def test_output_on_with_nan_limit_is_refused(self):
        supply = FakeSupply(upper_limit=float("nan"))
        code, _, _ = self.run_tool(supply, "output", "on", "--yes")
        self.assertEqual(code, 3)
        self.assertFalse(supply.output)
        self.assertEqual(supply.set_writes(), [])

    def test_output_on_with_nan_setpoint_is_refused(self):
        supply = FakeSupply()
        supply.volts = float("nan")
        code, _, _ = self.run_tool(supply, "output", "on", "--yes")
        self.assertEqual(code, 3)
        self.assertFalse(supply.output)

    def test_output_off_is_allowed_with_nan_limit(self):
        supply = FakeSupply(upper_limit=float("nan"))
        supply.output = True
        code, _, _ = self.run_tool(supply, "output", "off")
        self.assertEqual(code, 0)
        self.assertFalse(supply.output)

    def test_nan_on_the_command_line_is_usage(self):
        supply = FakeSupply()
        code, _, _ = self.run_tool(supply, "set", "--volts", "nan")
        self.assertEqual(code, 2)
        self.assertEqual(supply.writes, [])

    def test_doctor_prints_no_control_bytes(self):
        supply = FakeSupply(
            model=b"DPS-150\x1b[2J", firmware=b"V1\x1b]0;title\x07\r\n" + b"A" * 200
        )
        with mock.patch.object(dps150, "load_serial"):
            code, out, _ = self.run_tool(supply, "doctor")
        self.assertEqual(code, 0)
        self.assertIn("model: DPS-150?[2J\n", out)
        self.assertIn("version 0xDF: V1?]0;title???AAA", out)
        self.assertNotIn("\x1b", out)
        self.assertNotIn("\x07", out)
        self.assertNotIn("\r", out)
        self.assertLess(max(len(line) for line in out.splitlines()), 100)

    def test_exact_model_still_passes_doctor(self):
        with mock.patch.object(dps150, "load_serial"):
            code, out, _ = self.run_tool(FakeSupply(), "doctor")
        self.assertEqual(code, 0)
        self.assertIn("model: DPS-150\n", out)

    def test_wrong_model_is_refused_before_any_write(self):
        supply = FakeSupply(model=b"OTHER")
        code, _, _ = self.run_tool(supply, "set", "--volts", "1")
        self.assertEqual(code, 3)
        self.assertEqual(supply.set_writes(), [])

    def test_skill_prints_the_document(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = dps150.main(["--skill"])
        self.assertEqual(code, 0)
        self.assertTrue(out.getvalue().startswith("---\nname: fnirsi-dps-150"))


if __name__ == "__main__":
    unittest.main()
