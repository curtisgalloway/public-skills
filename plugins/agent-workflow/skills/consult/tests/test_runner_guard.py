# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""The consult-runner guard: what it allows, what it denies, and when it stays out.

portability-scan: intentional. The guard is a Claude Code hook (Codex hooks cannot
tell which agent made a call), so these cases use Claude Code's tool names.
"""

import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("runner_guard", SCRIPTS / "runner_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)
HELPER = str(SCRIPTS / "consult.py")


def event(command, agent_type="agent-workflow:consult-runner", tool="Bash"):
    return {"hook_event_name": "PreToolUse", "agent_type": agent_type,
            "tool_name": tool, "tool_input": {"command": command}}


def decide(payload):
    return guard.main(io.StringIO(json.dumps(payload)))


class RunnerGuardTests(unittest.TestCase):
    def setUp(self):
        # Keep deny messages off the test output.
        self.stdout, self.stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = io.StringIO()

    def tearDown(self):
        sys.stdout, sys.stderr = self.stdout, self.stderr

    def test_helper_commands_are_allowed(self):
        heredoc = ("python3 %s start --from claude --to codex --project '/a b' "
                   "--message-file - <<'CONSULT_EOF'\nUse $(rm -rf /) && `x`; | > *\n"
                   "CONSULT_EOF" % HELPER)
        for command in ("python3 %s wait 1234 --timeout 540" % HELPER,
                        "python3 '%s' read 1234 --all" % HELPER,
                        "/usr/bin/python3.12 %s status 1234" % HELPER,
                        "python3 %s --runner" % HELPER,
                        heredoc):
            with self.subTest(command=command):
                self.assertEqual(decide(event(command)), 0)

    def test_everything_else_is_denied(self):
        for command in ("ls -la",
                        "agy -p hi --dangerously-skip-permissions",
                        "python3 /tmp/consult.py status 1",
                        "python3 -c 'import os'",
                        "python3 %s status 1; rm -rf ~" % HELPER,
                        "python3 %s status 1 && ls" % HELPER,
                        "python3 %s status $(id -u)" % HELPER,
                        'python3 %s status "$HOME"' % HELPER,
                        "python3 %s status 1 > /tmp/out" % HELPER,
                        "python3 %s status 1\nls" % HELPER,
                        "python3 %s start <<EOF\nunquoted\nEOF" % HELPER,
                        "python3 %s start <<'E'\nbody\nE\nls" % HELPER,
                        "python3 %s start <<'E'\nE\nmore\nE" % HELPER,
                        "cd /tmp && python3 %s status 1" % HELPER,
                        "bash -c 'python3 %s status 1'" % HELPER,
                        ""):
            with self.subTest(command=command):
                self.assertEqual(decide(event(command)), 2)

    def test_other_tools_are_denied(self):
        for tool in ("Write", "Read", "Edit", "WebFetch"):
            with self.subTest(tool=tool):
                self.assertEqual(decide(event(None, tool=tool)), 2)

    def test_other_agents_and_bad_input_get_no_opinion(self):
        # Exit 0 with no output: the guard must never break or auto-approve anyone else's calls.
        for payload in (event("rm -rf /", agent_type=None), event("rm -rf /", agent_type="Explore"),
                        event("rm -rf /", agent_type="consult-runner-2"), {"tool_name": "Bash"}):
            with self.subTest(payload=payload):
                sys.stdout = io.StringIO()
                self.assertEqual(decide(payload), 0)
                self.assertEqual(sys.stdout.getvalue(), "")
        self.assertEqual(guard.main(io.StringIO("not json")), 0)

    def test_deny_speaks_both_claude_code_dialects(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "runner_guard.py")],
                                input=json.dumps(event("ls")), text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        decision = json.loads(result.stdout)["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("consult.py", result.stderr)


if __name__ == "__main__":
    unittest.main()
