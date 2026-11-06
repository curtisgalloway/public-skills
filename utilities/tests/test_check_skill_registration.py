# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for the marketplace checks in utilities/check-skill-registration.py."""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location(
    "check_skill_registration", HERE.parent / "check-skill-registration.py")
csr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(csr)

THEMES = ["agent-workflow", "dev-tools", "hardware-lab"]


def marketplace(bundle_skills: list[str] | None, *, bundle: bool = True) -> dict:
    plugins = [{"name": t, "source": f"./plugins/{t}"} for t in THEMES]
    if bundle:
        entry = {"name": csr.BUNDLE, "source": "./"}
        if bundle_skills is not None:
            entry["skills"] = bundle_skills
        plugins.append(entry)
    return {"plugins": plugins}


class CheckMarketplaceTest(unittest.TestCase):

    def test_full_bundle_passes(self) -> None:
        data = marketplace([f"./plugins/{t}/skills" for t in THEMES])
        self.assertEqual(csr.check_marketplace(THEMES, data), [])

    def test_missing_bundle_fails(self) -> None:
        failures = csr.check_marketplace(THEMES, marketplace(None, bundle=False))
        self.assertEqual(len(failures), 1)
        self.assertIn("bundle entry missing", failures[0])

    def test_empty_skills_list_fails(self) -> None:
        for skills in ([], None):
            failures = csr.check_marketplace(THEMES, marketplace(skills))
            self.assertEqual(len(failures), 1, skills)
            self.assertIn("no skills[]", failures[0])

    def test_one_missing_theme_dir_fails(self) -> None:
        data = marketplace([f"./plugins/{t}/skills" for t in THEMES if t != "dev-tools"])
        failures = csr.check_marketplace(THEMES, data)
        self.assertEqual(failures,
                         [f"dev-tools: ./plugins/dev-tools/skills missing from the "
                          f"{csr.BUNDLE} bundle skills[]"])

    def test_missing_theme_entry_still_reported(self) -> None:
        data = marketplace([f"./plugins/{t}/skills" for t in THEMES])
        data["plugins"] = [p for p in data["plugins"] if p["name"] != "hardware-lab"]
        failures = csr.check_marketplace(THEMES, data)
        self.assertIn("hardware-lab: no entry in marketplace.json", failures)

    def test_repo_marketplace_names_the_bundle(self) -> None:
        names = {p["name"] for p in json.loads(csr.MARKETPLACE.read_text())["plugins"]}
        self.assertIn(csr.BUNDLE, names)


if __name__ == "__main__":
    unittest.main()
