#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/session_audit.py.

Run:  python3 -m unittest discover -s skills/cleanroom-implementer/tests -v

test_shares_policy_with_the_hook is the one that matters most: the auditor
imports the hook's policy loader and matcher so enforcement and detection
cannot drift apart. If that import is ever severed, a policy edit would
silently protect one and not the other, and this test goes red.

The rest cover the record formats the auditor has to read: Antigravity
session logs (toolCall objects with PascalCase args, toolCalls[] entries),
task artifacts in a directory, a SQLite conversation store, and Claude Code
JSONL. Format is sniffed per file, so each shape needs its own case.
"""

import json
import os
import pathlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
AUDIT = HERE.parent / "scripts" / "session_audit.py"
HOOK = HERE.parent / "scripts" / "cleanroom_hook.py"
FIX = HERE / "fixtures"


def run_audit(*args):
    """Run session_audit.py in an isolated project dir; return (rc, output)."""
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ)
        env["CLEANROOM_PROJECT_DIR"] = tmp
        env.pop("CLEANROOM_POLICY", None)
        proc = subprocess.run(
            [sys.executable, str(AUDIT)] + [str(a) for a in args],
            capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout + proc.stderr


class TestSessionAudit(unittest.TestCase):

    def test_co_located_with_the_hook(self):
        """The import coupling requires both files in one directory."""
        self.assertTrue(HOOK.is_file(),
                        "session_audit.py imports cleanroom_hook.py from its "
                        "own directory; they must stay co-located")

    def test_dirty_session_is_flagged(self):
        rc, out = run_audit(FIX / "dirty_session.jsonl")
        self.assertEqual(rc, 1, out)
        self.assertIn("FINDINGS", out)
        self.assertIn("tool-target", out)
        self.assertIn("license-marker", out)
        self.assertIn("discard the session's diff wholesale", out)

    def test_clean_session_passes(self):
        rc, out = run_audit(FIX / "clean_session.jsonl")
        self.assertEqual(rc, 0, out)
        self.assertIn("verdict: clean", out)
        self.assertIn("0 finding(s)", out)

    def test_report_cites_markers_not_content(self):
        """Findings name the marker and count, never the fetched text."""
        rc, out = run_audit(FIX / "dirty_session.jsonl")
        self.assertEqual(rc, 1, out)
        self.assertIn("MODULE_LICENSE", out)
        for verbatim in ("widgetron_probe", "#include <linux/module.h>",
                         "EXPORT_SYMBOL_GPL("):
            self.assertNotIn(verbatim, out,
                             f"audit reproduced result content: {verbatim!r}")

    def test_emits_a_ledger_line(self):
        _, out = run_audit(FIX / "clean_session.jsonl")
        self.assertIn("ledger line:", out)

    def test_shares_policy_with_the_hook(self):
        """A pattern only in the custom policy must reach the auditor.

        acme-vendor-blob-sdk is absent from the built-in defaults, so a
        finding can only come from session_audit resolving the same policy
        file through the hook's loader.
        """
        rc, out = run_audit(FIX / "custom_policy_session.jsonl")
        self.assertEqual(rc, 0, out)
        rc, out = run_audit(FIX / "custom_policy_session.jsonl",
                            "--policy", FIX / "custom-policy.json")
        self.assertEqual(rc, 1, out)
        self.assertIn("acme-vendor-blob-sdk", out)

    def test_missing_transcript_is_error(self):
        rc, out = run_audit(HERE / "no-such-session.jsonl")
        self.assertEqual(rc, 2, out)


class TestAntigravityTranscripts(unittest.TestCase):
    """The session log named by transcriptPath on every hook event."""

    def test_dirty_session_is_flagged(self):
        rc, out = run_audit(FIX / "antigravity_dirty_session.jsonl")
        self.assertEqual(rc, 1, out)
        # PascalCase argument names, nested under toolCall.
        self.assertIn("view_file matched 'path:/linux/drivers/'", out)
        self.assertIn("run_command matched 'url:github.com/torvalds'", out)
        self.assertIn("search_web matched 'url:kernel.org'", out)

    def test_results_are_attributed_to_the_call(self):
        """A result must be correlated back to the tool that ran.

        Antigravity puts the result beside toolCall on the record rather
        than inside it; losing that would report every marker against '?'.
        """
        rc, out = run_audit(FIX / "antigravity_dirty_session.jsonl")
        self.assertEqual(rc, 1, out)
        self.assertIn("MODULE_LICENSE x1 in view_file result", out)

    def test_clean_session_passes(self):
        """Also pins the content exemption on the audit side.

        The fixture's CodeEdit names trusted-firmware-a, linux/drivers/,
        kernel.org and bootlin.com in a code comment, exactly as a real
        clean-room driver header does. Authored content is not a tool target.
        """
        rc, out = run_audit(FIX / "antigravity_clean_session.jsonl")
        self.assertEqual(rc, 0, out)
        self.assertIn("verdict: clean", out)


class TestAntigravityArtifacts(unittest.TestCase):
    """Plans and walkthroughs are records too - and in the IDE, where hooks
    may not fire, sometimes the only ones."""

    def test_artifact_directory_is_walked(self):
        rc, out = run_audit(FIX / "antigravity_artifacts")
        self.assertEqual(rc, 1, out)
        self.assertIn("walkthrough.md", out)
        self.assertIn("license-marker", out)
        self.assertNotIn("EXPORT_SYMBOL_GPL(", out,
                         "audit reproduced artifact content")

    def test_artifact_code_density_is_exempt(self):
        """A plan quoting the new driver is not evidence of contamination.

        implementation-plan.md is deliberately dense with Rust; only license
        markers may flag a text artifact.
        """
        rc, out = run_audit(FIX / "antigravity_artifacts" /
                            "implementation-plan.md")
        self.assertEqual(rc, 0, out)
        self.assertIn("0 finding(s)", out)

    def test_sqlite_conversation_store_is_audited(self):
        """Antigravity keeps conversations in SQLite, schema undocumented.

        Every text cell is treated as a candidate record: parsed as JSON when
        it parses, scanned as text when it does not.
        """
        with tempfile.TemporaryDirectory() as tmp:
            db = pathlib.Path(tmp) / "conversation.db"
            con = sqlite3.connect(db)
            con.execute("CREATE TABLE steps (id INTEGER, payload TEXT)")
            con.execute("INSERT INTO steps VALUES (1, ?)", [json.dumps(
                {"type": "gemini", "content": [{"functionCall": {
                    "id": "c1", "name": "run_command",
                    "args": {"command": "git clone "
                                        "https://github.com/torvalds/linux"}}}]})])
            con.execute("INSERT INTO steps VALUES (2, ?)",
                        ['note: upstream declares MODULE_LICENSE("GPL");'])
            con.commit()
            con.close()
            rc, out = run_audit(db)
        self.assertEqual(rc, 1, out)
        self.assertIn("(sqlite)", out)
        self.assertIn("run_command matched 'url:github.com/torvalds'", out)
        self.assertIn("MODULE_LICENSE", out)


if __name__ == "__main__":
    unittest.main()
