#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check that every skill on disk is registered everywhere it needs to be.

Adding plugins/<theme>/skills/<name>/ means editing more than one file, and
nothing used to catch a miss -- cli-conventions shipped registered in its
plugin README and plugin.json but absent from the root README table.

This walks the skills that actually exist and asserts each one appears in:

  * the Themes table in README.md (the row for its plugin)
  * plugins/<theme>/README.md

and that each plugin directory has an entry in .claude-plugin/marketplace.json
and is covered by the bundle entry's skills[] list.

Exit codes follow the dev-tools/cli-conventions contract:

  0  everything registered
  1  ran fine; found unregistered skills
  2  usage error
  3  missing precondition (expected file not found)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ROOT_README = REPO / "README.md"
MARKETPLACE = REPO / ".claude-plugin" / "marketplace.json"
BUNDLE = "public-skills"


def discover_skills() -> dict[str, list[str]]:
    """Map plugin name -> sorted skill names, from the directory tree."""
    found: dict[str, list[str]] = {}
    for skill_md in sorted((REPO / "plugins").glob("*/skills/*/SKILL.md")):
        plugin = skill_md.parents[2].name
        found.setdefault(plugin, []).append(skill_md.parent.name)
    return {k: sorted(v) for k, v in found.items()}


def root_table_cell(plugin: str) -> str | None:
    """The Skills column of the Themes-table row for `plugin`, or None."""
    for line in ROOT_README.read_text().splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 3 and f"`{plugin}`" in cells[0]:
            return cells[-1]
    return None


def plugin_readme_text(plugin: str) -> str | None:
    """The full text of plugins/<plugin>/README.md, or None if absent.

    Deliberately the whole file rather than a "## Skills" section: only
    dev-tools uses that heading. The other three organize by narrative
    section ("The Cynthion pipeline", "Board experts"), so there is no
    smaller region that reliably contains the list.
    """
    readme = REPO / "plugins" / plugin / "README.md"
    return readme.read_text() if readme.exists() else None


def skill_is_registered(name: str, text: str) -> bool:
    """Is skill `name` listed in `text`?

    The rule is strict: the name must appear backtick-quoted, exactly.

    A bare `name in text` false-passes whenever the name also occurs in the
    surrounding prose, and the plugin-README region is the whole file. Five of
    the 27 skills are in that state today -- teach, jj, os-investigator,
    cleanroom-implementer, agent-agnostic-skills -- so delisting any of them
    would go undetected by a loose check. Requiring the backticks also kills
    prefix bleed for free: the closing backtick stops `cynthion-capture` from
    satisfying a hypothetical `cynthion-capture-foo`.

    The cost is a false failure the day someone writes a skill name unquoted
    in a heading. That is the intended trade: this runs before a commit, the
    message names the skill and the file, and the fix is two backticks. All
    27 skills in the tree already comply.
    """
    return f"`{name}`" in text


def check_marketplace(plugins: list[str]) -> list[str]:
    """Structural marketplace checks.

    Deliberately NOT a name check. The `description` fields are curated prose
    ("USB device profiles", not `usb-device-profile`); requiring exact names
    there flagged 17 of 27 skills on a clean tree, which is noise that buries
    anything real. What IS mechanical: every plugin directory needs an entry,
    and the bundle must cover its skills dir.
    """
    failures: list[str] = []
    data = json.loads(MARKETPLACE.read_text())
    entries = {p["name"]: p for p in data.get("plugins", [])}
    bundle_dirs = set(entries.get(BUNDLE, {}).get("skills", []))

    for plugin in plugins:
        if plugin not in entries:
            failures.append(f"{plugin}: no entry in {MARKETPLACE.name}")
            continue
        want = f"./plugins/{plugin}/skills"
        if bundle_dirs and want not in bundle_dirs:
            failures.append(f"{plugin}: {want} missing from the {BUNDLE} bundle skills[]")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--json", action="store_true", help="emit machine-readable results on stdout"
    )
    args = parser.parse_args()

    for required in (ROOT_README, MARKETPLACE):
        if not required.exists():
            print(f"missing precondition: {required} not found", file=sys.stderr)
            return 3

    skills = discover_skills()
    if not skills:
        print("missing precondition: no skills found under plugins/", file=sys.stderr)
        return 3

    failures: list[str] = []
    for plugin, names in skills.items():
        cell = root_table_cell(plugin)
        readme = plugin_readme_text(plugin)
        if cell is None:
            failures.append(f"{plugin}: no row in the README.md Themes table")
        if readme is None:
            failures.append(f"{plugin}: no plugins/{plugin}/README.md")
        for name in names:
            where = f"{plugin}/{name}"
            if cell is not None and not skill_is_registered(name, cell):
                failures.append(f"{where}: missing from the README.md Themes table")
            if readme is not None and not skill_is_registered(name, readme):
                failures.append(f"{where}: missing from plugins/{plugin}/README.md")

    failures += check_marketplace(sorted(skills))
    total = sum(len(v) for v in skills.values())

    if args.json:
        json.dump({"skills": total, "failures": failures}, sys.stdout, indent=2)
        sys.stdout.write("\n")
    elif failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        print(f"FAIL: {len(failures)} registration problem(s)", file=sys.stderr)
    else:
        print(f"OK: {total} skills registered")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
