# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for agent_usage.py against synthetic Codex, agy and Muse logs (no network)."""

import contextlib
import io
import json
import os
import sqlite3
import sys
import tempfile
import time
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import agent_usage  # pylint: disable=wrong-import-position

NOW = int(time.time())


def iso(seconds):
    return time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(seconds))


def pb_varint(value):
    out = bytearray()
    while True:
        byte, value = value & 0x7F, value >> 7
        out.append(byte | (0x80 if value else 0))
        if not value:
            return bytes(out)


def pb(*items):
    """Encode (field, value) pairs: int as varint, bytes/str as length-delimited."""
    out = b""
    for number, value in items:
        if isinstance(value, int):
            out += pb_varint(number << 3) + value_bytes(value)
        else:
            data = value.encode() if isinstance(value, str) else value
            out += pb_varint(number << 3 | 2) + pb_varint(len(data)) + data
    return out


def value_bytes(value):
    return pb_varint(value)


class AgentUsageTest(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.TemporaryDirectory()
        self.addCleanup(self.home.cleanup)
        env = mock.patch.dict(os.environ, {"HOME": self.home.name, "CODEX_HOME": ""})
        env.start()
        self.addCleanup(env.stop)

    def path(self, *parts):
        path = os.path.join(self.home.name, *parts)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return path

    def run_json(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = agent_usage.main(["--json", *args])
        return status, json.loads(out.getvalue())

    def write_codex(self):
        def count(stamp, inp, cached, out, reasoning):
            return {"timestamp": iso(stamp), "type": "event_msg", "payload": {
                "type": "token_count", "info": {"total_token_usage": {
                    "input_tokens": inp, "cached_input_tokens": cached,
                    "output_tokens": out, "reasoning_output_tokens": reasoning}}}}
        events = [
            {"timestamp": iso(NOW - 60), "type": "turn_context",
             "payload": {"model": "model-a"}},
            count(NOW - 50, 100, 80, 10, 4),
            count(NOW - 45, 100, 80, 10, 4),  # repeated total: not a new call
            count(NOW - 40, 250, 200, 30, 9),
            count(NOW - 99 * 86400, 1, 1, 1, 1),  # backwards total: ignored
        ]
        with open(self.path(".codex", "sessions", "2026", "10", "16", "rollout-x.jsonl"),
                  "w") as stream:
            stream.write("\n".join(json.dumps(e) for e in events) + "\n")

    def test_codex_sums_increases_in_the_running_total(self):
        self.write_codex()
        status, data = self.run_json("--source", "codex")
        self.assertEqual(status, 0)
        (row,) = data["rows"]
        self.assertEqual((row["model"], row["calls"]), ("model-a", 2))
        self.assertEqual((row["input"], row["cached"], row["output"], row["reasoning"]),
                         (250, 200, 30, 9))

    def test_agy_reads_generation_counts_and_step_time(self):
        path = self.path(".gemini", "antigravity-cli", "conversations", "c.db")
        db = sqlite3.connect(path)
        db.execute("create table steps (idx integer, metadata blob)")
        db.execute("create table gen_metadata (idx integer, data blob)")
        db.execute("insert into steps values (0, ?)", (pb((1, pb((1, NOW - 30)))),))
        counts = pb((1, 1320), (2, 1000), (3, 446), (9, 347), (10, 99), (5, 12))
        db.execute("insert into gen_metadata values (0, ?)",
                   (pb((1, pb((4, counts), (19, "gem-x")))),))
        db.commit()
        db.close()
        _, data = self.run_json("--source", "agy")
        (row,) = data["rows"]
        self.assertEqual((row["model"], row["input"], row["output"], row["reasoning"],
                          row["cached"]), ("gem-x", 1000, 446, 347, 12))

    def test_agy_old_conversation_is_outside_the_window(self):
        path = self.path(".gemini", "antigravity-cli", "conversations", "c.db")
        db = sqlite3.connect(path)
        db.execute("create table steps (idx integer, metadata blob)")
        db.execute("create table gen_metadata (idx integer, data blob)")
        db.execute("insert into steps values (0, ?)", (pb((1, pb((1, NOW - 30 * 86400)))),))
        db.execute("insert into gen_metadata values (0, ?)",
                   (pb((1, pb((4, pb((2, 5))), (19, "gem-x")))),))
        db.commit()
        db.close()
        status, data = self.run_json("--source", "agy", "--days", "7")
        self.assertEqual((status, data["rows"]), (1, []))

    def test_muse_attributes_subagent_usage_to_its_own_model(self):
        session = self.path(".local", "share", "muse", "sessions", "2026", "10", "16", "s1",
                            "session.jsonl")
        sub = self.path(".local", "share", "muse", "sessions", "2026", "10", "16", "s1",
                        "subagent", "a1", "session.jsonl")

        def usage(stamp, inp, out):
            return {"recorded_at": stamp * 1_000_000, "payload_type": "runtime.session",
                    "payload": {"event": {"record": {"usage_family": "provider", "quantity": {
                        "unit": "tokens", "input_tokens": inp, "cached_tokens": 1,
                        "output_tokens": out, "reasoning_tokens": 2,
                        "main_llm_steps": 1}}}}}

        def configured(model):
            return {"recorded_at": (NOW - 20) * 1_000_000,
                    "payload_type": "run.model.configured",
                    "payload": {"record": {"model_id": model}}}

        for path, model, inp in ((session, "big", 100), (sub, "small", 7)):
            with open(path, "w") as stream:
                for record in (configured(model), usage(NOW - 10, inp, 3)):
                    stream.write(json.dumps(record) + "\n")
        _, data = self.run_json("--source", "muse")
        got = {(r["model"], r["input"]) for r in data["rows"]}
        self.assertEqual(got, {("big", 100), ("small", 7)})

    def test_repeated_source_counts_once(self):
        self.write_codex()
        _, data = self.run_json("--source", "codex", "--source", "codex")
        self.assertEqual(data["rows"][0]["input"], 250)

    def test_codex_local_time_stamp_is_skipped(self):
        event = {"timestamp": "2026-10-16T12:00:00", "type": "event_msg", "payload": {
            "type": "token_count", "info": {"total_token_usage": {"input_tokens": 9}}}}
        with open(self.path(".codex", "sessions", "2026", "10", "16", "rollout-n.jsonl"),
                  "w") as stream:
            stream.write(json.dumps(event) + "\n")
        _, data = self.run_json("--source", "codex", "--days", "36500")
        self.assertEqual(data["rows"], [])

    def test_unreadable_log_is_skipped_not_fatal(self):
        self.write_codex()
        os.makedirs(self.path(".codex", "sessions", "2026", "10", "16", "rollout-d.jsonl", "x"))
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            status, data = self.run_json("--source", "codex")
        self.assertEqual((status, len(data["rows"])), (0, 1))
        self.assertIn("skipped", errors.getvalue())

    def test_agy_bad_row_skips_the_whole_file(self):
        path = self.path(".gemini", "antigravity-cli", "conversations", "half.db")
        db = sqlite3.connect(path)
        db.execute("create table steps (idx integer, metadata blob)")
        db.execute("create table gen_metadata (idx integer, data blob)")
        db.execute("insert into steps values (0, ?)", (pb((1, pb((1, NOW - 30)))),))
        db.execute("insert into gen_metadata values (0, ?)",
                   (pb((1, pb((4, pb((2, 5))), (19, "gem-x")))),))
        db.execute("insert into gen_metadata values (1, ?)", (b"\x0f\xff",))
        db.commit()
        db.close()
        with contextlib.redirect_stderr(io.StringIO()):
            _, data = self.run_json("--source", "agy")
        self.assertEqual(data["rows"], [])

    def test_nothing_found_exits_1(self):
        status, data = self.run_json()
        self.assertEqual((status, data["rows"]), (1, []))

    def test_corrupt_agy_blob_warns_instead_of_counting(self):
        path = self.path(".gemini", "antigravity-cli", "conversations", "bad.db")
        db = sqlite3.connect(path)
        db.execute("create table steps (idx integer, metadata blob)")
        db.execute("create table gen_metadata (idx integer, data blob)")
        db.execute("insert into gen_metadata values (0, ?)", (b"\x0f\xff",))
        db.commit()
        db.close()
        errors = io.StringIO()
        with contextlib.redirect_stderr(errors):
            status, data = self.run_json("--source", "agy")
        self.assertEqual((status, data["rows"]), (1, []))
        self.assertIn("skipped bad.db", errors.getvalue())


if __name__ == "__main__":
    unittest.main()
