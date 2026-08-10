#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/cleanroom_hook.py.

Run:  python3 -m unittest discover -s skills/cleanroom-implementer/tests -v

Each case drives the hook the way Claude Code does: a PreToolUse JSON event
on stdin, exit 0 to allow or 2 to block. CLAUDE_PROJECT_DIR is pointed at a
temp dir per test so the hook's log never touches a real project.

Two invariants here are deliberate design decisions that a well-meaning
future edit would break: content is not scanned (test_edit_content_is_not_
scanned), and malformed input allows rather than blocks (test_malformed_
input_allows).
"""

import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
HOOK = HERE.parent / "scripts" / "cleanroom_hook.py"
FIX = HERE / "fixtures"

BLOCKED_PATH = "/home/dev/src/linux/drivers/tty/serial/widgetron.c"


class HookCase(unittest.TestCase):

    def fire(self, tool, tool_input, role=None, policy=None):
        """Send one PreToolUse event; return (rc, stderr, log_entries)."""
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["CLAUDE_PROJECT_DIR"] = tmp
            env.pop("CLEANROOM_ROLE", None)
            if role is not None:
                env["CLEANROOM_ROLE"] = role
            if policy is not None:
                env["CLEANROOM_POLICY"] = str(policy)
            else:
                env.pop("CLEANROOM_POLICY", None)
            event = json.dumps({"tool_name": tool, "tool_input": tool_input,
                                "session_id": "test-session"})
            proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                                  capture_output=True, text=True, env=env)
            log = pathlib.Path(tmp) / "docs" / "provenance" / "hook-blocks.jsonl"
            entries = []
            if log.is_file():
                entries = [json.loads(ln) for ln in
                           log.read_text().splitlines() if ln.strip()]
            return proc.returncode, proc.stderr, entries


class TestBlocking(HookCase):

    def test_blocked_path_without_role(self):
        rc, err, log = self.fire("Read", {"file_path": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)
        self.assertIn("BLOCKED", err)
        self.assertIn("spec-gap", err)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["action"], "blocked")

    def test_blocked_url_via_webfetch(self):
        rc, err, log = self.fire(
            "WebFetch", {"url": "https://git.kernel.org/pub/scm/linux/x.c"})
        self.assertEqual(rc, 2, err)
        self.assertEqual(log[0]["action"], "blocked")

    def test_websearch_query_is_checked_against_urls(self):
        rc, err, _ = self.fire(
            "WebSearch", {"query": "widgetron driver site:kernel.org"})
        self.assertEqual(rc, 2, err)

    def test_bash_command_is_checked(self):
        rc, err, _ = self.fire(
            "Bash", {"command": "git clone https://github.com/torvalds/linux"})
        self.assertEqual(rc, 2, err)

    def test_unknown_mcp_tool_is_checked_for_urls(self):
        """settings-fragment.json wires matcher '*' precisely for this."""
        rc, err, _ = self.fire(
            "mcp__fetcher__get",
            {"target": "https://kernel.org/doc/widgetron.html"})
        self.assertEqual(rc, 2, err)


class TestAllowing(HookCase):

    def test_benign_path_is_silent(self):
        rc, err, log = self.fire(
            "Read", {"file_path": "docs/widgetron-spec.md"})
        self.assertEqual(rc, 0, err)
        self.assertEqual(err, "")
        self.assertEqual(log, [], "benign calls must not be logged")

    def test_investigator_role_allows_and_logs(self):
        rc, err, log = self.fire("Read", {"file_path": BLOCKED_PATH},
                                 role="investigator")
        self.assertEqual(rc, 0, err)
        self.assertEqual(len(log), 1, "authorized reads must still be logged")
        self.assertEqual(log[0]["action"], "allowed-role")
        self.assertEqual(log[0]["role"], "investigator")

    def test_verifier_role_allows(self):
        rc, err, log = self.fire("Read", {"file_path": BLOCKED_PATH},
                                 role="verifier")
        self.assertEqual(rc, 0, err)
        self.assertEqual(log[0]["action"], "allowed-role")

    def test_unrecognised_role_still_blocks(self):
        rc, err, _ = self.fire("Read", {"file_path": BLOCKED_PATH},
                               role="implementer")
        self.assertEqual(rc, 2, err)

    def test_edit_content_is_not_scanned(self):
        """Deliberate: a comment naming a blocked project must not block.

        Content-level leaks belong to session_audit and the output scan.
        Scanning Edit/Write content here would false-positive on prose.
        """
        rc, err, log = self.fire("Edit", {
            "file_path": "src/devices/widgetron/driver.rs",
            "old_string": "// TODO",
            "new_string": "// Ported clean-room; do not consult "
                          "trusted-firmware-a or linux/drivers/ for this.",
        })
        self.assertEqual(rc, 0, err)
        self.assertEqual(log, [])

    def test_malformed_input_allows(self):
        """The hook must never break a session on bad input."""
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["CLAUDE_PROJECT_DIR"] = tmp
            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input="this is not json",
                                  capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestPolicyPlumbing(HookCase):

    def test_custom_policy_file_is_honoured(self):
        path = "/home/dev/src/acme-vendor-blob-sdk/hal/widgetron.c"
        rc, _, _ = self.fire("Read", {"file_path": path})
        self.assertEqual(rc, 0, "not blocked by the built-in defaults")
        rc, err, log = self.fire("Read", {"file_path": path},
                                 policy=FIX / "custom-policy.json")
        self.assertEqual(rc, 2, err)
        self.assertIn("acme-vendor-blob-sdk", log[0]["pattern"])


if __name__ == "__main__":
    unittest.main()
