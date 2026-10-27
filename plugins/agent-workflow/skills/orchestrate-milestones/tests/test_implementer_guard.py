# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""The milestone-implementer guard: what it denies, and when it stays out.

portability-scan: intentional. The guard is a Claude Code hook, so these cases use
Claude Code's tool names.
"""

import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
spec = importlib.util.spec_from_file_location("implementer_guard",
                                              SCRIPTS / "implementer_guard.py")
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


def event(command, agent_type="agent-workflow:milestone-implementer", tool="Bash"):
    return {"hook_event_name": "PreToolUse", "agent_type": agent_type,
            "tool_name": tool, "tool_input": {"command": command}}


def decide(payload):
    return guard.main(io.StringIO(json.dumps(payload)))


class ImplementerGuardTests(unittest.TestCase):
    def setUp(self):
        # Keep deny messages off the test output.
        self.stdout, self.stderr = sys.stdout, sys.stderr
        sys.stdout = sys.stderr = io.StringIO()

    def tearDown(self):
        sys.stdout, sys.stderr = self.stdout, self.stderr

    def test_ordinary_work_is_allowed(self):
        for command in ("git status",
                        "git commit -m 'push the parser forward'",
                        "git -C /work/tree log --oneline -5",
                        "git rebase origin/main",
                        "git fetch origin main && git cherry origin/main HEAD",
                        "python3 -m unittest discover -s tests -v",
                        "grep -rn push src/"):
            with self.subTest(command=command):
                self.assertEqual(decide(event(command)), 0)

    def test_pushes_and_gh_are_denied(self):
        for command in ("git push",
                        "git push -u origin feature",
                        "git -C /work/tree push origin HEAD",
                        "git -c push.default=current push",
                        "/usr/bin/git push",
                        "make test && git push",
                        "env GIT_TRACE=1 git push",
                        "sh -c 'git push origin HEAD'",
                        "gh pr create --fill",
                        "gh pr merge 12 --squash",
                        "gh api repos/o/r/pulls",
                        "echo $(gh auth token)"):
            with self.subTest(command=command):
                self.assertEqual(decide(event(command)), 2)

    def test_deny_speaks_both_dialects(self):
        out = io.StringIO()
        sys.stdout = out
        self.assertEqual(decide(event("git push")), 2)
        decision = json.loads(out.getvalue())["hookSpecificOutput"]
        self.assertEqual(decision["permissionDecision"], "deny")
        self.assertIn("orchestrator", decision["permissionDecisionReason"])

    def test_other_agents_and_tools_get_no_opinion(self):
        for payload in (event("git push", agent_type=None),
                        event("git push", agent_type="agent-workflow:consult-runner"),
                        event("git push", agent_type="milestone-implementer-extra"),
                        event("git push", tool="Read")):
            with self.subTest(payload=payload):
                self.assertEqual(decide(payload), 0)

    def test_bare_agent_name_is_recognized(self):
        self.assertEqual(decide(event("git push", agent_type="milestone-implementer")), 2)

    def test_unparseable_input_gets_no_opinion(self):
        self.assertEqual(guard.main(io.StringIO("not json")), 0)
        self.assertEqual(guard.main(io.StringIO("[]")), 0)


if __name__ == "__main__":
    unittest.main()
