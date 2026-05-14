#!/usr/bin/env python3
# Copyright 2026 contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0

"""
_sibling.py — locate and import the cynthion-pcap-decode decode module.

All scripts in this skill import via:
    from _sibling import import_decode
    decode = import_decode()
"""

import sys
from pathlib import Path


def find_decode_scripts() -> Path:
    """Return the path containing decode.py, or raise ImportError."""
    here = Path(__file__).resolve().parent
    candidates = [
        # Standard ~/.claude/skills install
        Path.home() / ".claude" / "skills" / "cynthion-pcap-decode" / "scripts",
        # Sibling in the same skills tree (repo / development layout)
        here.parent.parent / "cynthion-pcap-decode" / "scripts",
    ]
    for p in candidates:
        if (p / "decode.py").exists():
            return p
    raise ImportError(
        "cynthion-pcap-decode skill not found.\n"
        "Install it alongside this skill so that decode.py is reachable at:\n"
        "  ~/.claude/skills/cynthion-pcap-decode/scripts/decode.py\n"
        "Get it from: skills/cynthion-pcap-decode/ in the public-skills repo."
    )


def import_decode():
    """Import and return the decode module from cynthion-pcap-decode."""
    path = find_decode_scripts()
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
    import decode  # noqa: PLC0415
    return decode
