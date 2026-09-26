# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for claude_usage.py and codex_usage.py parsing (no network, no real home)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import claude_usage  # pylint: disable=wrong-import-position
import codex_usage  # pylint: disable=wrong-import-position


class ClaudePoolsTest(unittest.TestCase):

    def test_limits_list(self):
        data = {"limits": [
            {"kind": "session", "percent": 90, "resets_at": "A", "scope": None},
            {"kind": "weekly_all", "percent": 62, "resets_at": "B", "scope": None},
            {"kind": "weekly_scoped", "percent": 41, "resets_at": "B",
             "scope": {"model": {"id": None, "display_name": "Fable"}}},
        ]}
        got = [(p["pool"], p["percent"]) for p in claude_usage.pools(data)]
        self.assertEqual(
            got, [("5-hour", 90), ("weekly", 62), ("Fable weekly", 41)])

    def test_legacy_fields_when_no_limits(self):
        data = {"limits": None,
                "five_hour": {"utilization": 10, "resets_at": "A"},
                "seven_day": {"utilization": 20, "resets_at": "B"}}
        got = [(p["pool"], p["percent"]) for p in claude_usage.pools(data)]
        self.assertEqual(got, [("5-hour", 10), ("weekly", 20)])

    def test_unknown_kind_passes_through(self):
        data = {"limits": [{"kind": "monthly_all", "percent": 5}]}
        self.assertEqual(claude_usage.pools(data)[0]["pool"], "monthly_all")


class CodexRecordTest(unittest.TestCase):

    def test_newest_record_wins_within_file(self):
        with tempfile.TemporaryDirectory() as home:
            day = os.path.join(home, "2026", "09", "25")
            os.makedirs(day)
            lines = [
                {"payload": {"rate_limits": {"primary": {"used_percent": 1}}}},
                {"payload": {"other": 1}},
                {"payload": {"info": {"rate_limits": {
                    "primary": {"used_percent": 7, "window_minutes": 10080}}}}},
            ]
            with open(os.path.join(day, "rollout-x.jsonl"), "w") as f:
                f.write("\n".join(json.dumps(x) for x in lines))
            old = codex_usage.SESSIONS
            codex_usage.SESSIONS = home
            try:
                _, _, limits = codex_usage.newest_record()
            finally:
                codex_usage.SESSIONS = old
            self.assertEqual(limits["primary"]["used_percent"], 7)

    def test_window_names(self):
        self.assertEqual(codex_usage.window_name(10080), "weekly")
        self.assertEqual(codex_usage.window_name(300), "5-hour")
        self.assertEqual(codex_usage.window_name(60), "60-minute")


if __name__ == "__main__":
    unittest.main()
