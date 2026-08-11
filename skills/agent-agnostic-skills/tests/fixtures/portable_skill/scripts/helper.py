#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""SYNTHETIC TEST FIXTURE - the same helper, bound to stable layers.

Targets are found by argument name rather than tool name, so a tool this
fixture has never heard of is still classified correctly.
"""

import os

PATH_KEYS = {"file_path", "absolute_path", "path", "paths", "targetfile",
             "cwd", "searchdirectory"}
COMMAND_KEYS = {"command", "commandline", "cmd"}
CONTENT_KEYS = {"content", "codeedit", "new_string", "patch"}

CONFIG_DIRS = (".agents", ".agent", ".gemini", ".claude")


def project_dir(cwd_hint=None):
    explicit = os.environ.get("PORTABLE_SKILL_PROJECT_DIR")
    if explicit:
        return explicit
    if cwd_hint:
        return cwd_hint
    for var in ("GEMINI_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        if os.environ.get(var):
            return os.environ[var]
    return os.getcwd()


def policy_path(cwd_hint=None):
    root = project_dir(cwd_hint)
    for cfg in CONFIG_DIRS:
        cand = os.path.join(root, cfg, "policy.json")
        if os.path.isfile(cand):
            return cand
    raise FileNotFoundError(
        "no policy.json under any of: "
        + ", ".join(os.path.join(root, c) for c in CONFIG_DIRS))
