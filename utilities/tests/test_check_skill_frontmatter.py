# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for utilities/check-skill-frontmatter.py."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "check_skill_frontmatter", HERE.parent / "check-skill-frontmatter.py")
csf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csf)


class CheckFileTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def skill(self, name: str, body: str) -> Path:
        path = Path(self.tmp.name, name, "SKILL.md")
        path.parent.mkdir(parents=True)
        path.write_text(body, encoding="utf-8")
        return path

    def check(self, path: Path, *, is_skill: bool = True) -> list[str]:
        return csf.check_file(path, yaml, is_skill=is_skill)

    def test_valid_skill_passes(self):
        path = self.skill("demo", "---\nname: demo\ndescription: Does a thing.\n---\n\nBody\n")
        self.assertEqual(self.check(path), [])

    def test_folded_description_passes(self):
        path = self.skill("demo", "---\nname: demo\ndescription: >-\n  Uses x.py: a\n  colon.\n---\n")
        self.assertEqual(self.check(path), [])

    def test_plain_scalar_with_colon_space_fails(self):
        path = self.skill("demo", "---\nname: demo\ndescription: Uses x.py: status, more\n---\n")
        [problem] = self.check(path)
        self.assertIn("not valid YAML", problem)

    def test_long_description_fails(self):
        path = self.skill("demo", f"---\nname: demo\ndescription: {'a' * 1025}\n---\n")
        [problem] = self.check(path)
        self.assertIn("1025 characters", problem)

    def test_description_at_limit_passes(self):
        path = self.skill("demo", f"---\nname: demo\ndescription: {'a' * 1024}\n---\n")
        self.assertEqual(self.check(path), [])

    def test_name_must_match_directory(self):
        path = self.skill("demo", "---\nname: other\ndescription: x\n---\n")
        [problem] = self.check(path)
        self.assertIn("does not match", problem)

    def test_name_charset(self):
        path = self.skill("Demo_1", "---\nname: Demo_1\ndescription: x\n---\n")
        [problem] = self.check(path)
        self.assertIn("lowercase", problem)

    def test_missing_frontmatter_fails(self):
        path = self.skill("demo", "# demo\n")
        [problem] = self.check(path)
        self.assertIn("no '---' frontmatter", problem)

    def test_missing_description_fails(self):
        path = self.skill("demo", "---\nname: demo\n---\n")
        [problem] = self.check(path)
        self.assertIn("`description`", problem)

    def test_agent_name_need_not_match_directory(self):
        path = self.skill("agents", "---\nname: helper\ndescription: x\n---\n")
        self.assertEqual(self.check(path, is_skill=False), [])


class RepoTest(unittest.TestCase):
    def test_repository_passes(self):
        self.assertEqual(csf.main(["--root", str(HERE.parent.parent)]), 0)


if __name__ == "__main__":
    unittest.main()
