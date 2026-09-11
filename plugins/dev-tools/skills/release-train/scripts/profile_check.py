#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check a repo's RELEASE-TRAIN.md profile against the repo it describes.

A release-train profile is prose an agent executes, and prose drifts: the
helper list grows, a workflow job is renamed, a packaging script moves. This
script turns "is the profile still true?" into a mechanical answer, so the
train can refuse to run on a stale profile instead of shipping from one.

Checks, in order:

  sources   every row of the `## Sources` table (path | blob | feeds) still
            hashes to the recorded git blob id. A changed source means the
            section it feeds needs re-reading; a missing one means the fact
            is gone.
  paths     every backtick-quoted repo path in the profile exists. Only
            tokens whose first segment is a directory at the repo root (or a
            file at the root) are treated as repo paths, so `bin/paniolo`
            inside a tarball or `$T/lab.toml` is not a false alarm.
  headings  the fixed headings the skill reads are all present.
  channels  every `### <arm>` under `## Channels` carries the bullets the
            arms are executed from, and its `workflow job:` names a job that
            exists in the release workflow.
  smoke     with --cli, the first word after the CLI name in each smoke
            row's first command is a subcommand the live CLI lists in
            --help. Without --cli this check is reported as skipped.

`--update` rewrites the Sources blob ids and the "Derived from commit" line
to the current tree, for use after a human has re-read the sections the
changed sources feed. It never touches any other line.

Exit codes follow the cli-conventions contract:

  0  profile is current
  1  ran fine; found drift or a malformed profile (details on stdout)
  2  usage error
  3  missing precondition (profile or repo not found)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys

REQUIRED_HEADINGS = [
    "## Project",
    "## Hosts",
    "## Smoke contract",
    "## Channels",
    "## Archaeology",
    "## Publish",
    "## Sources",
]
REQUIRED_ARM_BULLETS = ["kind", "artifact", "build", "install like a user", "smoke", "cleanup"]
SOURCE_ROW = re.compile(r"^\|\s*`?([^`|]+?)`?\s*\|\s*([0-9a-f]{7,40}|unknown|-)\s*\|\s*(.*?)\s*\|\s*$")
BACKTICK = re.compile(r"`([^`\n]+)`")
ARM_HEADING = re.compile(r"^### (.+?)\s*$")
BULLET = re.compile(r"^\s*-\s+([a-z][a-z ]+?):\s*(.*)$")
DERIVED = re.compile(r"^(Derived from commit )([0-9a-f]{7,40}|unknown)(.*)$")


def blob_id(path: pathlib.Path) -> str:
    """The git blob id of a file, computed without git."""
    data = path.read_bytes()
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def head_commit(repo: pathlib.Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip() or "unknown"
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def sections(lines: list[str]) -> dict[str, tuple[int, int]]:
    """Map each `## Heading` to its (start, end) line range."""
    found: dict[str, tuple[int, int]] = {}
    starts = [(i, l.rstrip()) for i, l in enumerate(lines) if l.startswith("## ")]
    for n, (i, heading) in enumerate(starts):
        end = starts[n + 1][0] if n + 1 < len(starts) else len(lines)
        found[heading] = (i, end)
    return found


def check_sources(lines, secs, repo, findings, update):
    rng = secs.get("## Sources")
    if rng is None:
        return
    for i in range(rng[0], rng[1]):
        m = SOURCE_ROW.match(lines[i])
        if not m or m.group(1).lower() in ("path", "---", ":--"):
            continue
        rel, recorded, feeds = m.group(1).strip(), m.group(2), m.group(3)
        path = repo / rel
        if not path.is_file():
            findings.append({"check": "sources", "status": "MISSING", "path": rel, "feeds": feeds})
            continue
        current = blob_id(path)
        if recorded in ("unknown", "-"):
            status = "UNRECORDED"
        elif current.startswith(recorded):
            status = "ok"
        else:
            status = "CHANGED"
        if status != "ok":
            findings.append({"check": "sources", "status": status, "path": rel, "feeds": feeds})
        if update:
            lines[i] = f"| `{rel}` | {current[:12]} | {feeds} |\n"


def check_paths(lines, repo, findings):
    roots = {p.name for p in repo.iterdir()}
    seen = set()
    for i, line in enumerate(lines):
        for tok in BACKTICK.findall(line):
            if any(c in tok for c in " $<>*|{}") or tok.startswith(("-", "http", "/", "~")):
                continue
            first = tok.split("/")[0]
            if first not in roots:
                continue
            if tok in seen:
                continue
            seen.add(tok)
            if not (repo / tok).exists():
                findings.append({"check": "paths", "status": "MISSING", "path": tok, "line": i + 1})


def check_headings(lines, findings):
    present = {l.rstrip() for l in lines if l.startswith("## ")}
    for h in REQUIRED_HEADINGS:
        if h not in present:
            findings.append({"check": "headings", "status": "MISSING", "heading": h})


def project_field(lines, secs, key):
    rng = secs.get("## Project")
    if rng is None:
        return None
    for i in range(rng[0], rng[1]):
        m = BULLET.match(lines[i])
        if m and m.group(1).strip().lower() == key:
            return m.group(2).strip().strip("`")
    return None


def check_channels(lines, secs, repo, findings):
    rng = secs.get("## Channels")
    if rng is None:
        return []
    workflow = project_field(lines, secs, "release workflow")
    wf_text = ""
    if workflow and (repo / workflow).is_file():
        wf_text = (repo / workflow).read_text(errors="replace")
    arms = []
    current = None
    bullets: dict[str, str] = {}

    def close():
        if current is None:
            return
        arms.append(current)
        for b in REQUIRED_ARM_BULLETS:
            if b not in bullets:
                findings.append({"check": "channels", "status": "MISSING BULLET", "arm": current, "bullet": b})
        job = bullets.get("workflow job")
        if job and job not in ("none", "-") and wf_text:
            jobs = set(re.findall(r"^  ([A-Za-z0-9_-]+):\s*$", wf_text, re.M))
            names = set(re.findall(r"^\s+name:\s*(.+?)\s*$", wf_text, re.M))
            if job not in jobs and job not in names and not any(job in n for n in names):
                findings.append({"check": "channels", "status": "NO SUCH JOB", "arm": current, "job": job, "workflow": workflow})

    for i in range(rng[0], rng[1]):
        m = ARM_HEADING.match(lines[i])
        if m:
            close()
            current = m.group(1).strip("`")
            bullets = {}
            continue
        b = BULLET.match(lines[i])
        if b and current is not None:
            bullets[b.group(1).strip().lower()] = b.group(2).strip().strip("`")
    close()
    if not arms:
        findings.append({"check": "channels", "status": "NO ARMS"})
    return arms


def check_smoke(lines, secs, cli, findings):
    rng = secs.get("## Smoke contract")
    if rng is None:
        return "skipped"
    if not cli:
        return "skipped (no --cli)"
    try:
        out = subprocess.run([cli, "--help"], capture_output=True, text=True, check=False)
    except OSError as e:
        findings.append({"check": "smoke", "status": "CLI NOT RUNNABLE", "cli": cli, "error": str(e)})
        return "failed"
    help_text = out.stdout + out.stderr
    cli_name = pathlib.Path(cli).name
    for i in range(rng[0], rng[1]):
        line = lines[i]
        if not re.match(r"^\|\s*S\d+\s*\|", line):
            continue
        cmds = BACKTICK.findall(line)
        if not cmds:
            continue
        words = cmds[0].split()
        if not words or pathlib.Path(words[0]).name != cli_name:
            continue
        sub = next((w for w in words[1:] if not w.startswith("-") and not w.startswith("$")), None)
        if sub and not re.search(rf"^\s*{re.escape(sub)}\b", help_text, re.M):
            findings.append({"check": "smoke", "status": "UNKNOWN SUBCOMMAND", "row": line.split("|")[1].strip(), "subcommand": sub})
    return "ran"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("profile", nargs="?", default="RELEASE-TRAIN.md", help="path to the profile (default RELEASE-TRAIN.md)")
    ap.add_argument("--repo", help="repo root (default: the profile's directory)")
    ap.add_argument("--cli", help="path to the built CLI, enables the smoke subcommand check")
    ap.add_argument("--update", action="store_true", help="rewrite Sources blob ids and the derived-from commit to the current tree")
    ap.add_argument("--json", action="store_true", help="machine-readable findings")
    args = ap.parse_args(argv)

    profile = pathlib.Path(args.profile)
    if not profile.is_file():
        print(f"profile not found: {profile}", file=sys.stderr)
        return 3
    repo = pathlib.Path(args.repo) if args.repo else profile.resolve().parent
    if not repo.is_dir():
        print(f"repo not found: {repo}", file=sys.stderr)
        return 3

    lines = profile.read_text().splitlines(keepends=True)
    secs = sections(lines)
    findings: list[dict] = []
    check_headings(lines, findings)
    check_sources(lines, secs, repo, findings, args.update)
    check_paths(lines, repo, findings)
    arms = check_channels(lines, secs, repo, findings)
    smoke = check_smoke(lines, secs, args.cli, findings)

    if args.update:
        head = head_commit(repo)
        for i, line in enumerate(lines):
            m = DERIVED.match(line)
            if m:
                lines[i] = f"{m.group(1)}{head}{m.group(3)}\n"
                break
        profile.write_text("".join(lines))

    if args.json:
        print(json.dumps({"profile": str(profile), "arms": arms, "smoke": smoke, "findings": findings}, indent=2))
    else:
        print(f"profile: {profile}  arms: {', '.join(arms) or '(none)'}  smoke check: {smoke}")
        for f in findings:
            detail = ", ".join(f"{k}={v}" for k, v in f.items() if k not in ("check", "status"))
            print(f"  {f['check']:9} {f['status']:16} {detail}")
        if not findings:
            print("  current: every source unchanged, every path present, every arm complete")
        elif args.update:
            print("  sources table and derived-from commit rewritten; re-read the sections the CHANGED rows feed")
    return 1 if findings and not args.update else 0


if __name__ == "__main__":
    sys.exit(main())
