#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""SYNTHETIC TEST FIXTURE - one harness assumed at every turn."""

import os

PATH_FIELDS = {
    "Read": "file_path",
    "Edit": "file_path",
    "Write": "file_path",
    "Grep": "path",
    "Bash": "command",
    "WebFetch": "url",
}


def project_dir():
    return os.environ["CLAUDE_PROJECT_DIR"]


def policy_path():
    return os.path.join(project_dir(), ".claude", "policy.json")
