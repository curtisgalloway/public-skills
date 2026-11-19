#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check that every skill's and agent's frontmatter parses and fits the limits.

A skill whose frontmatter is not valid YAML may load in one harness and be
skipped by another: fnirsi-dps-150 shipped with a plain-scalar description
containing ": ", which strict parsers reject. release-train shipped with a
1165-character description, over the 1024-character Agent Skills limit.

For every plugins/*/skills/*/SKILL.md and plugins/*/skills/*/agents/*.md this asserts:

  * the file opens with a '---' frontmatter block that parses as a YAML mapping
  * `name` and `description` are non-empty strings
  * a skill's `name` matches its directory, is at most 64 characters, and
    uses only lowercase letters, digits and hyphens
  * `description` is at most 1024 characters

Exit codes follow the dev-tools/cli-conventions contract:

  0  every file passes
  1  ran fine; found problems
  2  usage error
  3  missing precondition (PyYAML not installed)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MAX_NAME = 64
MAX_DESCRIPTION = 1024
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def frontmatter(text: str) -> str | None:
    """Return the YAML between the opening and closing '---' lines, or None."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[1:i])
    return None


def check_file(path: Path, yaml, *, is_skill: bool) -> list[str]:
    """Return the problems found in one SKILL.md or agent file."""
    block = frontmatter(path.read_text(encoding="utf-8"))
    if block is None:
        return [f"{path}: no '---' frontmatter block at the top of the file"]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        first = str(exc).splitlines()[0]
        return [f"{path}: frontmatter is not valid YAML ({first}); "
                "quote the value or use a '>-' block"]
    if not isinstance(data, dict):
        return [f"{path}: frontmatter is not a YAML mapping"]

    problems = []
    name, desc = data.get("name"), data.get("description")
    if not isinstance(name, str) or not name.strip():
        problems.append(f"{path}: missing or empty `name`")
    elif is_skill:
        if name != path.parent.name:
            problems.append(f"{path}: `name` {name!r} does not match its "
                            f"directory {path.parent.name!r}")
        if len(name) > MAX_NAME or not NAME_RE.match(name):
            problems.append(f"{path}: `name` must be at most {MAX_NAME} "
                            "lowercase letters, digits and hyphens")
    if not isinstance(desc, str) or not desc.strip():
        problems.append(f"{path}: missing or empty `description`")
    elif len(desc) > MAX_DESCRIPTION:
        problems.append(f"{path}: `description` is {len(desc)} characters, "
                        f"over the {MAX_DESCRIPTION} limit")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path,
                        default=Path(__file__).resolve().parent.parent,
                        help="repository root (default: this script's repo)")
    args = parser.parse_args(argv)
    try:
        import yaml
    except ImportError:
        print("error: PyYAML is required (pip install pyyaml)", file=sys.stderr)
        return 3

    skills = sorted(args.root.glob("plugins/*/skills/*/SKILL.md"))
    agents = sorted(args.root.glob("plugins/*/skills/*/agents/*.md"))
    problems = []
    for path in skills:
        problems += check_file(path, yaml, is_skill=True)
    for path in agents:
        problems += check_file(path, yaml, is_skill=False)
    for problem in problems:
        print(problem)
    if problems:
        return 1
    print(f"OK: {len(skills)} skills and {len(agents)} agents, frontmatter valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
