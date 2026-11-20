# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Run the handoff's published shell instructions against real Git checkouts."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


SKILL = Path(__file__).resolve().parents[1] / "SKILL.md"
HANDOFF_NAMES = ("HANDOFF.md", "HANDOFF.md.read")
GITIGNORE = b"*.log\n"
EXISTING_EXCLUDE = b"*.local-settings"


class ExcludeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        section = SKILL.read_text().split("### 3. Exclude it from git\n", 1)[1]
        section = section.split("\n### ", 1)[0]
        block = re.search(r"^```sh\n(.*?)^```$", section, re.MULTILINE | re.DOTALL)
        if block is None:
            raise AssertionError("Missing shell block in handoff exclusion instructions")
        cls.script = block[1]

    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="handoff test ")
        self.addCleanup(temp.cleanup)
        root = Path(temp.name)
        self.primary = root / "primary checkout"
        self.primary.mkdir()
        self.linked = root / "linked checkout"
        self.exclude = self.primary / ".git" / "info" / "exclude"
        self.env = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        self.env.update(
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_CONFIG_NOSYSTEM="1",
            XDG_CONFIG_HOME=str(root / "config"),
        )
        self.git(self.primary, "init", "--quiet", "--template=")
        self.exclude.parent.mkdir(exist_ok=True)
        self.exclude.write_bytes(EXISTING_EXCLUDE)
        (self.primary / ".gitignore").write_bytes(GITIGNORE)
        self.git(self.primary, "add", ".gitignore")
        self.git(
            self.primary, "-c", "user.name=Test", "-c", "user.email=test@example.com",
            "commit", "--quiet", "-m", "Track ignore rules",
        )

    def git(self, checkout, *args):
        return subprocess.run(
            ["git", "-C", str(checkout), *args], env=self.env,
            capture_output=True, text=True, check=True,
        ).stdout.strip()

    def run_snippet(self, checkout, **env):
        for name in HANDOFF_NAMES:
            (checkout / name).touch()
        result = subprocess.run(
            ["sh", "-s"], input=self.script, cwd=checkout, env=self.env | env,
            capture_output=True, text=True,
        )
        self.assertEqual((checkout / ".gitignore").read_bytes(), GITIGNORE)
        return result

    def assert_handoff_ignored(self, checkout):
        for name in HANDOFF_NAMES:
            self.git(checkout, "check-ignore", "--quiet", "--", name)

    def assert_exclusion_is_idempotent(self, checkout):
        result = self.run_snippet(checkout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_handoff_ignored(checkout)
        exclude = self.exclude.read_bytes()
        self.assertIn(EXISTING_EXCLUDE, exclude.splitlines())
        self.assertIn(b"HANDOFF.md*", exclude.splitlines())
        result = self.run_snippet(checkout)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.exclude.read_bytes(), exclude)

    def test_primary_checkout(self):
        self.assert_exclusion_is_idempotent(self.primary)

    def test_existing_rule_covers_only_the_active_handoff(self):
        self.exclude.write_bytes(EXISTING_EXCLUDE + b"\nHANDOFF.md\n")
        self.assert_exclusion_is_idempotent(self.primary)

    def test_linked_checkout_uses_shared_exclude(self):
        self.git(self.primary, "worktree", "add", "--quiet", "--detach", str(self.linked))
        self.assert_exclusion_is_idempotent(self.linked)
        self.assert_handoff_ignored(self.primary)

    def test_failed_git_resolution_falls_back_in_primary_checkout(self):
        result = self.run_snippet(self.primary, GIT_DIR="missing git directory")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not verify", result.stderr)
        self.assert_handoff_ignored(self.primary)

    def test_failed_git_resolution_does_not_guess_in_linked_checkout(self):
        self.git(self.primary, "worktree", "add", "--quiet", "--detach", str(self.linked))
        pointer = self.linked / ".git"
        original_pointer = pointer.read_bytes()
        git_dir = Path(self.git(self.linked, "rev-parse", "--absolute-git-dir"))

        result = self.run_snippet(self.linked, GIT_DIR="missing git directory")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Could not locate", result.stderr)
        self.assertEqual(self.exclude.read_bytes(), EXISTING_EXCLUDE)
        self.assertEqual(pointer.read_bytes(), original_pointer)
        self.assertFalse((git_dir / "info" / "exclude").exists())
