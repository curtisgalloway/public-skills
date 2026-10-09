# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for claude_usage.py and codex_usage.py parsing (no network, no real home)."""

import contextlib
import datetime
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import claude_usage  # pylint: disable=wrong-import-position
import codex_usage  # pylint: disable=wrong-import-position


class ClaudePoolsTest(unittest.TestCase):

    def test_limits_list(self):
        data = {
            "limits": [
                {"kind": "session", "percent": 90, "resets_at": "A", "scope": None},
                {"kind": "weekly_all", "percent": 62, "resets_at": "B", "scope": None},
                {
                    "kind": "weekly_scoped",
                    "percent": 41,
                    "resets_at": "B",
                    "scope": {"model": {"id": None, "display_name": "Fable"}},
                },
            ]
        }
        got = [(p["pool"], p["percent"]) for p in claude_usage.pools(data)]
        self.assertEqual(got, [("5-hour", 90), ("weekly", 62), ("Fable weekly", 41)])

    def test_legacy_fields_when_no_limits(self):
        data = {
            "limits": None,
            "five_hour": {"utilization": 10, "resets_at": "A"},
            "seven_day": {"utilization": 20, "resets_at": "B"},
        }
        got = [(p["pool"], p["percent"]) for p in claude_usage.pools(data)]
        self.assertEqual(got, [("5-hour", 10), ("weekly", 20)])

    def test_unknown_kind_passes_through(self):
        data = {"limits": [{"kind": "monthly_all", "percent": 5}]}
        self.assertEqual(claude_usage.pools(data)[0]["pool"], "monthly_all")


class CodexRecordTest(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        env = mock.patch.dict(os.environ, {"CODEX_HOME": self.home.name})
        env.start()
        self.addCleanup(env.stop)
        self.day = os.path.join(self.home.name, "sessions", "2026", "10", "09")
        os.makedirs(self.day)

    def write_log(self, name, records):
        path = os.path.join(self.day, name)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("\n".join(json.dumps(record) for record in records))
        return path

    @staticmethod
    def event(timestamp, percent):
        return {
            "timestamp": timestamp,
            "payload": {
                "rate_limits": {
                    "primary": {"used_percent": percent, "window_minutes": 10080}
                }
            },
        }

    def test_newest_record_wins_within_file(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event("2026-10-09T10:00:00Z", 7),
                {"payload": {"other": 1}},
                self.event("2026-10-09T09:00:00Z", 1),
            ],
        )
        _, _, limits = codex_usage.newest_record()
        self.assertEqual(limits["primary"]["used_percent"], 7)

    def test_newest_event_wins_despite_later_unrelated_writes(self):
        old = self.write_log(
            "rollout-old.jsonl",
            [
                self.event("2026-10-08T00:00:00Z", 10),
                {"timestamp": "2026-10-09T12:00:00Z", "payload": {"other": 1}},
            ],
        )
        new = self.write_log(
            "rollout-new.jsonl",
            [
                self.event("2026-10-09T11:59:00Z", 95),
            ],
        )
        os.utime(old, (2000, 2000))
        os.utime(new, (1000, 1000))
        path, _, limits = codex_usage.newest_record()
        self.assertEqual(path, new)
        self.assertEqual(limits["primary"]["used_percent"], 95)

    def test_json_age_uses_usage_event_time(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event("2026-10-09T10:00:00Z", 10),
                {"timestamp": "2026-10-09T12:00:00Z", "payload": {"other": 1}},
            ],
        )
        now = datetime.datetime(2026, 10, 9, 12, tzinfo=datetime.timezone.utc)
        output = io.StringIO()
        with mock.patch.object(codex_usage.time, "time", return_value=now.timestamp()):
            with mock.patch.object(sys, "argv", ["codex_usage.py", "--json"]):
                with contextlib.redirect_stdout(output), self.assertRaises(
                    SystemExit
                ) as exit_:
                    codex_usage.main()
        self.assertEqual(exit_.exception.code, 0)
        self.assertEqual(json.loads(output.getvalue())["age_minutes"], 120)

    def test_unknown_timestamps_do_not_become_fresh_readings(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event(None, 5),
                self.event("bad", 6),
                self.event("2026-10-09T12:00:00", 7),
            ],
        )
        self.assertIsNone(codex_usage.newest_record())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(
            SystemExit
        ) as exit_:
            codex_usage.main()
        self.assertEqual(exit_.exception.code, 1)

    def test_nested_record_survives_partial_line_and_empty_limits(self):
        nested = {
            "timestamp": "2026-10-09T10:00:00+00:00",
            "payload": {"info": {"rate_limits": {"primary": {"used_percent": 12}}}},
        }
        path = self.write_log(
            "rollout-x.jsonl",
            [nested, {"timestamp": "2026-10-09T11:00:00Z", "rate_limits": {}}],
        )
        with open(path, "a", encoding="utf-8") as stream:
            stream.write('\n{"rate_limits":')
        _, _, limits = codex_usage.newest_record()
        self.assertEqual(limits["primary"]["used_percent"], 12)

    def test_timestamp_offsets_compare_as_instants(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event("2026-10-09T08:00:00-07:00", 20),
                self.event("2026-10-09T14:00:00Z", 10),
            ],
        )
        _, _, limits = codex_usage.newest_record()
        self.assertEqual(limits["primary"]["used_percent"], 20)

    def test_codex_home_controls_log_discovery(self):
        self.write_log("rollout-x.jsonl", [self.event("2026-10-09T10:00:00Z", 17)])
        self.assertEqual(
            codex_usage.sessions_dir(), os.path.join(self.home.name, "sessions")
        )
        self.assertEqual(codex_usage.newest_record()[2]["primary"]["used_percent"], 17)
        with mock.patch.dict(
            os.environ, {"CODEX_HOME": os.path.join(self.home.name, "other")}
        ):
            self.assertIsNone(codex_usage.newest_record())

    def test_default_home_when_codex_home_is_unset_or_empty(self):
        for env in (
            {"HOME": self.home.name},
            {"HOME": self.home.name, "CODEX_HOME": ""},
        ):
            with self.subTest(env=env), mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(
                    codex_usage.sessions_dir(),
                    os.path.join(self.home.name, ".codex", "sessions"),
                )

    def test_window_names(self):
        self.assertEqual(codex_usage.window_name(10080), "weekly")
        self.assertEqual(codex_usage.window_name(300), "5-hour")
        self.assertEqual(codex_usage.window_name(60), "60-minute")


if __name__ == "__main__":
    unittest.main()
