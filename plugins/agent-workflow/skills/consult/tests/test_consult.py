# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Exercise real worker processes against deterministic, local fake CLIs."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "consult.py"
spec = importlib.util.spec_from_file_location("consult", SCRIPT)
consult = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consult)

FAKE = r'''
import json, os, pathlib, sys, time, uuid
args = sys.argv[1:]
prompt = sys.stdin.read()
peer = pathlib.Path(sys.argv[0]).name
root = pathlib.Path(os.environ["FAKE_STATE"])
if "resume" in args:
    session = args[args.index("--skip-git-repo-check") + 1]
elif "--resume" in args:
    session = args[args.index("--resume") + 1]
else:
    session = str(uuid.uuid4())
history_path = root / session
history = json.loads(history_path.read_text()) if history_path.exists() else []
if ("resume" in args or "--resume" in args) and not history:
    sys.exit(8)
history.append({"prompt": prompt, "args": args, "cwd": os.getcwd(),
                "peer_guard": os.environ.get("CONSULT_PEER")})
history_path.write_text(json.dumps(history))
if "FIXTURE_FAIL" in prompt:
    print("authentication unavailable", file=sys.stderr)
    sys.exit(7)
if "FIXTURE_SLEEP" in prompt:
    time.sleep(30)
if "FIXTURE_MALFORMED" in prompt:
    print("not JSON")
    sys.exit(0)
answer = "Retained initial context: " + history[0]["prompt"] + "\nTurn: " + str(len(history))
if peer == "claude":
    print(json.dumps({"subtype": "success", "is_error": False,
                      "session_id": session, "result": answer}))
else:
    print(json.dumps({"type": "thread.started", "thread_id": session}))
    print(json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": answer}}))
    print(json.dumps({"type": "turn.completed"}))
'''


class ConsultationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.project = self.root / "project with spaces"
        self.project.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.fake_state = self.root / "fake-state"
        self.fake_state.mkdir()
        for peer in ("claude", "codex"):
            path = self.bin / peer
            path.write_text("#!" + sys.executable + "\n" + FAKE)
            path.chmod(0o700)
        self.state = self.root / "state"
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
                        FAKE_STATE=str(self.fake_state))
        self.env.pop("CONSULT_PEER", None)
        self.ids = []

    def tearDown(self):
        for identity in self.ids:
            result = self.run_cli("status", identity, check=False)
            if result.get("status") in {"running", "closing"}:
                self.run_cli("close", identity, "--outcome", "cancelled")
                self.wait(identity)
        self.temp.cleanup()

    def command(self, *args):
        return [sys.executable, str(SCRIPT), "--state-dir", str(self.state), *args]

    def run_cli(self, *args, text=None, check=True):
        result = subprocess.run(self.command(*args), input=text, text=True,
                                capture_output=True, env=self.env, timeout=10)
        if check:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def start(self, origin="codex", text="Independent brief: token maple", *extra):
        state = self.run_cli("start", "--from", origin, "--project", str(self.project),
                             "--message-file", "-", *extra, text=text)
        self.ids.append(state["id"])
        return state["id"]

    def wait(self, identity):
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            state = self.run_cli("status", identity, check=False)
            if state["status"] not in {"running", "closing"}:
                return state
            time.sleep(0.03)
        self.fail("Worker did not finish")

    def test_both_directions_retain_context_and_confirm(self):
        for origin, peer in (("claude", "codex"), ("codex", "claude")):
            with self.subTest(origin=origin):
                identity = self.start(origin)
                first = self.wait(identity)
                self.assertEqual(first["status"], "ready", first)
                self.assertEqual(first["peer"], peer)
                self.run_cli("reply", identity, "--message-file", "-", text="Consider a different approach")
                second = self.wait(identity)
                self.assertEqual(first["session_id"], second["session_id"])
                self.run_cli("reply", identity, "--phase", "confirm", "--message-file", "-",
                             text="Confirm this exact proposal")
                third = self.wait(identity)
                self.assertEqual(first["session_id"], third["session_id"])
                transcript = self.run_cli("read", identity, "--all")["messages"]
                self.assertEqual(len(transcript), 3)
                self.assertIn("token maple", transcript[-1]["answer"])
                self.assertIn("Turn: 3", transcript[-1]["answer"])
                closed = self.run_cli("close", identity, "--outcome", "consensus", "--summary-file", "-",
                                      text="The exact proposal")
                self.assertEqual(closed["status"], "closed")
                history = json.loads((self.fake_state / first["session_id"]).read_text())
                for turn in history:
                    self.assertEqual(turn["peer_guard"], "1")
                    self.assertEqual(turn["cwd"], str(self.project.resolve()))
                    args = turn["args"]
                    if peer == "claude":
                        self.assertEqual(args[args.index("--tools") + 1], "Read,Glob,Grep")
                        self.assertIn("--strict-mcp-config", args)
                    else:
                        self.assertEqual(args[args.index("-s") + 1], "read-only")
                        self.assertEqual(args[args.index("-a") + 1], "never")
                        self.assertIn("--ignore-user-config", args)

    def test_requires_confirmation_and_bounds_rounds(self):
        identity = self.start("codex", "brief", "--rounds", "1")
        self.wait(identity)
        rejected = self.run_cli("close", identity, "--outcome", "consensus", "--summary-file", "-",
                                text="Unconfirmed", check=False)
        self.assertIn("confirmation", rejected["error"])
        self.run_cli("reply", identity, "--message-file", "-", text="Compare")
        self.wait(identity)
        rejected = self.run_cli("reply", identity, "--message-file", "-", text="Again", check=False)
        self.assertIn("limit", rejected["error"])
        self.run_cli("reply", identity, "--phase", "confirm", "--message-file", "-", text="Confirm")
        self.wait(identity)
        rejected = self.run_cli("reply", identity, "--message-file", "-", text="Again", check=False)
        self.assertIn("Confirmation already", rejected["error"])

    def test_failures_are_visible_and_cannot_be_resumed(self):
        for token in ("FIXTURE_FAIL", "FIXTURE_MALFORMED"):
            identity = self.start(text=token)
            state = self.wait(identity)
            self.assertEqual(state["status"], "failed")
            self.assertTrue(state["error"])
            rejected = self.run_cli("reply", identity, "--message-file", "-", text="retry", check=False)
            self.assertIn("successful idle", rejected["error"])

    def test_timeout_and_cancellation(self):
        identity = self.start("claude", "FIXTURE_SLEEP", "--timeout", "1")
        self.assertIn("timed out", self.wait(identity)["error"])
        identity = self.start(text="FIXTURE_SLEEP")
        rejected = self.run_cli("reply", identity, "--message-file", "-", text="competing reply", check=False)
        self.assertIn("successful idle", rejected["error"])
        self.run_cli("close", identity, "--outcome", "cancelled")
        self.assertEqual(self.wait(identity)["status"], "closed")

    def test_distinct_consultations_do_not_share_sessions(self):
        first, second = self.start(), self.start()
        self.assertNotEqual(self.wait(first)["session_id"], self.wait(second)["session_id"])

    def test_reopen_preserves_session(self):
        identity = self.start()
        session = self.wait(identity)["session_id"]
        self.run_cli("close", identity, "--outcome", "unresolved", "--summary-file", "-", text="Need evidence")
        self.run_cli("reply", identity, "--reopen", "--message-file", "-", text="New evidence")
        self.assertEqual(self.wait(identity)["session_id"], session)

    def test_failed_followup_cannot_be_reopened_after_close(self):
        identity = self.start()
        self.wait(identity)
        self.run_cli("reply", identity, "--message-file", "-", text="FIXTURE_FAIL")
        self.assertEqual(self.wait(identity)["status"], "failed")
        self.run_cli("close", identity, "--outcome", "unresolved", "--summary-file", "-", text="Failure")
        rejected = self.run_cli("reply", identity, "--reopen", "--message-file", "-",
                                text="Retry ambiguous work", check=False)
        self.assertIn("successful idle", rejected["error"])

    def test_simultaneous_replies_launch_only_one_peer_turn(self):
        identity = self.start()
        first = self.wait(identity)
        command = self.command("reply", identity, "--message-file", "-")
        processes = [subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE, text=True, env=self.env) for _ in range(2)]
        # Both calls contend for the same lock; the accepted peer remains busy.
        for process in processes:
            process.stdin.write("FIXTURE_SLEEP")
            process.stdin.close()
            process.stdin = None
        results = [process.communicate(timeout=10) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 1], results)
        state = self.run_cli("status", identity)
        self.assertEqual(len(state["jobs"]), 2)
        self.assertEqual(state["session_id"], first["session_id"])

    def test_missing_cli_fails_before_creating_state(self):
        (self.bin / "claude").unlink()
        self.env["PATH"] = str(self.bin)
        rejected = self.run_cli("start", "--from", "codex", "--project", str(self.project),
                                "--message-file", "-", text="brief", check=False)
        self.assertIn("not found", rejected["error"])
        self.assertFalse(self.state.exists())

    def test_abandoned_worker_is_reported_without_signalling_saved_pid(self):
        identity = self.start()
        self.wait(identity)
        path = self.state / identity / "state.json"
        state = json.loads(path.read_text())
        state["status"] = "running"
        path.write_text(json.dumps(state))
        state = self.run_cli("status", identity, check=False)
        self.assertEqual(state["status"], "failed")
        self.assertIn("Worker exited", state["error"])

    def test_state_private_and_outside_project(self):
        identity = self.start()
        self.wait(identity)
        directory = self.state / identity
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.assertEqual((directory / "state.json").stat().st_mode & 0o777, 0o600)
        self.assertEqual(list(self.project.iterdir()), [])
        rejected = self.run_cli("start", "--from", "codex", "--project", str(self.root),
                                "--message-file", "-", text="brief", check=False)
        self.assertIn("outside", rejected["error"])

    def test_peer_guard_and_invalid_id(self):
        self.env["CONSULT_PEER"] = "1"
        rejected = self.run_cli("start", "--from", "codex", "--message-file", "-", text="brief", check=False)
        self.assertIn("recursively", rejected["error"])
        self.env.pop("CONSULT_PEER")
        rejected = self.run_cli("status", "../escape", check=False)
        self.assertIn("Invalid", rejected["error"])

    def test_parser_rejects_partial_or_failed_turns(self):
        for peer, raw in [
            ("claude", '{"subtype":"error_max_turns","is_error":true}'),
            ("codex", '{"type":"thread.started","thread_id":"example"}'),
            ("codex", '{"type":"error","message":"failed"}'),
        ]:
            with self.subTest(peer=peer), self.assertRaises(consult.ConsultError):
                consult.parse_response(peer, raw)


if __name__ == "__main__":
    unittest.main()
