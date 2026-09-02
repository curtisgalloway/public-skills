#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/portability_scan.py.

Run:  python3 -m unittest discover -s plugins/agent-workflow/skills/agent-agnostic-skills/tests -v

The two fixtures are the same small skill written twice — once welded to one
harness, once bound to stable layers — so the suite checks a difference in
authoring style rather than a difference in subject matter.

The test that matters most is test_ladder_is_not_lock_in: the scanner's whole
premise is that naming several harnesses together is translation, not
lock-in. Lose that distinction and the tool either flags every compatibility
table it should be encouraging, or stops flagging anything.
"""

import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SCAN = HERE.parent / "scripts" / "portability_scan.py"
FIX = HERE / "fixtures"
REPO = next(p for p in HERE.parents if (p / ".claude-plugin" / "marketplace.json").is_file())


def sibling_skill(name: str) -> pathlib.Path:
    """A skill elsewhere in this repo, whichever theme directory holds it."""
    hits = sorted(REPO.glob(f"plugins/*/skills/{name}")) or [REPO / "skills" / name]
    return hits[0]


def run_scan(*args):
    proc = subprocess.run(
        [sys.executable, str(SCAN)] + [str(a) for a in args],
        capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


class TestLockedSkill(unittest.TestCase):
    """Every check should fire on the fixture that earns it."""

    def setUp(self):
        self.rc, self.out = run_scan(FIX / "locked_skill")

    def test_findings_are_reported(self):
        self.assertEqual(self.rc, 1, self.out)

    def test_single_harness_path(self):
        self.assertIn("single-harness-path", self.out)
        self.assertIn(".claude/skills/locked-skill", self.out)

    def test_single_harness_env(self):
        self.assertIn("single-harness-env", self.out)
        self.assertIn("CLAUDE_PROJECT_DIR", self.out)

    def test_brand_context_file(self):
        self.assertIn("brand-context-file", self.out)

    def test_tool_name_table(self):
        """A dict keyed on one harness's tool names is the classic lock-in."""
        self.assertIn("tool-name-table", self.out)

    def test_absolute_home_path(self):
        self.assertIn("absolute-home-path", self.out)


class TestPortableSkill(unittest.TestCase):

    def test_portable_fixture_is_clean(self):
        """Same skill, stable bindings: nothing to report.

        It still names .claude and .gemini paths — in a ladder — which is
        exactly what must not be flagged.
        """
        rc, out = run_scan(FIX / "portable_skill")
        self.assertEqual(rc, 0, out)
        self.assertIn("0 finding(s)", out)

    def test_reference_implementation_is_clean(self):
        """The scripts this skill points at as worked examples must pass.

        If a change to the clean-room hook or auditor reintroduces a
        tool-name table or a single-harness path, this goes red — the skill
        should not be able to recommend code that fails its own check.
        """
        rc, out = run_scan(sibling_skill("cleanroom-implementer") / "scripts")
        self.assertEqual(rc, 0, out)


class TestHeuristics(unittest.TestCase):

    def scan_text(self, name, body):
        with tempfile.TemporaryDirectory() as tmp:
            path = pathlib.Path(tmp) / name
            path.write_text(body)
            return run_scan(path)

    def test_ladder_is_not_lock_in(self):
        """Naming several harnesses together is translation, not lock-in.

        This is the scanner's central distinction. A compatibility ladder is
        the pattern the skill argues for, so flagging it would train people
        out of the right answer.
        """
        rc, out = self.scan_text("ladder.py", (
            'ROOTS = (".agents/skills", ".gemini/skills", ".claude/skills")\n'))
        self.assertEqual(rc, 0, out)

    def test_lone_harness_path_is_lock_in(self):
        rc, out = self.scan_text("lone.py", 'ROOT = ".claude/skills"\n')
        self.assertEqual(rc, 1, out)
        self.assertIn("single-harness-path", out)

    def test_shared_tool_names_are_not_a_table(self):
        """read_file and grep_search belong to more than one harness.

        A vocabulary several agents share is not evidence of lock-in, so the
        check must resolve names to families rather than counting them.
        """
        rc, out = self.scan_text("shared.py", (
            'TOOLS = ("read_file", "write_file", "grep_search")\n'))
        self.assertEqual(rc, 0, out)

    def test_placeholder_home_paths_are_fine(self):
        """/home/dev/ is the fix this check asks for, not a violation."""
        rc, out = self.scan_text("ph.md", "See /home/dev/src/thing for the layout.\n")
        self.assertEqual(rc, 0, out)

    def test_real_looking_home_path_is_flagged(self):
        body = "See /home/rjmiller/src/thing.\n"  # portability-ok: check input
        rc, out = self.scan_text("real.md", body)
        self.assertEqual(rc, 1, out)
        self.assertIn("absolute-home-path", out)

    def test_line_suppression(self):
        rc, out = self.scan_text("sup.py", (
            'ROOT = ".claude/skills"  # deliberate: portability-ok\n'))
        self.assertEqual(rc, 0, out)

    def test_file_suppression(self):
        """For a file that is single-harness by design, e.g. an install asset."""
        rc, out = self.scan_text("asset.md", (
            "<!-- portability-scan: intentional - Claude Code install asset -->\n"
            "Install to `~/.claude/agents/thing.md`.\n"))
        self.assertEqual(rc, 0, out)

    def test_missing_path_is_error(self):
        rc, out = run_scan(HERE / "no-such-directory")
        self.assertEqual(rc, 2, out)


if __name__ == "__main__":
    unittest.main()
