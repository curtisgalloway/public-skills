#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0

"""
_sibling.py — locate and import the cynthion-pcap-decode decode module.

All scripts in this skill that need decode.py import via:
    from _sibling import import_decode
    decode = import_decode()

Skills roots differ per agent — and per release — so nothing here is
hardcoded to one harness. Resolution order:

  1. $CYNTHION_PCAP_DECODE_SCRIPTS, if you want to point at it outright.
  2. $PUBLIC_SKILLS_REPO/skills/ (the variable this repo's manifest.json
     already uses).
  3. A sibling in the same skills tree — the repo layout, and what any
     harness that installs whole skill trees together produces. This is the
     case that works without configuration; prefer it.
  4. Known skills roots under $HOME and the current workspace -
     Antigravity first, then others - plus Antigravity plugin directories,
     which are globbed because the plugin name is the user's.
"""

import os
import sys
from pathlib import Path

SKILL = "cynthion-pcap-decode"
MODULE = "decode.py"

# Skills roots, relative to $HOME or to the workspace. Kept in one list so a
# new harness is one line, not a new code path.
HOME_SKILL_ROOTS = (
    ".gemini/antigravity/skills",     # Antigravity, user-level
    ".agents/skills",                 # cross-tool convention
    ".gemini/skills",                 # legacy Gemini CLI layout
    ".claude/skills",                 # Claude Code, user-level
)
WORKSPACE_SKILL_ROOTS = (
    ".agents/skills",                 # Antigravity workspace
    ".gemini/skills",                 # legacy Gemini CLI layout
    ".claude/skills",
    "skills",                         # a plain checkout of a skills repo
)
# Antigravity ships skills inside plugins; the plugin directory is the user's.
PLUGIN_GLOBS = (
    ".gemini/antigravity-cli/plugins/*/skills",
    ".gemini/antigravity/plugins/*/skills",
    ".gemini/extensions/*/skills",
)


def _candidates():
    here = Path(__file__).resolve().parent

    direct = os.environ.get("CYNTHION_PCAP_DECODE_SCRIPTS")
    if direct:
        yield Path(direct).expanduser()

    repo = os.environ.get("PUBLIC_SKILLS_REPO")
    if repo:
        yield Path(repo).expanduser() / "skills" / SKILL / "scripts"

    # Sibling in the same skills tree (repo / development layout, and any
    # harness that installs the tree wholesale).
    yield here.parent.parent / SKILL / "scripts"

    home = Path.home()
    for root in HOME_SKILL_ROOTS:
        yield home / root / SKILL / "scripts"
    for pattern in PLUGIN_GLOBS:
        for match in sorted(home.glob(pattern)):
            yield match / SKILL / "scripts"

    cwd = Path.cwd()
    for root in WORKSPACE_SKILL_ROOTS:
        yield cwd / root / SKILL / "scripts"


def find_decode_scripts() -> Path:
    """Return the path containing decode.py, or raise ImportError."""
    for path in _candidates():
        if (path / MODULE).exists():
            return path
    raise ImportError(
        f"{SKILL} skill not found.\n"
        "Install it alongside this skill so the two sit in one skills tree — "
        f"then {MODULE} is found with no configuration. Searched the sibling "
        "path plus the Antigravity, cross-tool and Claude Code skills roots "
        "under $HOME and this workspace.\n"
        "To point at it directly, set one of:\n"
        f"  CYNTHION_PCAP_DECODE_SCRIPTS=<dir containing {MODULE}>\n"
        "  PUBLIC_SKILLS_REPO=<clone of the public-skills repo>\n"
        f"Get it from: skills/{SKILL}/ in the public-skills repo."
    )


def import_decode():
    """Import and return the decode module from cynthion-pcap-decode."""
    path = find_decode_scripts()
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    import decode  # noqa: PLC0415
    return decode
