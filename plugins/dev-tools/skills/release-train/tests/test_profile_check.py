#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for scripts/profile_check.py.

Run:  python3 -m unittest discover -s plugins/dev-tools/skills/release-train/tests -v

Each test builds a tiny repo (a workflow, a packaging dir, a README) and a
profile that cites them, then runs the checker as a subprocess and asserts
on its exit code and findings. The ones that matter most: a changed source
must be CHANGED (exit 1), a vanished path must be MISSING, an arm without
its required bullets must be refused, and --update must re-pin so the next
run is clean, without touching any other line.
"""

import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
CHECK = HERE.parent / "scripts" / "profile_check.py"

WORKFLOW = """\
name: Release
jobs:
  package:
    name: package (linux)
    runs-on: ubuntu-latest
  package-windows:
    name: package (windows x86_64)
    runs-on: windows-latest
"""


def profile_text(blob_wf: str, blob_pkg: str, arm_extra: str = "") -> str:
    return f"""# Release train profile: demo

Derived from commit unknown on 2026-01-01.

## Project

- cli: `demo`
- release workflow: `.github/workflows/release.yml`

## Hosts

| role | needed by | what it must have |
|---|---|---|
| local | deb | cargo |

## Smoke contract

| id | check | pass condition |
|---|---|---|
| S1 | `demo --help` | exit 0 |
| S2 | `demo skill` | lists skills |

## Channels

### deb

- kind: deb
- artifact: `demo_X_amd64.deb`
- workflow job: package
- build: `packaging/build.sh`
- install like a user: apt install
- smoke: S1..S2
- cleanup: apt remove
{arm_extra}
## Archaeology

- issue source: gh

## Publish

- gate: ask

## Sources

| path | blob | feeds |
|---|---|---|
| `.github/workflows/release.yml` | {blob_wf} | Channels |
| `packaging/build.sh` | {blob_pkg} | Channels: deb |
"""


def run(args, cwd):
    return subprocess.run(
        [sys.executable, str(CHECK), *args], cwd=cwd, capture_output=True, text=True, check=False
    )


class ProfileCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = pathlib.Path(self.tmp.name)
        (self.repo / ".github" / "workflows").mkdir(parents=True)
        (self.repo / ".github" / "workflows" / "release.yml").write_text(WORKFLOW)
        (self.repo / "packaging").mkdir()
        (self.repo / "packaging" / "build.sh").write_text("#!/bin/sh\necho build\n")
        self.profile = self.repo / "RELEASE-TRAIN.md"
        # Pin the sources with --update from a profile whose ids are unknown.
        self.profile.write_text(profile_text("unknown", "unknown"))
        r = run(["RELEASE-TRAIN.md", "--update"], self.repo)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def tearDown(self):
        self.tmp.cleanup()

    def findings(self, *extra):
        r = run(["RELEASE-TRAIN.md", "--json", *extra], self.repo)
        return r.returncode, json.loads(r.stdout)["findings"]

    def test_pinned_profile_is_current(self):
        code, found = self.findings()
        self.assertEqual(code, 0, found)
        self.assertEqual(found, [])

    def test_update_pins_blob_ids_and_nothing_else(self):
        text = self.profile.read_text()
        self.assertNotIn("| unknown |", text)
        self.assertIn("- install like a user: apt install", text)
        self.assertIn("## Smoke contract", text)

    def test_changed_source_is_reported(self):
        (self.repo / ".github" / "workflows" / "release.yml").write_text(WORKFLOW + "  extra:\n")
        code, found = self.findings()
        self.assertEqual(code, 1)
        self.assertIn(
            {"check": "sources", "status": "CHANGED", "path": ".github/workflows/release.yml", "feeds": "Channels"},
            found,
        )

    def test_missing_source_and_path_are_reported(self):
        (self.repo / "packaging" / "build.sh").unlink()
        code, found = self.findings()
        self.assertEqual(code, 1)
        statuses = {(f["check"], f["status"], f.get("path")) for f in found}
        self.assertIn(("sources", "MISSING", "packaging/build.sh"), statuses)
        self.assertIn(("paths", "MISSING", "packaging/build.sh"), statuses)

    def test_tarball_internal_paths_are_not_repo_paths(self):
        text = self.profile.read_text().replace(
            "- install like a user: apt install",
            "- install like a user: copy `bin/demo` and `$T/lab.toml` then apt install",
        )
        self.profile.write_text(text)
        code, found = self.findings()
        self.assertEqual(code, 0, found)

    def test_arm_missing_required_bullet_is_refused(self):
        text = self.profile.read_text().replace("- cleanup: apt remove\n", "")
        self.profile.write_text(text)
        code, found = self.findings()
        self.assertEqual(code, 1)
        self.assertIn({"check": "channels", "status": "MISSING BULLET", "arm": "deb", "bullet": "cleanup"}, found)

    def test_unknown_workflow_job_is_reported(self):
        text = self.profile.read_text().replace("- workflow job: package\n", "- workflow job: package-macos\n")
        self.profile.write_text(text)
        code, found = self.findings()
        self.assertEqual(code, 1)
        self.assertTrue(any(f["status"] == "NO SUCH JOB" and f["job"] == "package-macos" for f in found), found)

    def test_job_matched_by_display_name(self):
        text = self.profile.read_text().replace("- workflow job: package\n", "- workflow job: package (windows x86_64)\n")
        self.profile.write_text(text)
        code, found = self.findings()
        self.assertEqual(code, 0, found)

    def test_missing_heading_is_reported(self):
        text = self.profile.read_text().replace("## Publish\n\n- gate: ask\n", "")
        self.profile.write_text(text)
        code, found = self.findings()
        self.assertEqual(code, 1)
        self.assertIn({"check": "headings", "status": "MISSING", "heading": "## Publish"}, found)

    def test_smoke_subcommand_checked_against_live_cli(self):
        cli = self.repo / "demo"
        cli.write_text("#!/bin/sh\nprintf 'Usage: demo <COMMAND>\\n\\nCommands:\\n  skill  list\\n  help   help\\n'\n")
        cli.chmod(0o755)
        code, found = self.findings("--cli", str(cli))
        self.assertEqual(code, 0, found)
        text = self.profile.read_text().replace("| S2 | `demo skill` |", "| S2 | `demo skills` |")
        self.profile.write_text(text)
        code, found = self.findings("--cli", str(cli))
        self.assertEqual(code, 1)
        self.assertTrue(any(f["status"] == "UNKNOWN SUBCOMMAND" and f["subcommand"] == "skills" for f in found), found)

    def test_missing_profile_is_a_precondition_failure(self):
        r = run(["nope.md"], self.repo)
        self.assertEqual(r.returncode, 3)


if __name__ == "__main__":
    unittest.main()
