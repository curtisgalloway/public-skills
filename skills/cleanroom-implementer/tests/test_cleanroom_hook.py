#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/cleanroom_hook.py.

Run:  python3 -m unittest discover -s skills/cleanroom-implementer/tests -v

Each case drives the hook the way a harness does: one pre-tool-use event on
stdin (Gemini CLI's BeforeTool, Antigravity's PreToolUse and Claude Code's
PreToolUse all deliver tool_name + tool_input), exit 0 to allow or 2 to
block. The project dir is pointed at a temp dir per test so the hook's log
never touches a real project.

Three invariants here are deliberate design decisions that a well-meaning
future edit would break: content is not scanned (test_edit_content_is_not_
scanned, test_gemini_write_file_content_is_not_scanned), malformed input
allows rather than blocks (test_malformed_input_allows), and a deny is
emitted in all three harness dialects at once (test_deny_speaks_every_
harness_dialect).
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

    def fire(self, tool, tool_input, role=None, policy=None,
             project_var="CLEANROOM_PROJECT_DIR", extra_env=None, setup=None):
        """Send one pre-tool-use event; return (rc, stderr, log_entries).

        stdout and the temp project dir land on self for the cases that
        assert on them.
        """
        with tempfile.TemporaryDirectory() as tmp:
            if setup is not None:
                setup(pathlib.Path(tmp))
            env = dict(os.environ)
            for var in ("CLEANROOM_PROJECT_DIR", "GEMINI_PROJECT_DIR",
                        "CLAUDE_PROJECT_DIR", "CLEANROOM_ROLE",
                        "CLEANROOM_POLICY", "CLEANROOM_BLOCK_EXIT_CODE"):
                env.pop(var, None)
            env[project_var] = tmp
            if role is not None:
                env["CLEANROOM_ROLE"] = role
            if policy is not None:
                env["CLEANROOM_POLICY"] = str(policy)
            env.update(extra_env or {})
            event = json.dumps({"tool_name": tool, "tool_input": tool_input,
                                "session_id": "test-session"})
            proc = subprocess.run([sys.executable, str(HOOK)], input=event,
                                  capture_output=True, text=True, env=env)
            self.stdout = proc.stdout
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
        """The shipped fragments wire matcher '.*' precisely for this."""
        rc, err, _ = self.fire(
            "mcp__fetcher__get",
            {"target": "https://kernel.org/doc/widgetron.html"})
        self.assertEqual(rc, 2, err)


class TestGeminiAndAntigravityTools(HookCase):
    """Tool vocabularies differ per harness; argument names carry the load.

    Nothing in the hook keys off a tool-name table, so these cases are the
    guard against someone reintroducing one.
    """

    def test_gemini_read_file_is_checked(self):
        rc, err, log = self.fire("read_file", {"file_path": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)
        self.assertEqual(log[0]["tool"], "read_file")

    def test_gemini_read_file_absolute_path_arg(self):
        rc, err, _ = self.fire("read_file", {"absolute_path": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)

    def test_gemini_grep_search_path_is_checked(self):
        rc, err, _ = self.fire(
            "grep_search", {"pattern": "widgetron_reset",
                            "path": "/home/dev/src/linux/drivers/net"})
        self.assertEqual(rc, 2, err)

    def test_gemini_read_many_files_list_is_checked(self):
        rc, err, _ = self.fire(
            "read_many_files", {"paths": ["docs/widgetron-spec.md",
                                          BLOCKED_PATH]})
        self.assertEqual(rc, 2, err)

    def test_gemini_web_fetch_prompt_carries_the_url(self):
        """web_fetch takes a prompt, not a url - the URL is embedded in it."""
        rc, err, _ = self.fire("web_fetch", {
            "prompt": "Summarise the reset ordering at "
                      "https://lore.kernel.org/all/widgetron.patch"})
        self.assertEqual(rc, 2, err)

    def test_gemini_run_shell_command_is_checked(self):
        rc, err, _ = self.fire(
            "run_shell_command",
            {"command": "rg widgetron ~/src/u-boot/drivers"})
        self.assertEqual(rc, 2, err)

    def test_antigravity_run_command_is_checked(self):
        rc, err, _ = self.fire(
            "run_command",
            {"command": "curl -O https://source.denx.de/u-boot/u-boot.git"})
        self.assertEqual(rc, 2, err)

    def test_antigravity_view_file_target_file_arg(self):
        rc, err, _ = self.fire("view_file", {"target_file": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)


class TestAllowing(HookCase):

    def test_benign_path_is_silent(self):
        rc, err, log = self.fire(
            "Read", {"file_path": "docs/widgetron-spec.md"})
        self.assertEqual(rc, 0, err)
        self.assertEqual(err, "")
        self.assertEqual(self.stdout, "", "allow must emit no directives")
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

    def test_gemini_write_file_content_is_not_scanned(self):
        """Same exemption, and it matters more here.

        Unrecognised argument keys are scanned for URLs, so `content` has to
        be exempt by name or every citation in a doc comment would block the
        write that adds it.
        """
        rc, err, log = self.fire("write_file", {
            "file_path": "docs/references/README.md",
            "content": "Datasheet mirror list (do not fetch): "
                       "https://kernel.org/doc/, https://bootlin.com/",
        })
        self.assertEqual(rc, 0, err)
        self.assertEqual(log, [])

    def test_malformed_input_allows(self):
        """The hook must never break a session on bad input."""
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["CLEANROOM_PROJECT_DIR"] = tmp
            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input="this is not json",
                                  capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)


class TestDenyContract(HookCase):
    """One script has to satisfy three harnesses' block protocols."""

    def test_deny_speaks_every_harness_dialect(self):
        rc, err, _ = self.fire("read_file", {"file_path": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)
        payload = json.loads(self.stdout)
        # Gemini CLI and Antigravity read the decision object.
        self.assertEqual(payload["decision"], "deny")
        self.assertIn("spec-gap", payload["reason"])
        self.assertTrue(payload["continue"],
                        "block the call, not the whole session")
        # Claude Code reads hookSpecificOutput.
        self.assertEqual(
            payload["hookSpecificOutput"]["permissionDecision"], "deny")
        # Every harness treats exit 2 + stderr as a hard block.
        self.assertIn("BLOCKED", err)

    def test_block_exit_code_is_overridable(self):
        """For a harness that honours only the stdout object."""
        rc, _, log = self.fire("read_file", {"file_path": BLOCKED_PATH},
                               extra_env={"CLEANROOM_BLOCK_EXIT_CODE": "0"})
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.stdout)["decision"], "deny")
        self.assertEqual(log[0]["action"], "blocked",
                         "an overridden exit code is still a block")


class TestPolicyPlumbing(HookCase):

    def test_custom_policy_file_is_honoured(self):
        path = "/home/dev/src/acme-vendor-blob-sdk/hal/widgetron.c"
        rc, _, _ = self.fire("Read", {"file_path": path})
        self.assertEqual(rc, 0, "not blocked by the built-in defaults")
        rc, err, log = self.fire("Read", {"file_path": path},
                                 policy=FIX / "custom-policy.json")
        self.assertEqual(rc, 2, err)
        self.assertIn("acme-vendor-blob-sdk", log[0]["pattern"])

    def test_gemini_project_dir_is_honoured(self):
        """$GEMINI_PROJECT_DIR is what Gemini CLI exports to hooks."""
        rc, err, log = self.fire("read_file", {"file_path": BLOCKED_PATH},
                                 project_var="GEMINI_PROJECT_DIR")
        self.assertEqual(rc, 2, err)
        self.assertEqual(len(log), 1, "log must land under the project dir")

    def test_claude_project_dir_still_works(self):
        rc, err, log = self.fire("Read", {"file_path": BLOCKED_PATH},
                                 project_var="CLAUDE_PROJECT_DIR")
        self.assertEqual(rc, 2, err)
        self.assertEqual(len(log), 1)

    def test_policy_is_found_in_the_gemini_config_dir(self):
        """<project>/.gemini/cleanroom-policy.json, no env var needed."""
        def setup(root):
            cfg = root / ".gemini"
            cfg.mkdir()
            (cfg / "cleanroom-policy.json").write_text(json.dumps({
                "checkout_roots": [],
                "blocked_path_patterns": ["acme-vendor-blob-sdk"],
                "blocked_url_patterns": [],
            }))
        rc, err, log = self.fire(
            "read_file",
            {"file_path": "/home/dev/src/acme-vendor-blob-sdk/hal/w.c"},
            setup=setup)
        self.assertEqual(rc, 2, err)
        self.assertIn("acme-vendor-blob-sdk", log[0]["pattern"])

    def test_policy_is_found_in_the_antigravity_config_dir(self):
        """<workspace>/.agents/cleanroom-policy.json."""
        def setup(root):
            cfg = root / ".agents"
            cfg.mkdir()
            (cfg / "cleanroom-policy.json").write_text(json.dumps({
                "checkout_roots": [],
                "blocked_path_patterns": ["acme-vendor-blob-sdk"],
                "blocked_url_patterns": [],
            }))
        rc, err, _ = self.fire(
            "view_file",
            {"target_file": "/home/dev/src/acme-vendor-blob-sdk/hal/w.c"},
            setup=setup)
        self.assertEqual(rc, 2, err)


if __name__ == "__main__":
    unittest.main()
