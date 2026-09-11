#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""review-swarm: check reviewer findings against the code, and render the table.

Two subcommands, stdlib only:

  verify --repo ROOT --run DIR [--arms a,b,c,d] [--slack N] [--json]
      Read DIR/<arm>.json for every arm. An arm with no file, unparsable
      JSON, or no findings list is ARM FAILED and said so in capitals; an
      arm that declared "status": "partial" is ARM PARTIAL. Every finding
      is checked against ROOT: the file exists, the range is inside it, and
      the whitespace-normalized evidence_quote occurs within the range (or
      within --slack lines of it, in which case the range is corrected).
      Findings that fail are dropped with a reason. Plainly identical
      findings are merged; overlapping ones are flagged as duplicate
      candidates for the referee. Writes DIR/verified.json.

  table --run DIR [--json]
      Render DIR/final.json (the referee's output) or, failing that,
      DIR/verified.json marked UNREFEREED, as a ranked Markdown table with
      the arm-status lines above it.

Exit codes follow the dev-tools/cli-conventions contract:

  0  every arm delivered a complete file (findings may still be dropped)
  1  ran fine; at least one arm is FAILED or PARTIAL, or (table) the
     result being rendered is unrefereed
  2  usage error
  3  missing precondition (run directory or repo not found)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMA = "review-swarm/1"
DEFAULT_ARMS = ("security", "correctness", "compat", "docs")
SEVERITIES = ("critical", "high", "medium", "low")
REQUIRED = ("severity", "file", "line_range", "claim", "evidence_quote", "suggested_fix")
DEFAULT_SLACK = 3
MERGE_SIMILARITY = 0.5
_TOKEN = re.compile(r"[a-z0-9_]{3,}")


def norm(text: str) -> str:
    """Collapse all whitespace runs to one space; nothing else is changed."""
    return " ".join(str(text).split())


def tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def jaccard(a: str, b: str) -> float:
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


# --------------------------------------------------------------------------
# Loading arms
# --------------------------------------------------------------------------


def load_arm(run: Path, arm: str) -> dict:
    """Return {"status": OK|PARTIAL|FAILED, "reason": str, "findings": list}."""
    path = run / f"{arm}.json"
    if not path.is_file():
        return {"status": "FAILED", "reason": f"no output file (expected {path})", "findings": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"status": "FAILED", "reason": f"unparsable JSON in {path}: {exc}", "findings": []}
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return {
            "status": "FAILED",
            "reason": f"{path} has no \"findings\" list",
            "findings": [],
        }
    status = data.get("status", "complete")
    if status == "partial":
        note = norm(data.get("note", "")) or "no note given"
        return {"status": "PARTIAL", "reason": f"arm declared partial: {note}", "findings": data["findings"]}
    if status != "complete":
        return {
            "status": "FAILED",
            "reason": f"{path} has unknown status {status!r} (want complete or partial)",
            "findings": [],
        }
    return {"status": "OK", "reason": "", "findings": data["findings"]}


# --------------------------------------------------------------------------
# Checking one finding
# --------------------------------------------------------------------------


class Drop(Exception):
    """A finding fails the evidence check; the message is the reason."""


def _read_lines(repo: Path, rel: str) -> list[str]:
    if not rel or rel.startswith(("/", "\\")) or ".." in Path(rel).parts:
        raise Drop(f"file path must be relative to the repo and contain no '..': {rel!r}")
    path = repo / rel
    if not path.is_file():
        raise Drop(f"file not found in checkout: {rel}")
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError as exc:
        raise Drop(f"cannot read {rel}: {exc}") from exc


def _tightest_range(lines: list[str], quote: str, lo: int, hi: int) -> tuple[int, int] | None:
    """Smallest 1-based inclusive [s, e] inside [lo, hi] whose text contains quote."""
    best = None
    for start in range(lo, hi + 1):
        acc: list[str] = []
        for end in range(start, hi + 1):
            acc.append(lines[end - 1])
            if quote in norm(" ".join(acc)):
                if best is None or (end - start) < (best[1] - best[0]):
                    best = (start, end)
                break
    return best


def check_finding(repo: Path, finding: dict, slack: int) -> dict:
    """Return a normalized copy of `finding`, or raise Drop with the reason."""
    if not isinstance(finding, dict):
        raise Drop("finding is not an object")
    missing = [key for key in REQUIRED if key not in finding]
    if missing:
        raise Drop("missing field(s): " + ", ".join(missing))

    severity = str(finding["severity"]).strip().lower()
    if severity not in SEVERITIES:
        raise Drop(f"unknown severity {finding['severity']!r} (want one of {', '.join(SEVERITIES)})")

    rng = finding["line_range"]
    if (
        not isinstance(rng, (list, tuple))
        or len(rng) != 2
        or not all(isinstance(n, int) and not isinstance(n, bool) for n in rng)
    ):
        raise Drop(f"line_range must be [first, last] integers, got {rng!r}")
    first, last = int(rng[0]), int(rng[1])
    if first < 1 or last < first:
        raise Drop(f"line_range out of order or below 1: [{first}, {last}]")

    quote = norm(finding["evidence_quote"])
    if not quote:
        raise Drop("empty evidence_quote")

    rel = str(finding["file"]).strip()
    lines = _read_lines(repo, rel)
    if last > len(lines):
        raise Drop(f"line_range [{first}, {last}] exceeds file length {len(lines)}")

    window = norm(" ".join(lines[first - 1 : last]))
    note = ""
    if quote not in window:
        lo, hi = max(1, first - slack), min(len(lines), last + slack)
        found = _tightest_range(lines, quote, lo, hi)
        if found is None:
            if quote in norm(" ".join(lines)):
                raise Drop(
                    f"evidence_quote exists in {rel} but not within lines "
                    f"{first}-{last} (checked +/- {slack})"
                )
            raise Drop(f"evidence_quote not found in {rel}")
        note = f"range corrected from [{first}, {last}] to [{found[0]}, {found[1]}]"
        first, last = found
    else:
        found = _tightest_range(lines, quote, first, last)
        if found and found != (first, last):
            note = f"range tightened from [{first}, {last}] to [{found[0]}, {found[1]}]"
            first, last = found

    out = {
        "severity": severity,
        "file": rel,
        "line_range": [first, last],
        "claim": norm(finding["claim"]),
        "evidence_quote": str(finding["evidence_quote"]),
        "suggested_fix": norm(finding["suggested_fix"]),
    }
    if note:
        out["check_note"] = note
    return out


# --------------------------------------------------------------------------
# Dedup
# --------------------------------------------------------------------------


def _overlap(a: dict, b: dict) -> bool:
    if a["file"] != b["file"]:
        return False
    (a1, a2), (b1, b2) = a["line_range"], b["line_range"]
    return a1 <= b2 and b1 <= a2


def dedup(findings: list[dict]) -> tuple[list[dict], list[list[str]]]:
    """Merge near-identical findings; flag merely overlapping ones.

    Two findings on overlapping lines of one file whose claims share at
    least MERGE_SIMILARITY of their words are one finding: keep the first,
    take the higher severity, union the arms. Overlapping findings below
    that similarity are returned as candidate groups for the referee, who
    can read the code; this function cannot.
    """
    kept: list[dict] = []
    for f in findings:
        target = None
        for k in kept:
            if _overlap(k, f) and jaccard(k["claim"], f["claim"]) >= MERGE_SIMILARITY:
                target = k
                break
        if target is None:
            kept.append(f)
            continue
        if SEVERITIES.index(f["severity"]) < SEVERITIES.index(target["severity"]):
            target["severity"] = f["severity"]
        for arm in f["arms"]:
            if arm not in target["arms"]:
                target["arms"].append(arm)
        target.setdefault("merged_from", []).append(f["id"])

    candidates: list[list[str]] = []
    seen: set[str] = set()
    for i, a in enumerate(kept):
        if a["id"] in seen:
            continue
        group = [a["id"]]
        for b in kept[i + 1 :]:
            if b["id"] not in seen and _overlap(a, b):
                group.append(b["id"])
        if len(group) > 1:
            seen.update(group)
            candidates.append(group)
    return kept, candidates


# --------------------------------------------------------------------------
# verify
# --------------------------------------------------------------------------


def cmd_verify(args: argparse.Namespace) -> int:
    repo = Path(args.repo).resolve()
    run = Path(args.run).resolve()
    if not repo.is_dir():
        print(f"missing precondition: repo not found: {repo}", file=sys.stderr)
        return 3
    if not run.is_dir():
        print(f"missing precondition: run directory not found: {run}", file=sys.stderr)
        return 3
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    if not arms:
        print("usage error: --arms is empty", file=sys.stderr)
        return 2

    arm_report: dict[str, dict] = {}
    findings: list[dict] = []
    dropped: list[dict] = []
    counter = 0
    for arm in arms:
        loaded = load_arm(run, arm)
        received = len(loaded["findings"])
        verified = 0
        for raw in loaded["findings"]:
            counter += 1
            fid = f"F{counter}"
            try:
                checked = check_finding(repo, raw, args.slack)
            except Drop as exc:
                dropped.append(
                    {
                        "id": fid,
                        "arm": arm,
                        "file": str(raw.get("file", "?")) if isinstance(raw, dict) else "?",
                        "line_range": raw.get("line_range") if isinstance(raw, dict) else None,
                        "claim": norm(raw.get("claim", "")) if isinstance(raw, dict) else "",
                        "reason": str(exc),
                    }
                )
                continue
            verified += 1
            findings.append({"id": fid, "arms": [arm], **checked})
        arm_report[arm] = {
            "status": loaded["status"],
            "reason": loaded["reason"],
            "received": received,
            "verified": verified,
            "dropped": received - verified,
        }

    kept, candidates = dedup(findings)
    result = {
        "schema": SCHEMA,
        "repo": str(repo),
        "arms": arm_report,
        "findings": kept,
        "dropped": dropped,
        "dup_candidates": candidates,
    }
    (run / "verified.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    report = sys.stderr if args.json else sys.stdout
    bad = 0
    for arm, info in arm_report.items():
        if info["status"] in ("FAILED", "PARTIAL"):
            bad += 1
            print(f"!!! ARM {info['status']}: {arm} — {info['reason']}", file=report)
        else:
            print(f"arm {arm}: OK, {info['verified']} verified, {info['dropped']} dropped", file=report)
        if info["status"] == "PARTIAL":
            print(
                f"    (partial arm: {info['verified']} verified, {info['dropped']} dropped)",
                file=report,
            )
    for d in dropped:
        print(f"dropped {d['id']} [{d['arm']}] {d['file']}: {d['reason']}", file=report)
    merged = sum(len(f.get("merged_from", [])) for f in kept)
    print(
        f"{len(kept)} findings verified ({merged} merged as identical), "
        f"{len(dropped)} dropped, {len(candidates)} duplicate-candidate group(s); "
        f"wrote {run / 'verified.json'}",
        file=report,
    )
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    return 1 if bad else 0


# --------------------------------------------------------------------------
# table
# --------------------------------------------------------------------------


def rank_key(f: dict) -> tuple:
    return (SEVERITIES.index(f["severity"]), -len(f.get("arms", [])), f["file"], f["line_range"][0])


def _cell(text: str, limit: int | None = None) -> str:
    text = norm(text).replace("|", "\\|")
    if limit and len(text) > limit:
        text = text[: limit - 1].rstrip() + "…"
    return text


def render_table(data: dict, refereed: bool) -> str:
    lines: list[str] = []
    ranked = sorted(data.get("findings", []), key=rank_key)
    head = f"## Review swarm: {len(ranked)} finding(s)"
    if not refereed:
        head += " — UNREFEREED (referee produced no final.json; rendered from verified.json)"
    lines.append(head)
    lines.append("")
    arms = data.get("arms", {})
    trouble = [a for a, i in arms.items() if i.get("status") in ("FAILED", "PARTIAL")]
    if trouble:
        for arm in trouble:
            lines.append(f"!!! ARM {arms[arm]['status']}: {arm} — {arms[arm].get('reason', '')}")
    else:
        lines.append(f"All {len(arms)} arms delivered.")
    lines.append("")
    if ranked:
        lines.append("| # | ID | Severity | Arms | Location | Claim | Suggested fix |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for n, f in enumerate(ranked, 1):
            a, b = f["line_range"]
            loc = f"`{f['file']}:{a}`" if a == b else f"`{f['file']}:{a}-{b}`"
            lines.append(
                f"| {n} | {f['id']} | {f['severity']} | {', '.join(f.get('arms', []))} | {loc} "
                f"| {_cell(f['claim'])} | {_cell(f['suggested_fix'], 160)} |"
            )
    else:
        lines.append("No findings survived.")
    lines.append("")
    dropped_check = len(data.get("dropped", []))
    ref = data.get("referee", {})
    parts = [f"checker dropped {dropped_check}"]
    if refereed:
        parts.append(f"referee dropped {len(ref.get('dropped', []))}")
        parts.append(f"merged {len(ref.get('merged', []))}")
        if ref.get("status") == "partial":
            parts.append(
                f"REFEREE PARTIAL: {len(ref.get('unexamined', []))} finding(s) not examined"
            )
    lines.append("Dropped before this table: " + "; ".join(parts) + ".")
    return "\n".join(lines) + "\n"


def cmd_table(args: argparse.Namespace) -> int:
    run = Path(args.run).resolve()
    if not run.is_dir():
        print(f"missing precondition: run directory not found: {run}", file=sys.stderr)
        return 3
    final = run / "final.json"
    verified = run / "verified.json"
    refereed = final.is_file()
    source = final if refereed else verified
    if not source.is_file():
        print(f"missing precondition: neither final.json nor verified.json in {run}", file=sys.stderr)
        return 3
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"missing precondition: {source} is not valid JSON: {exc}", file=sys.stderr)
        return 3
    if refereed and verified.is_file():
        # The referee copies "arms"; if it dropped the map, restore it from the checker.
        if not data.get("arms"):
            data["arms"] = json.loads(verified.read_text(encoding="utf-8")).get("arms", {})
        if "dropped" not in data:
            data["dropped"] = json.loads(verified.read_text(encoding="utf-8")).get("dropped", [])
    if args.json:
        json.dump(
            {"refereed": refereed, "arms": data.get("arms", {}), "findings": sorted(data.get("findings", []), key=rank_key)},
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_table(data, refereed))
    trouble = any(i.get("status") in ("FAILED", "PARTIAL") for i in data.get("arms", {}).values())
    return 1 if (trouble or not refereed) else 0


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    v = sub.add_parser("verify", help="check every arm's findings against the checkout")
    v.add_argument("--repo", required=True, help="head checkout root")
    v.add_argument("--run", required=True, help="run directory holding <arm>.json files")
    v.add_argument("--arms", default=",".join(DEFAULT_ARMS), help="comma-separated arm names")
    v.add_argument("--slack", type=int, default=DEFAULT_SLACK, help="lines of range tolerance")
    v.add_argument("--json", action="store_true", help="emit verified.json on stdout")
    v.set_defaults(func=cmd_verify)

    t = sub.add_parser("table", help="render the ranked findings table")
    t.add_argument("--run", required=True, help="run directory")
    t.add_argument("--json", action="store_true", help="emit the ranked list as JSON")
    t.set_defaults(func=cmd_table)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
