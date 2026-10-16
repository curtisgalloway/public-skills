#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""review-swarm: check reviewer findings against the code, and render the table.

Four subcommands, stdlib only:

  plan --run DIR [--tier auto|light|standard|full] [--close] [--external CLI] [--json]
      Read DIR/diff.patch, pick the review tier from the diff's size, the
      kind of files it touches, and risk triggers in its changed lines, and
      write DIR/plan.json: the tier, the reasons, and the arms to launch
      with a model class and budget for each. The agent launches what the
      plan says; it does not choose arms itself. --external adds, outside
      the light tier, a correctness-CLI arm with the correctness mandate and
      model "external:CLI", run in that agent CLI instead of a subagent.

  collect --run DIR --arm NAME --stream FILE
      Turn an external arm's saved output (Muse's --json events, or plain
      text) into DIR/NAME.json: the first JSON object with a findings list.
      Without one, writes nothing, so verify reports the arm FAILED.

  verify --repo ROOT --run DIR [--arms a,b,c,d] [--slack N] [--json]
      Read DIR/<arm>.json for every arm (the arms in DIR/plan.json when
      --arms is not given, else the seven full-tier arms). An arm with no
      file, unparsable JSON, or no findings list is ARM FAILED and said so
      in capitals; an
      arm that declared "status": "partial" is ARM PARTIAL. Every finding
      is checked against ROOT: the file exists, the range is inside it, and
      the whitespace-normalized evidence_quote occurs within the range (or
      within --slack lines of it, in which case the range is corrected).
      Findings that fail are dropped with a reason. When DIR/diff.patch
      exists, a finding whose lines touch no hunk of the diff is kept but
      marked outside_diff, for the referee to judge. Plainly identical
      findings are merged; overlapping ones are flagged as duplicate
      candidates for the referee. Records whether the referee is needed (a
      surviving high or critical finding, or a duplicate-candidate group).
      An arm file with a "resolved" list (the recheck after fixes) has each
      resolution's quote checked too; one that cannot be found is
      RESOLUTION NOT CONFIRMED. Writes DIR/verified.json.

  table --run DIR [--json | --format pr --blob-url URL]
      Render DIR/final.json (the referee's output) or, failing that,
      DIR/verified.json, as a ranked Markdown table with the arm-status
      lines above it. A result that needed a referee and has none is
      marked UNREFEREED. --format pr renders the same result
      as a pull request comment, each location a permalink under URL
      (https://github.com/<owner>/<repo>/blob/<full head sha>).

Exit codes follow the dev-tools/cli-conventions contract:

  0  every arm delivered a complete file (findings may still be dropped)
  1  ran fine; at least one arm is FAILED or PARTIAL, a recheck resolution
     is not confirmed, or (table) the result needed a referee and has none
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
DEFAULT_ARMS = ("security", "correctness", "compat", "docs", "history", "conventions", "perf")
SEVERITIES = ("critical", "high", "medium", "low")
REQUIRED = ("severity", "file", "line_range", "claim", "evidence_quote", "suggested_fix")
DEFAULT_SLACK = 3
MERGE_SIMILARITY = 0.5
_TOKEN = re.compile(r"[a-z0-9_]{3,}")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


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
# plan: pick the tier and the arms
# --------------------------------------------------------------------------

PLAN_SCHEMA = "review-swarm-plan/1"
LIGHT_MAX_LINES = 50
SPLIT_LINES = 3000
STANDARD_ARMS = ("correctness", "docs", "compat", "context")
STRONG_ARMS = ("correctness",)
# Files that are prose, records, data or config rather than executable code.
# Measured: 67 swarm runs over diffs of only these kinds produced no high or
# critical finding, so they get the light tier at any size.
NONCODE_EXT = {
    ".md", ".markdown", ".rst", ".txt", ".adoc", ".org", ".log", ".csv", ".tsv",
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".svg", ".png", ".jpg", ".jpeg", ".gif", ".pdf",
}
NONCODE_NAMES = {"LICENSE", "NOTICE", "COPYING", "AUTHORS", "CHANGELOG", "CODEOWNERS"}
# Risk triggers, matched case-insensitively against changed lines of code
# files. A full-tier trigger sends the whole review to all seven arms; a
# security-surface trigger adds the security arm to the standard tier.
FULL_TRIGGERS = {
    "secrets/auth": re.compile(
        r"\b(password|passwd|secret|api[_-]?key|access[_-]?token|bearer|credential\w*|"
        r"private[_-]?key|authenticat\w*|authoriz\w*|oauth|jwt|session[_-]?id)\b",
        re.I,
    ),
    "concurrency": re.compile(
        r"\b(thread\w*|mutex\w*|rwlock|locks?|semaphore|atomic\w*|async|await|"
        r"goroutine|condvar|spinlock)\b",
        re.I,
    ),
    "persisted format": re.compile(
        r"\b(migrations?|schema|alter\s+table|create\s+table|serializ\w*|deserializ\w*|"
        r"pickle|protobuf|fsync)\b",
        re.I,
    ),
}
FULL_TRIGGER_PATHS = re.compile(r"(^|/)migrations?/|\.(sql|proto)$", re.I)
SECURITY_SURFACE = re.compile(
    r"\b(subprocess|popen|os\.system|shell\s*=\s*true|eval|exec\w*|unsafe|yaml\.load|"
    r"urlopen|requests\.|socket|chmod|mktemp|tempfile|sql)\b",
    re.I,
)


def is_code(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    if name in NONCODE_NAMES or name.split(".")[0] in NONCODE_NAMES:
        return False
    ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
    return ext not in NONCODE_EXT


def diff_files(patch: str) -> dict[str, list[str]]:
    """Map each path in a unified diff to its changed (+/-) lines, marker stripped."""
    files: dict[str, list[str]] = {}
    current: str | None = None
    old: str | None = None
    for line in patch.splitlines():
        if line.startswith("--- "):
            src = line[4:].split("\t")[0].strip()
            old = None if src == "/dev/null" else src.removeprefix("a/")
            continue
        if line.startswith("+++ "):
            dst = line[4:].split("\t")[0].strip()
            current = old if dst == "/dev/null" else dst.removeprefix("b/")
            if current is not None:
                files.setdefault(current, [])
            continue
        if current is None or line.startswith(("diff --git", "@@", "index ")):
            continue
        if line[:1] in "+-":
            files[current].append(line[1:])
    return files


def arm_spec(name: str, code: bool, changed: int) -> dict:
    strong = name in STRONG_ARMS or (name == "light" and code)
    budget = (25, 8) if name == "light" and changed <= 300 else (40, 15)
    return {"name": name, "model": "strong" if strong else "cheap",
            "tool_budget": budget[0], "wall_minutes": budget[1]}


def make_plan(patch: str, tier: str = "auto", close: bool = False,
              external: str | None = None) -> dict:
    files = diff_files(patch)
    changed = sum(len(v) for v in files.values())
    code_files = sorted(p for p in files if is_code(p))
    triggers: dict[str, list[str]] = {}
    surface: list[str] = []
    for path in code_files:
        if FULL_TRIGGER_PATHS.search(path):
            triggers.setdefault("persisted format", []).append(path)
        for text in files[path]:
            for label, rx in FULL_TRIGGERS.items():
                m = rx.search(text)
                if m and len(triggers.setdefault(label, [])) < 3:
                    triggers[label].append(f"{path}: {m.group(0)}")
            m = SECURITY_SURFACE.search(text)
            if m and len(surface) < 3:
                surface.append(f"{path}: {m.group(0)}")
    triggers = {k: v for k, v in triggers.items() if v}

    reasons: list[str] = []
    if tier != "auto":
        reasons.append(f"tier {tier} requested")
        chosen = tier
    elif not code_files:
        chosen = "light"
        reasons.append("no code files changed (prose, records, data or config only)")
    elif triggers:
        chosen = "full"
        reasons.append("risk trigger(s) in changed code: " + ", ".join(sorted(triggers)))
    elif close:
        chosen = "full"
        reasons.append("closing review of a pull request or milestone that changes code")
    elif changed <= LIGHT_MAX_LINES:
        chosen = "light"
        reasons.append(f"{changed} changed line(s), at most {LIGHT_MAX_LINES}, no risk trigger")
    else:
        chosen = "standard"
        reasons.append(f"{changed} changed lines of code, no full-tier trigger")

    if chosen == "light":
        names = ["light"]
    elif chosen == "standard":
        names = list(STANDARD_ARMS)
        if surface:
            names.insert(0, "security")
            reasons.append("security surface in changed code: " + "; ".join(surface))
    else:
        names = list(DEFAULT_ARMS)
    arms = [arm_spec(n, bool(code_files), changed) for n in names]
    # The arm that owns a fired trigger's risk gets the strong model too.
    owners = {"secrets/auth": "security", "persisted format": "compat"}
    for label in triggers:
        for a in arms:
            if a["name"] == owners.get(label):
                a["model"] = "strong"
    # A second correctness arm on another vendor's model: the bug every same-vendor
    # reviewer misses is the one a different model is most likely to see.
    if external and chosen != "light":
        twin = dict(arm_spec("correctness", True, changed), name=f"correctness-{external}",
                    model=f"external:{external}", mandate="correctness")
        arms.insert([a["name"] for a in arms].index("correctness") + 1, twin)
        reasons.append(f"cross-vendor correctness arm on {external} (requested)")
    elif external:
        reasons.append(f"cross-vendor arm on {external} not added: the light tier is one reviewer")
    return {
        "schema": PLAN_SCHEMA,
        "tier": chosen,
        "reasons": reasons,
        "changed_lines": changed,
        "files": len(files),
        "code_files": len(code_files),
        "triggers": triggers,
        "split_required": changed > SPLIT_LINES,
        "arms": arms,
        "referee": "only if a surviving finding is high or critical, or the checker "
        "flags a duplicate-candidate group",
    }


def cmd_plan(args: argparse.Namespace) -> int:
    run = Path(args.run).resolve()
    patch = run / "diff.patch"
    if not patch.is_file():
        print(f"missing precondition: {patch} not found", file=sys.stderr)
        return 3
    plan = make_plan(patch.read_text(encoding="utf-8", errors="replace"), args.tier, args.close,
                     args.external)
    (run / "plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if args.json:
        json.dump(plan, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"tier: {plan['tier']} — {plan['changed_lines']} changed lines in {plan['files']} "
          f"file(s), {plan['code_files']} of them code")
    for r in plan["reasons"]:
        print(f"  because: {r}")
    for a in plan["arms"]:
        print(f"  arm {a['name']}: {a['model']} model, {a['tool_budget']} tool calls, "
              f"{a['wall_minutes']} min")
    print(f"  referee: {plan['referee']}")
    if plan["split_required"]:
        print(f"!!! SPLIT REQUIRED: more than {SPLIT_LINES} changed lines. Split by directory or "
              "commit; every part runs this same arm list.")
    print(f"wrote {run / 'plan.json'}")
    return 0



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
        return {
            "status": "PARTIAL",
            "reason": f"arm declared partial: {note}",
            "findings": data["findings"],
            "resolved": data.get("resolved"),
        }
    if status != "complete":
        return {
            "status": "FAILED",
            "reason": f"{path} has unknown status {status!r} (want complete or partial)",
            "findings": [],
        }
    return {"status": "OK", "reason": "", "findings": data["findings"], "resolved": data.get("resolved")}


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


def check_resolved(repo: Path, arm: str, entries: list, slack: int) -> list[dict]:
    """Check each recheck "resolved" entry's quote the way a finding's is checked.

    A resolution whose quote is not in the checkout is reported as not
    confirmed: the fix it claims cannot be pointed at.
    """
    out = []
    for entry in entries:
        entry = entry if isinstance(entry, dict) else {}
        probe = {
            "severity": "low",
            "file": entry.get("file", ""),
            "line_range": entry.get("line_range"),
            "claim": "resolution",
            "evidence_quote": entry.get("evidence_quote", ""),
            "suggested_fix": "",
        }
        try:
            checked = check_finding(repo, probe, slack)
        except Drop as exc:
            out.append({"id": entry.get("id", "?"), "arm": arm, "confirmed": False, "reason": str(exc)})
            continue
        out.append({"id": entry.get("id", "?"), "arm": arm, "confirmed": True,
                    "file": checked["file"], "line_range": checked["line_range"]})
    return out


# --------------------------------------------------------------------------
# Diff hunks
# --------------------------------------------------------------------------


def diff_hunks(patch: str) -> dict[str, list[tuple[int, int]]]:
    """Map each head-side path in a unified diff to its hunks' line ranges.

    A range is the hunk's whole head-side span, context lines included, so a
    finding next to a changed line still counts as touching the change. A
    pure deletion (zero head lines) is recorded as the one line it sits at.
    Deleted files have no head side and are absent from the map.
    """
    hunks: dict[str, list[tuple[int, int]]] = {}
    current: str | None = None
    for line in patch.splitlines():
        if line.startswith("+++ "):
            target = line[4:].split("\t")[0].strip()
            current = None if target == "/dev/null" else target.removeprefix("b/")
            continue
        m = _HUNK.match(line)
        if m and current is not None:
            start = int(m.group(1))
            count = 1 if m.group(2) is None else int(m.group(2))
            hunks.setdefault(current, []).append((max(start, 1), max(start, 1) + max(count, 1) - 1))
    return hunks


def touches_diff(finding: dict, hunks: dict[str, list[tuple[int, int]]]) -> bool:
    first, last = finding["line_range"]
    return any(a <= last and first <= b for a, b in hunks.get(finding["file"], []))


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
    arm_list = args.arms
    plan_path = run / "plan.json"
    if arm_list is None and plan_path.is_file():
        try:
            arm_list = ",".join(a["name"] for a in json.loads(plan_path.read_text())["arms"])
        except (OSError, ValueError, KeyError, TypeError) as exc:
            print(f"missing precondition: unreadable {plan_path}: {exc}", file=sys.stderr)
            return 3
    if arm_list is None:
        arm_list = ",".join(DEFAULT_ARMS)
    arms = [a.strip() for a in arm_list.split(",") if a.strip()]
    if not arms:
        print("usage error: --arms is empty", file=sys.stderr)
        return 2

    patch = run / "diff.patch"
    hunks = diff_hunks(patch.read_text(encoding="utf-8", errors="replace")) if patch.is_file() else None

    arm_report: dict[str, dict] = {}
    findings: list[dict] = []
    dropped: list[dict] = []
    resolved_report: list[dict] = []
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
            if hunks is not None and not touches_diff(checked, hunks):
                checked["outside_diff"] = True
            findings.append({"id": fid, "arms": [arm], **checked})
        if isinstance(loaded.get("resolved"), list):
            resolved_report.extend(check_resolved(repo, arm, loaded["resolved"], args.slack))
        arm_report[arm] = {
            "status": loaded["status"],
            "reason": loaded["reason"],
            "received": received,
            "verified": verified,
            "dropped": received - verified,
        }

    kept, candidates = dedup(findings)
    serious = [f["id"] for f in kept if f["severity"] in ("critical", "high")]
    if serious or candidates:
        why = []
        if serious:
            why.append(f"{len(serious)} high/critical finding(s)")
        if candidates:
            why.append(f"{len(candidates)} duplicate-candidate group(s)")
        referee_reason = ", ".join(why)
    else:
        referee_reason = "no high/critical finding and no duplicate-candidate group"
    result = {
        "schema": SCHEMA,
        "repo": str(repo),
        "arms": arm_report,
        "findings": kept,
        "dropped": dropped,
        "dup_candidates": candidates,
        "diff_checked": hunks is not None,
        "referee_needed": bool(serious or candidates),
        "resolved": resolved_report,
        "referee_reason": referee_reason,
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
    for r in resolved_report:
        if r["confirmed"]:
            print(f"resolved {r['id']}: quote confirmed at {r['file']}:{r['line_range'][0]}", file=report)
        else:
            print(f"!!! RESOLUTION NOT CONFIRMED {r['id']}: {r['reason']}", file=report)
    merged = sum(len(f.get("merged_from", [])) for f in kept)
    if hunks is None:
        print(f"no {patch}; findings were not checked against the diff's hunks", file=report)
    else:
        outside = sum(1 for f in kept if f.get("outside_diff"))
        print(f"{outside} finding(s) touch no hunk of the diff (marked outside_diff)", file=report)
    print(
        f"{len(kept)} findings verified ({merged} merged as identical), "
        f"{len(dropped)} dropped, {len(candidates)} duplicate-candidate group(s); "
        f"wrote {run / 'verified.json'}",
        file=report,
    )
    print(
        f"referee: {'NEEDED' if result['referee_needed'] else 'not needed'} ({referee_reason})",
        file=report,
    )
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    unconfirmed = any(not r["confirmed"] for r in resolved_report)
    return 1 if (bad or unconfirmed) else 0


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


def referee_skipped(data: dict, refereed: bool) -> bool:
    """True when there is no referee result because none was needed."""
    return not refereed and data.get("referee_needed") is False


def render_table(data: dict, refereed: bool) -> str:
    lines: list[str] = []
    ranked = sorted(data.get("findings", []), key=rank_key)
    head = f"## Review swarm: {len(ranked)} finding(s)"
    if referee_skipped(data, refereed):
        head += " — not refereed: " + data.get("referee_reason", "referee not needed")
    elif not refereed:
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
            if f.get("outside_diff"):
                loc += " (outside diff)"
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


def render_pr(data: dict, refereed: bool, blob_url: str) -> str:
    """The same ranked result as a pull request comment with permalinks.

    Arm failures and an unrefereed result are stated in the comment too: a
    reader of the PR must be able to tell a partial review from a clean one.
    """
    blob_url = blob_url.rstrip("/")
    ranked = sorted(data.get("findings", []), key=rank_key)
    arms = data.get("arms", {})
    lines = ["### Review swarm", ""]
    if referee_skipped(data, refereed):
        lines += [f"Not refereed: {data.get('referee_reason', 'referee not needed')}; "
                  "findings passed the quote check.", ""]
    elif not refereed:
        lines += ["**UNREFEREED**: the referee produced no result; findings passed only the quote check.", ""]
    trouble = [a for a, i in arms.items() if i.get("status") in ("FAILED", "PARTIAL")]
    for arm in trouble:
        lines.append(f"- **ARM {arms[arm]['status']}: {arm}** — {_cell(arms[arm].get('reason', ''))}")
    if trouble:
        lines.append("")
    ok = [a for a in arms if a not in trouble]
    lines.append(f"Arms that delivered: {', '.join(ok) if ok else 'none'}.")
    lines.append("")
    if not ranked:
        lines.append("No findings survived.")
    else:
        lines.append(f"Found {len(ranked)} issue(s):")
        lines.append("")
        for n, f in enumerate(ranked, 1):
            a, b = f["line_range"]
            link = f"{blob_url}/{f['file']}#L{max(a - 1, 1)}-L{b + 1}"
            tag = f"{f['severity']}, {', '.join(f.get('arms', []))}"
            if f.get("outside_diff"):
                tag += ", outside diff"
            lines.append(f"{n}. **{tag}** — {_cell(f['claim'])}")
            lines.append(f"   Fix: {_cell(f['suggested_fix'])}")
            lines.append("")
            lines.append(f"   {link}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def cmd_table(args: argparse.Namespace) -> int:
    if args.format == "pr" and not args.blob_url:
        print("usage error: --format pr needs --blob-url", file=sys.stderr)
        return 2
    if args.format == "pr" and args.json:
        print("usage error: --json and --format pr are exclusive", file=sys.stderr)
        return 2
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
    elif args.format == "pr":
        sys.stdout.write(render_pr(data, refereed, args.blob_url))
    else:
        sys.stdout.write(render_table(data, refereed))
    trouble = any(i.get("status") in ("FAILED", "PARTIAL") for i in data.get("arms", {}).values())
    return 1 if (trouble or not (refereed or referee_skipped(data, refereed))) else 0


# --------------------------------------------------------------------------
# External arms
# --------------------------------------------------------------------------


def external_name(value: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9]*", value):
        raise argparse.ArgumentTypeError("a CLI name: lowercase letters and digits")
    return value


def final_text(raw: str) -> str:
    """The final answer in a CLI's saved output: Muse's run.terminal.completed text when
    the output is its --json event stream, otherwise the output itself."""
    answer = None
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            return raw
        if isinstance(event, dict) and event.get("payload_type") == "run.terminal.completed":
            answer = (event.get("payload") or {}).get("text")
    return raw if answer is None else answer


def arm_object(text: str, arm: str) -> dict | None:
    """The first JSON object in text that carries a findings list, fences allowed."""
    decoder = json.JSONDecoder()
    for start in (i for i, ch in enumerate(text) if ch == "{"):
        try:
            obj, _ = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and isinstance(obj.get("findings"), list):
            obj["arm"] = arm
            return obj
    return None


def cmd_collect(args: argparse.Namespace) -> int:
    run = Path(args.run).resolve()
    stream = Path(args.stream)
    if not stream.is_file():
        print(f"!!! ARM FAILED: {args.arm} — no output at {stream}", file=sys.stderr)
        return 1
    obj = arm_object(final_text(stream.read_text(encoding="utf-8", errors="replace")), args.arm)
    if obj is None:
        # Leave <arm>.json absent, so verify reports the arm as FAILED, never as empty.
        print(f"!!! ARM FAILED: {args.arm} — no findings object in {stream}", file=sys.stderr)
        return 1
    (run / f"{args.arm}.json").write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {run / (args.arm + '.json')}: {len(obj['findings'])} finding(s)")
    return 0


# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan", help="pick the review tier and arms from DIR/diff.patch")
    p.add_argument("--run", required=True, help="run directory holding diff.patch")
    p.add_argument("--tier", choices=("auto", "light", "standard", "full"), default="auto",
                   help="override the computed tier (the user asked for one)")
    p.add_argument("--close", action="store_true",
                   help="this is the closing review of a pull request or milestone")
    p.add_argument("--external", metavar="CLI", type=external_name,
                   help="add a correctness arm run in another agent CLI (e.g. muse)")
    p.add_argument("--json", action="store_true", help="emit plan.json on stdout")
    p.set_defaults(func=cmd_plan)

    c = sub.add_parser("collect", help="write <arm>.json from an external CLI's output")
    c.add_argument("--run", required=True, help="run directory")
    c.add_argument("--arm", required=True, help="arm name, as in plan.json")
    c.add_argument("--stream", required=True,
                   help="the CLI's saved output: Muse --json events, or plain text")
    c.set_defaults(func=cmd_collect)

    v = sub.add_parser("verify", help="check every arm's findings against the checkout")
    v.add_argument("--repo", required=True, help="head checkout root")
    v.add_argument("--run", required=True, help="run directory holding <arm>.json files")
    v.add_argument("--arms", default=None,
                   help="comma-separated arm names (default: plan.json's arms, else all seven)")
    v.add_argument("--slack", type=int, default=DEFAULT_SLACK, help="lines of range tolerance")
    v.add_argument("--json", action="store_true", help="emit verified.json on stdout")
    v.set_defaults(func=cmd_verify)

    t = sub.add_parser("table", help="render the ranked findings table")
    t.add_argument("--run", required=True, help="run directory")
    t.add_argument("--json", action="store_true", help="emit the ranked list as JSON")
    t.add_argument(
        "--format", choices=("markdown", "pr"), default="markdown", help="terminal table or PR comment"
    )
    t.add_argument("--blob-url", help="permalink base for --format pr: .../blob/<full head sha>")
    t.set_defaults(func=cmd_table)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
