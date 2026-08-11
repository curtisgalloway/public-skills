#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
Tests for scripts/cleanroom_hook.py.

Run:  python3 -m unittest discover -s skills/cleanroom-implementer/tests -v

Each case drives the hook the way Antigravity does: a PreToolUse event on
stdin with the call nested under `toolCall` and the workspace in
`workspacePaths`. Flat `tool_name`/`tool_input` payloads are exercised too,
because the same script is meant to keep working on other harnesses.

Four invariants here are deliberate design decisions that a well-meaning
future edit would break:

  - allow is ALWAYS explicit (test_allow_is_explicit, and the malformed-input
    case). Antigravity does not accept empty stdout as permission to proceed,
    so a silent hook can wedge every tool call in the session.
  - written content is not scanned (test_edit_content_is_not_scanned,
    test_code_edit_content_is_not_scanned).
  - malformed input allows rather than blocks.
  - a deny is emitted in every dialect at once
    (test_deny_speaks_every_harness_dialect).
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
ALLOW = {"decision": "allow"}


class HookCase(unittest.TestCase):

    def fire(self, tool, args, role=None, policy=None, shape="antigravity",
             project_var="CLEANROOM_PROJECT_DIR", extra_env=None, setup=None,
             event_extra=None):
        """Send one PreToolUse event; return (rc, stderr, log_entries).

        stdout and the temp workspace land on self for the cases that assert
        on them.
        """
        with tempfile.TemporaryDirectory() as tmp:
            if setup is not None:
                setup(pathlib.Path(tmp))
            env = dict(os.environ)
            for var in ("CLEANROOM_PROJECT_DIR", "GEMINI_PROJECT_DIR",
                        "CLAUDE_PROJECT_DIR", "CLEANROOM_ROLE",
                        "CLEANROOM_POLICY", "CLEANROOM_BLOCK_EXIT_CODE"):
                env.pop(var, None)
            if project_var:
                env[project_var] = tmp
            if role is not None:
                env["CLEANROOM_ROLE"] = role
            if policy is not None:
                env["CLEANROOM_POLICY"] = str(policy)
            env.update(extra_env or {})

            if shape == "antigravity":
                event = {"toolCall": {"name": tool, "args": args},
                         "stepIdx": 4,
                         "conversationId": "agy-test-session",
                         "workspacePaths": [tmp]}
            else:
                event = {"tool_name": tool, "tool_input": args,
                         "session_id": "test-session"}
            event.update(event_extra or {})

            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input=json.dumps(event),
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
        rc, err, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)
        self.assertIn("BLOCKED", err)
        self.assertIn("spec-gap", err)
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["action"], "blocked")

    def test_blocked_url_via_url_reader(self):
        rc, err, log = self.fire(
            "read_url_content",
            {"Url": "https://git.kernel.org/pub/scm/linux/x.c"})
        self.assertEqual(rc, 2, err)
        self.assertEqual(log[0]["action"], "blocked")

    def test_search_query_is_checked_against_urls(self):
        rc, err, _ = self.fire(
            "search_web", {"query": "widgetron driver site:kernel.org"})
        self.assertEqual(rc, 2, err)

    def test_unknown_mcp_tool_is_checked_for_urls(self):
        """The shipped hooks.json wires matcher '.*' precisely for this."""
        rc, err, _ = self.fire(
            "mcp__fetcher__get",
            {"target": "https://kernel.org/doc/widgetron.html"})
        self.assertEqual(rc, 2, err)


class TestToolVocabularies(HookCase):
    """Nothing keys off a tool-name table; argument names carry the load.

    Antigravity names its arguments in PascalCase (CommandLine, TargetFile)
    and has renamed tools between releases, so these cases are the guard
    against someone reintroducing a per-tool lookup.
    """

    def test_run_command_pascalcase_commandline(self):
        rc, err, log = self.fire("run_command", {
            "CommandLine": "git clone https://github.com/torvalds/linux",
            "Cwd": "/home/dev/src/widgetron-port",
            "WaitMsBeforeAsync": 0})
        self.assertEqual(rc, 2, err)
        self.assertEqual(log[0]["tool"], "run_command")

    def test_run_command_cwd_into_a_checkout(self):
        rc, err, _ = self.fire("run_command", {
            "CommandLine": "rg widgetron_reset .",
            "Cwd": "/home/dev/src/linux/drivers/net"})
        self.assertEqual(rc, 2, err)

    def test_view_file_target_file(self):
        rc, err, _ = self.fire("view_file", {"TargetFile": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)

    def test_grep_search_search_directory(self):
        rc, err, _ = self.fire("grep_search", {
            "Query": "widgetron_reset",
            "SearchDirectory": "/home/dev/src/u-boot/drivers"})
        self.assertEqual(rc, 2, err)

    def test_read_file_snake_case_still_works(self):
        rc, err, _ = self.fire("read_file", {"file_path": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)

    def test_path_list_is_checked(self):
        rc, err, _ = self.fire("read_many_files", {
            "paths": ["docs/widgetron-spec.md", BLOCKED_PATH]})
        self.assertEqual(rc, 2, err)

    def test_flat_payload_shape_still_works(self):
        """Other harnesses send tool_name/tool_input at the top level."""
        rc, err, _ = self.fire("Read", {"file_path": BLOCKED_PATH},
                               shape="flat")
        self.assertEqual(rc, 2, err)


class TestAllowing(HookCase):

    def test_allow_is_explicit(self):
        """Antigravity rejects empty stdout; silence would wedge the session."""
        rc, err, log = self.fire("view_file",
                                 {"TargetFile": "docs/widgetron-spec.md"})
        self.assertEqual(rc, 0, err)
        self.assertEqual(err, "")
        self.assertEqual(json.loads(self.stdout), ALLOW)
        self.assertEqual(log, [], "benign calls must not be logged")

    def test_investigator_role_allows_and_logs(self):
        rc, err, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH},
                                 role="investigator")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(self.stdout), ALLOW)
        self.assertEqual(len(log), 1, "authorized reads must still be logged")
        self.assertEqual(log[0]["action"], "allowed-role")
        self.assertEqual(log[0]["role"], "investigator")

    def test_verifier_role_allows(self):
        rc, err, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH},
                                 role="verifier")
        self.assertEqual(rc, 0, err)
        self.assertEqual(log[0]["action"], "allowed-role")

    def test_unrecognised_role_still_blocks(self):
        rc, err, _ = self.fire("view_file", {"TargetFile": BLOCKED_PATH},
                               role="implementer")
        self.assertEqual(rc, 2, err)

    def test_edit_content_is_not_scanned(self):
        """Deliberate: a comment naming a blocked project must not block.

        Content-level leaks belong to session_audit and the output scan.
        Scanning written content here would false-positive on prose.
        """
        rc, err, log = self.fire("edit_file", {
            "TargetFile": "src/devices/widgetron/driver.rs",
            "old_string": "// TODO",
            "new_string": "// Ported clean-room; do not consult "
                          "trusted-firmware-a or linux/drivers/ for this.",
        })
        self.assertEqual(rc, 0, err)
        self.assertEqual(log, [])

    def test_code_edit_content_is_not_scanned(self):
        """Same exemption, and it matters more here.

        Unrecognised argument keys are scanned for URLs, so Antigravity's
        CodeEdit has to be exempt by name or every citation in a doc comment
        would block the write that adds it.
        """
        rc, err, log = self.fire("write_file", {
            "TargetFile": "docs/references/README.md",
            "CodeEdit": "Mirror list (pre-fetched, do not fetch): "
                        "https://kernel.org/doc/, https://bootlin.com/",
        })
        self.assertEqual(rc, 0, err)
        self.assertEqual(log, [])

    def test_malformed_input_allows_explicitly(self):
        """Bad input must not wedge the session - in either direction.

        Exit 0 alone is not enough: Antigravity needs the decision object,
        so the allow payload has to be printed even on the error path.
        """
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ)
            env["CLEANROOM_PROJECT_DIR"] = tmp
            proc = subprocess.run([sys.executable, str(HOOK)],
                                  input="this is not json",
                                  capture_output=True, text=True, env=env)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout), ALLOW)


class TestDenyContract(HookCase):
    """One script has to satisfy more than one harness's block protocol."""

    def test_deny_speaks_every_harness_dialect(self):
        rc, err, _ = self.fire("view_file", {"TargetFile": BLOCKED_PATH})
        self.assertEqual(rc, 2, err)
        payload = json.loads(self.stdout)
        # Antigravity reads the decision object.
        self.assertEqual(payload["decision"], "deny")
        self.assertIn("spec-gap", payload["reason"])
        self.assertTrue(payload["continue"],
                        "block the call, not the whole session")
        # Claude Code reads hookSpecificOutput.
        self.assertEqual(
            payload["hookSpecificOutput"]["permissionDecision"], "deny")
        # A non-zero exit is a block everywhere, and fails closed.
        self.assertIn("BLOCKED", err)

    def test_block_exit_code_is_overridable(self):
        """For a build that objects to a non-zero exit from a hook."""
        rc, _, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH},
                               extra_env={"CLEANROOM_BLOCK_EXIT_CODE": "0"})
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(self.stdout)["decision"], "deny")
        self.assertEqual(log[0]["action"], "blocked",
                         "an overridden exit code is still a block")


class TestEventPlumbing(HookCase):

    def test_workspace_paths_locate_the_project(self):
        """No project-dir variable exists in Antigravity; the event carries it."""
        rc, err, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH},
                                 project_var=None)
        self.assertEqual(rc, 2, err)
        self.assertEqual(len(log), 1,
                         "log must land under workspacePaths[0]")

    def test_log_records_where_to_audit(self):
        """The pre-merge audit needs the session's own paths, not a guess."""
        rc, err, log = self.fire(
            "view_file", {"TargetFile": BLOCKED_PATH},
            event_extra={"transcriptPath": "/tmp/agy/session.jsonl",
                         "artifactDirectoryPath": "/tmp/agy/brain/abc"})
        self.assertEqual(rc, 2, err)
        self.assertEqual(log[0]["transcript"], "/tmp/agy/session.jsonl")
        self.assertEqual(log[0]["artifacts"], "/tmp/agy/brain/abc")

    def test_conversation_id_is_recorded(self):
        _, _, log = self.fire("view_file", {"TargetFile": BLOCKED_PATH})
        self.assertEqual(log[0]["session_id"], "agy-test-session")


class TestPolicyPlumbing(HookCase):

    def test_custom_policy_file_is_honoured(self):
        path = "/home/dev/src/acme-vendor-blob-sdk/hal/widgetron.c"
        rc, _, _ = self.fire("view_file", {"TargetFile": path})
        self.assertEqual(rc, 0, "not blocked by the built-in defaults")
        rc, err, log = self.fire("view_file", {"TargetFile": path},
                                 policy=FIX / "custom-policy.json")
        self.assertEqual(rc, 2, err)
        self.assertIn("acme-vendor-blob-sdk", log[0]["pattern"])

    def test_policy_is_found_in_the_workspace_agents_dir(self):
        """<workspace>/.agents/cleanroom-policy.json, no env var needed."""
        def setup(root):
            cfg = root / ".agents"
            cfg.mkdir()
            (cfg / "cleanroom-policy.json").write_text(json.dumps({
                "checkout_roots": [],
                "blocked_path_patterns": ["acme-vendor-blob-sdk"],
                "blocked_url_patterns": [],
            }))
        rc, err, log = self.fire(
            "view_file",
            {"TargetFile": "/home/dev/src/acme-vendor-blob-sdk/hal/w.c"},
            project_var=None, setup=setup)
        self.assertEqual(rc, 2, err)
        self.assertIn("acme-vendor-blob-sdk", log[0]["pattern"])

    def test_legacy_project_dir_variables_still_work(self):
        for var in ("GEMINI_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
            with self.subTest(var=var):
                rc, err, log = self.fire(
                    "Read", {"file_path": BLOCKED_PATH}, shape="flat",
                    project_var=var)
                self.assertEqual(rc, 2, err)
                self.assertEqual(len(log), 1)


if __name__ == "__main__":
    unittest.main()
