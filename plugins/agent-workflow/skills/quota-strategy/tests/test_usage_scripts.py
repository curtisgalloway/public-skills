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
import textwrap
import time
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
    def event(timestamp, percent, identifier=None):
        limits = {
            "primary": {
                "used_percent": percent, "window_minutes": 10080, "resets_at": 1791590400
            }
        }
        if identifier is not None:
            limits["limit_id"] = identifier
        return {"timestamp": timestamp, "type": "event_msg",
                "payload": {"type": "token_count", "rate_limits": limits}}

    def run_json(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = codex_usage.main(["--json", *args])
        return status, json.loads(output.getvalue())

    def fake_server(self, code):
        return mock.patch.object(codex_usage, "APP_SERVER_COMMAND",
                                 (sys.executable, "-u", "-c", textwrap.dedent(code)))

    def test_newest_record_wins_within_file(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event("2026-10-09T10:00:00Z", 7),
                {"payload": {"other": 1}},
                self.event("2026-10-09T09:00:00Z", 1),
            ],
        )
        _, limits = codex_usage.newest_records()["codex"]
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
        _, limits = codex_usage.newest_records()["codex"]
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
        with mock.patch.object(codex_usage.time, "time", return_value=now.timestamp()):
            status, data = self.run_json("--offline")
        self.assertEqual(status, 0)
        self.assertEqual(data["age_minutes"], 120)
        self.assertEqual(data["pools"]["codex"]["status"], "unknown")
        self.assertEqual(data["pools"]["codex"]["reason"], "stale")

    def test_unknown_timestamps_do_not_become_fresh_readings(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event(None, 5),
                self.event("bad", 6),
                self.event("2026-10-09T12:00:00", 7),
            ],
        )
        self.assertEqual(codex_usage.newest_records(), {})
        status, data = self.run_json("--offline")
        self.assertEqual(status, 1)
        self.assertEqual(data["pools"]["codex"]["status"], "unknown")
        self.assertIsNone(data["age_minutes"])

    def test_telemetry_survives_partial_line_and_empty_limits(self):
        event = self.event("2026-10-09T10:00:00+00:00", 12)
        empty = self.event("2026-10-09T11:00:00Z", 0)
        empty["payload"]["rate_limits"] = {}
        path = self.write_log("rollout-x.jsonl", [event, empty])
        with open(path, "a", encoding="utf-8") as stream:
            stream.write('\n{"rate_limits":')
        _, limits = codex_usage.newest_records()["codex"]
        self.assertEqual(limits["primary"]["used_percent"], 12)

    def test_ignores_non_telemetry_with_rate_limits(self):
        bogus = self.event("2026-10-09T11:00:00Z", 5, "codex")
        tool_record = {**bogus, "type": "response_item"}
        message_record = {**bogus, "payload": {**bogus["payload"], "type": "user_message"}}
        self.write_log("rollout-x.jsonl", [
            self.event("2026-10-09T10:00:00Z", 86, "codex"),
            tool_record,
            message_record,
        ])
        _, limits = codex_usage.newest_records()["codex"]
        self.assertEqual(limits["primary"]["used_percent"], 86)

    def test_timestamp_offsets_compare_as_instants(self):
        self.write_log(
            "rollout-x.jsonl",
            [
                self.event("2026-10-09T08:00:00-07:00", 20),
                self.event("2026-10-09T14:00:00Z", 10),
            ],
        )
        _, limits = codex_usage.newest_records()["codex"]
        self.assertEqual(limits["primary"]["used_percent"], 20)

    def test_codex_home_controls_log_discovery(self):
        self.write_log("rollout-x.jsonl", [self.event("2026-10-09T10:00:00Z", 17)])
        self.assertEqual(
            codex_usage.sessions_dir(), os.path.join(self.home.name, "sessions")
        )
        self.assertEqual(codex_usage.newest_records()["codex"][1]["primary"]["used_percent"], 17)
        with mock.patch.dict(
            os.environ, {"CODEX_HOME": os.path.join(self.home.name, "other")}
        ):
            self.assertEqual(codex_usage.newest_records(), {})

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


    def test_newer_other_pool_does_not_replace_main(self):
        self.write_log("rollout-main.jsonl", [
            self.event("2026-10-09T10:00:00Z", 86, "codex"),
        ])
        self.write_log("rollout-other.jsonl", [
            self.event("2026-10-09T10:05:00Z", 5, "codex_other"),
        ])
        now = datetime.datetime(2026, 10, 9, 10, 6, tzinfo=datetime.timezone.utc)
        with mock.patch.object(codex_usage.time, "time", return_value=now.timestamp()):
            with mock.patch.object(codex_usage, "app_server_rate_limits") as live:
                status, data = self.run_json("--offline")
                live.assert_not_called()
        self.assertEqual(status, 0)
        self.assertEqual(data["windows"][0]["used_percent"], 86)
        self.assertEqual(data["age_minutes"], 6)
        other = data["pools"]["codex_other"]
        self.assertEqual(other["windows"][0]["used_percent"], 5)
        self.assertEqual((other["source"], other["status"], other["age_minutes"]),
                         ("log", "known", 1))

    def test_other_only_leaves_main_unknown(self):
        self.write_log("rollout-other.jsonl", [
            self.event("2026-10-09T10:05:00Z", 5, "codex_other"),
        ])
        status, data = self.run_json("--offline")
        self.assertEqual(status, 1)
        self.assertEqual(data["windows"], [])
        self.assertEqual(data["pools"]["codex"]["reason"], "pool_missing")
        self.assertIn("codex_other", data["pools"])

    def test_reset_passed_is_unknown_even_when_fresh(self):
        event = self.event("2026-10-09T10:05:00Z", 86, "codex")
        now = datetime.datetime(2026, 10, 9, 10, 6, tzinfo=datetime.timezone.utc)
        event["payload"]["rate_limits"]["primary"]["resets_at"] = int(now.timestamp())
        self.write_log("rollout-reset.jsonl", [event])
        with mock.patch.object(codex_usage.time, "time", return_value=now.timestamp()):
            status, data = self.run_json("--offline")
        self.assertEqual(status, 0)
        self.assertEqual(data["pools"]["codex"]["reason"], "reset_passed")

    def test_live_handshake_and_multiple_pools(self):
        self.write_log("rollout-main.jsonl", [
            self.event("2026-10-09T10:00:00Z", 42, "codex"),
        ])
        with self.fake_server("""
            import json
            import os
            import sys
            import time

            init = json.loads(sys.stdin.readline())
            assert init["method"] == "initialize"
            assert init["params"]["clientInfo"]["name"]
            print(json.dumps({"id": init["id"], "result": {"userAgent": "fixture"}}))
            assert json.loads(sys.stdin.readline()) == {"method": "initialized", "params": {}}
            request = json.loads(sys.stdin.readline())
            assert request["method"] == "account/rateLimits/read"
            print(json.dumps({"method": "account/rateLimits/updated", "params": {}}))
            reset = int(time.time()) + 3600
            def bucket(percent, identifier):
                return {"primary": {"usedPercent": percent, "windowDurationMins": 10080,
                                    "resetsAt": reset}, "limitId": identifier}
            print(json.dumps({"id": request["id"], "result": {
                "rateLimits": bucket(5, "codex_other"),
                "rateLimitsByLimitId": {
                    "codex": bucket(86, "codex"), "codex_other": bucket(5, "codex_other"),
                },
            }}))
            assert sys.stdin.readline() == ""
            with open(os.path.join(os.environ["CODEX_HOME"], "closed"), "w"):
                pass
        """):
            status, data = self.run_json()
        self.assertTrue(os.path.exists(os.path.join(self.home.name, "closed")))
        self.assertEqual(status, 0)
        self.assertEqual(data["windows"][0]["used_percent"], 86)
        for pool in data["pools"].values():
            self.assertEqual((pool["source"], pool["status"], pool["age_minutes"]),
                             ("live", "known", 0))

    def test_live_multi_pool_response_does_not_infer_main(self):
        other = {"primary": {"usedPercent": 5, "windowDurationMins": 10080,
                             "resetsAt": int(time.time()) + 3600}}
        with mock.patch.object(codex_usage, "app_server_rate_limits", return_value={
            "rateLimits": other, "rateLimitsByLimitId": {"codex_other": other},
        }):
            status, data = self.run_json()
        self.assertEqual(status, 1)
        self.assertEqual(data["windows"], [])
        self.assertEqual(data["pools"]["codex"]["reason"], "pool_missing")
        self.assertEqual(data["pools"]["codex_other"]["source"], "live")

    def test_live_single_pool_compatibility_response(self):
        with mock.patch.object(codex_usage, "app_server_rate_limits", return_value={
            "rateLimits": {"primary": {"usedPercent": 20, "windowDurationMins": 300,
                                       "resetsAt": int(time.time()) + 3600}},
        }):
            status, data = self.run_json()
        self.assertEqual(status, 0)
        self.assertEqual(data["windows"][0]["used_percent"], 20)

    def test_live_error_falls_back_to_log(self):
        self.write_log("rollout-main.jsonl", [self.event("2026-10-09T10:00:00Z", 86)])
        with self.fake_server("""
            import json
            import sys

            init = json.loads(sys.stdin.readline())
            print(json.dumps({"id": init["id"], "result": {}}))
            sys.stdin.readline()
            request = json.loads(sys.stdin.readline())
            print(json.dumps({"id": request["id"], "error": {"code": -32601}}))
        """):
            status, data = self.run_json()
        self.assertEqual(status, 0)
        self.assertEqual(data["pools"]["codex"]["source"], "log")
        self.assertEqual(data["windows"][0]["used_percent"], 86)

    def test_live_timeout_falls_back_to_log(self):
        self.write_log("rollout-main.jsonl", [self.event("2026-10-09T10:00:00Z", 86)])
        with self.fake_server("""
            import sys
            import time

            sys.stdin.readline()
            sys.stdout.write("{")
            sys.stdout.flush()
            time.sleep(10)
        """):
            with mock.patch.object(codex_usage, "LIVE_TIMEOUT_SECONDS", 0.2):
                started = time.monotonic()
                status, data = self.run_json()
        self.assertLess(time.monotonic() - started, 5)
        self.assertEqual(status, 0)
        self.assertEqual(data["pools"]["codex"]["source"], "log")

    def test_window_names(self):
        self.assertEqual(codex_usage.window_name(10080), "weekly")
        self.assertEqual(codex_usage.window_name(300), "5-hour")
        self.assertEqual(codex_usage.window_name(60), "60-minute")


if __name__ == "__main__":
    unittest.main()
