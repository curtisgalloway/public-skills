#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""Check the source anchors in a source-anchored peripheral spec.

A source-anchored spec cites where each fact came from with inline tags:

    [src: drivers/net/ethernet/cadence/macb_main.c:2311-2340 (macb_init_hw)]
    [tgt: src/devices/block/drivers/sdhci/sdhci.cc:88 (Sdhci::Init)]
    [doc: Zynq-7000 TRM UG585 §16.3.2]

``src`` anchors resolve against the source repository, ``tgt`` anchors against
the target-OS repository, both at a pinned commit; ``doc`` tags are citations
to documents and are not resolved.  Several anchors may share one tag,
separated by ``;``.  A line consisting only of tags anchors the table or list
that follows it (a "block anchor").

The spec states its pins on lines of the form::

    Source pin: <name-or-url>@<commit>
    Target pin: <name-or-url>@<commit>

The ``reference-driver-review`` skill uses the same machinery under different
names: ``[impl:]`` is an alias of ``[src:]`` (with ``Impl pin:`` and
``--impl-repo``) and ``[ref:]`` an alias of ``[tgt:]`` (with ``Ref pin:`` and
``--ref-repo``), so a review's implementation-side anchors get drift tracking.

Modes (all stdlib; needs ``git`` on PATH):

  default   resolve every anchor at the pin: path exists, line range in bounds,
            symbol (if given) present in or near the range; flag fact-bearing
            lines that carry no tag at all, claims whose hex literals do not
            appear in the lines they cite, ``[hw-required]`` labels with no
            ``[doc:]`` backing, and ``[doc:]`` tags with no section number.
  --show    render a review sheet: each spec claim followed by the cited source
            lines, so a human can check the spec against the code by reading.
  --drift R compare each anchor's cited lines at the pin with revision R and
            report which anchors need re-review before the pin moves.
  --rewrite with --drift: update the spec in place — anchors whose cited text
            merely moved get their new line numbers and the Source pin becomes
            R; anchors whose text changed keep their numbers and gain a
            ``[stale: was <pin>]`` marker that fails every later check until a
            person re-verifies the claim and removes it.

Exit status: 0 clean, 1 findings, 2 usage or git error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

TAG_RE = re.compile(r"\[(src|tgt|impl|ref|doc|stale):\s*([^\]]*)\]")
KIND_ALIAS = {"impl": "src", "ref": "tgt"}
PIN_ALIAS = {"impl": "source", "ref": "target"}
ANCHOR_RE = re.compile(
    r"^(?P<path>[^\s:()]+):(?P<l1>\d+)(?:-(?P<l2>\d+))?(?:\s*\((?P<sym>[^)]+)\))?$"
)
PIN_RE = re.compile(r"^(Source|Target|Impl|Ref) pin:\s*(?P<name>\S+?)@(?P<rev>[0-9A-Za-z._/-]+)\s*$")
HEX_RE = re.compile(r"0x[0-9A-Fa-f]+")
FACT_HINT_RE = re.compile(
    r"0x[0-9A-Fa-f]+|\bbits?\s*\[?\d|\bIRQ\s*#?\d|\boffset\b|\bdelay\b|\btimeout\b|\bretr(y|ies)\b",
    re.IGNORECASE,
)
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}")
LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
HW_REQUIRED_RE = re.compile(r"\[?\bhw[-_ ]required\b\]?", re.IGNORECASE)
# A section NUMBER, not a quoted title: "§4.3", "section 6", "ch. 12", "Table 3-1", "p. 88",
# "Appendix B". A bare "§" followed by a title is how citations go unverifiable.
DOC_SECTION_RE = re.compile(r"§\s*[A-Z]?\d|\bsec(tion|t)?\.?\s*[A-Z]?\d|\bch(apter)?\.?\s*\d|"
                            r"\btable\s*[A-Z]?\d|\bfig(ure)?\.?\s*\d|\bp(age|p)?\.\s*\d|"
                            r"\bappendix\s*[A-Z0-9]", re.IGNORECASE)


def hex_set(text: str) -> set[str]:
    """Hex literals in text, normalized: lowercase, underscores dropped, leading zeros stripped."""
    out = set()
    for m in re.finditer(r"0[xX][0-9A-Fa-f_]+", text):
        v = m.group(0)[2:].replace("_", "").lower().lstrip("0") or "0"
        out.add(v)
    return out
SYMBOL_BEFORE = 200  # a symbol naming the enclosing definition may precede the range by this much


@dataclass
class Anchor:
    kind: str  # src | tgt
    path: str
    l1: int
    l2: int
    symbol: str | None
    spec_line: int
    claim: str
    raw: str


@dataclass
class Finding:
    level: str  # error | warn
    spec_line: int
    message: str
    anchor: str | None = None


@dataclass
class Report:
    spec: str
    pins: dict = field(default_factory=dict)
    anchors: int = 0
    doc_tags: int = 0
    findings: list = field(default_factory=list)
    moves: list = field(default_factory=list)  # (spec_line, old_raw, new_raw)
    stale: list = field(default_factory=list)  # (spec_line, raw) changed or gone

    def add(self, level: str, spec_line: int, message: str, anchor: str | None = None):
        self.findings.append(Finding(level, spec_line, message, anchor))

    @property
    def errors(self):
        return [f for f in self.findings if f.level == "error"]


class Repo:
    """Read-only view of a git repository at one revision."""

    def __init__(self, path: str, rev: str):
        self.path = Path(path)
        self.rev = rev
        self._files: dict[str, list[str] | None] = {}
        if not (self.path / ".git").exists() and not (self.path / "HEAD").exists():
            raise SystemExit(f"error: {path} is not a git repository")
        full = self._git("rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}")
        if full is None:
            raise SystemExit(f"error: revision {rev!r} not found in {path}")
        self.full_rev = full.strip()

    def _git(self, *args: str) -> str | None:
        proc = subprocess.run(
            ["git", "-C", str(self.path), *args],
            capture_output=True,
            text=True,
            errors="replace",
        )
        if proc.returncode != 0:
            return None
        return proc.stdout

    def lines(self, rel: str) -> list[str] | None:
        if rel not in self._files:
            text = self._git("show", f"{self.full_rev}:{rel}")
            self._files[rel] = None if text is None else text.split("\n")
        return self._files[rel]

    def blob(self, rel: str) -> str | None:
        out = self._git("rev-parse", "--verify", "--quiet", f"{self.full_rev}:{rel}")
        return None if out is None else out.strip()


# --------------------------------------------------------------------------- parse


def parse_tag_body(kind: str, body: str, spec_line: int, claim: str, report: Report) -> list[Anchor]:
    anchors = []
    for item in (s.strip() for s in body.split(";")):
        if not item:
            continue
        m = ANCHOR_RE.match(item)
        if not m:
            report.add("error", spec_line, f"malformed {kind} anchor: {item!r} "
                       "(expected path:L1[-L2] [(symbol)])", item)
            continue
        l1 = int(m["l1"])
        l2 = int(m["l2"]) if m["l2"] else l1
        if l2 < l1:
            report.add("error", spec_line, f"inverted line range in anchor {item!r}", item)
            l1, l2 = l2, l1
        anchors.append(Anchor(kind, m["path"], l1, l2, m["sym"], spec_line, claim, item))
    return anchors


def paragraph_before(lines: list[str], idx: int, tail: str) -> str:
    """Join the paragraph ending at lines[idx] (0-based) with `tail`, newest last."""
    parts = []
    j = idx - 1
    while j >= 0:
        prev = lines[j].strip()
        if not prev or prev.startswith("#") or prev.startswith("|") or LIST_RE.match(lines[j]):
            break
        parts.append(TAG_RE.sub("", prev).strip())
        j -= 1
    parts.reverse()
    joined = " ".join(parts + [tail]).strip(" .,;")
    return joined[-300:]


def parse_spec(text: str, report: Report, strict: bool) -> list[Anchor]:
    anchors: list[Anchor] = []
    lines = text.split("\n")
    # A tags-only line "arms" a block anchor; it covers the next contiguous block
    # (table or list), which may be separated from it by blank lines.
    block_state = None  # None | "armed" | "covering"
    block_anchors: list[Anchor] = []  # anchors of the armed/covering block anchor
    in_code = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        pin = PIN_RE.match(stripped)
        if pin:
            key = pin.group(1).lower()
            report.pins[PIN_ALIAS.get(key, key)] = {"name": pin["name"], "rev": pin["rev"]}
            continue
        tags = TAG_RE.findall(line)
        claim = TAG_RE.sub("", line).strip(" |-*")
        if tags and len(claim) < 40 and not stripped.startswith(("|", "-", "*")) \
                and not LIST_RE.match(line):
            # The tag closes a multi-line paragraph: the claim is the paragraph.
            claim = paragraph_before(lines, i - 1, claim)
        new_anchors: list[Anchor] = []
        for kind, body in tags:
            kind = KIND_ALIAS.get(kind, kind)
            if kind == "stale":
                report.add("error", i, f"anchor marked stale ({body.strip()}): re-verify the "
                                       "claim against the pin and remove the marker")
                continue
            if kind == "doc":
                report.doc_tags += 1
                if not body.strip():
                    report.add("error", i, "empty [doc:] tag")
                elif not DOC_SECTION_RE.search(body):
                    report.add("warn", i, f"[doc:] cites no section/chapter/table number: "
                                          f"{body.strip()[:60]!r}")
                continue
            new_anchors.extend(parse_tag_body(kind, body, i, claim, report))
        anchors.extend(new_anchors)
        if HW_REQUIRED_RE.search(line) and not any(k == "doc" for k, _ in tags):
            report.add("warn", i, "[hw-required] with no [doc:] on the line — if no document "
                                  "backs it, label it [as-implemented]")
        if not stripped:
            if block_state == "covering":
                block_state = None
                block_anchors = []
            continue
        tags_only = bool(tags) and not claim
        if tags_only:
            block_state = "armed"
            block_anchors = new_anchors
            continue
        if block_state == "armed":
            block_state = "covering"
        if block_state == "covering":
            # The block anchor's claim is the block it covers.
            for a in block_anchors:
                a.claim = (a.claim + " / " if a.claim else "") + stripped
            continue
        if tags:
            continue
        # No tag on this line and no block anchor in force: is it a fact?
        is_row = stripped.startswith("|") and not TABLE_SEP_RE.match(stripped)
        is_item = bool(LIST_RE.match(line))
        if not (is_row or is_item):
            continue
        header_row = is_row and i < len(lines) and TABLE_SEP_RE.match(lines[i].strip() or "x")
        if header_row:
            continue
        if strict or FACT_HINT_RE.search(stripped):
            report.add("warn" if not strict else "error", i,
                       "fact-bearing line carries no [src:]/[tgt:]/[doc:] tag: "
                       + stripped[:80])
    report.anchors = len(anchors)
    return anchors


# --------------------------------------------------------------------------- checks


def find_symbol(file_lines: list[str], symbol: str, lo: int, hi: int) -> int | None:
    """First 1-based line in [lo, hi] containing symbol as a whole word, else None."""
    pat = re.compile(r"(?<![A-Za-z0-9_])" + re.escape(symbol) + r"(?![A-Za-z0-9_])")
    lo = max(lo, 1)
    hi = min(hi, len(file_lines))
    for n in range(lo, hi + 1):
        if pat.search(file_lines[n - 1]):
            return n
    return None


def resolve(anchor: Anchor, repo: Repo, report: Report) -> list[str] | None:
    file_lines = repo.lines(anchor.path)
    if file_lines is None:
        report.add("error", anchor.spec_line,
                   f"{anchor.path} does not exist at {repo.rev}", anchor.raw)
        return None
    if anchor.l2 > len(file_lines):
        report.add("error", anchor.spec_line,
                   f"{anchor.path} has {len(file_lines)} lines; anchor cites "
                   f"{anchor.l1}-{anchor.l2}", anchor.raw)
        return None
    cited = file_lines[anchor.l1 - 1: anchor.l2]
    if anchor.symbol:
        # The symbol names the cited definition or the definition enclosing the
        # cited lines, so it may legitimately precede the range.
        if find_symbol(file_lines, anchor.symbol, anchor.l1 - SYMBOL_BEFORE, anchor.l2) is None:
            anywhere = find_symbol(file_lines, anchor.symbol, 1, len(file_lines))
            if anywhere is None:
                report.add("error", anchor.spec_line,
                           f"symbol {anchor.symbol!r} is not in {anchor.path}", anchor.raw)
            else:
                report.add("warn", anchor.spec_line,
                           f"symbol {anchor.symbol!r} first appears at line {anywhere}, not "
                           f"within {SYMBOL_BEFORE} lines before the cited range "
                           f"{anchor.l1}-{anchor.l2}", anchor.raw)
    if all(not l.strip() for l in cited):
        report.add("warn", anchor.spec_line,
                   f"cited range {anchor.path}:{anchor.l1}-{anchor.l2} is blank", anchor.raw)
    return cited


def check_hex_consistency(anchors: list[Anchor], cited_by_anchor: dict[int, list[str]], report: Report):
    """Per spec line: at least one hex literal in the claim must appear in the union of
    all lines cited by that spec line's anchors (a line may carry several anchors)."""
    by_line: dict[int, list[int]] = {}
    for idx, a in enumerate(anchors):
        if idx in cited_by_anchor:
            by_line.setdefault(a.spec_line, []).append(idx)
    for spec_line, idxs in by_line.items():
        claim_hex = hex_set(anchors[idxs[0]].claim)
        if not claim_hex:
            continue
        cited_hex = set()
        for idx in idxs:
            cited_hex |= hex_set("\n".join(cited_by_anchor[idx]))
        if not (claim_hex & cited_hex):
            shown = ", ".join("0x" + h for h in sorted(claim_hex)[:4])
            where = "; ".join(anchors[idx].raw for idx in idxs)
            report.add("warn", spec_line,
                       f"none of the claim's hex literals ({shown}) appear in the lines cited by "
                       f"this line ({where}) — wrong value, or cite the offset definition too?")


def check_drift(anchor: Anchor, pinned: Repo, new: Repo, report: Report):
    old_blob, new_blob = pinned.blob(anchor.path), new.blob(anchor.path)
    if new_blob is None:
        report.stale.append((anchor.spec_line, anchor.raw))
        report.add("error", anchor.spec_line,
                   f"{anchor.path} is gone at {new.rev}", anchor.raw)
        return
    if old_blob == new_blob:
        return
    old_lines, new_lines = pinned.lines(anchor.path), new.lines(anchor.path)
    if old_lines is None or new_lines is None:
        return
    old_cited = old_lines[anchor.l1 - 1: anchor.l2]
    new_cited = new_lines[anchor.l1 - 1: anchor.l2]
    if old_cited == new_cited:
        return  # file changed elsewhere; this range is byte-identical
    # Same text may simply have moved: look for it elsewhere in the new file.
    moved_to = None
    if old_cited and any(l.strip() for l in old_cited):
        n = len(old_cited)
        for start in range(0, max(len(new_lines) - n + 1, 0)):
            if new_lines[start: start + n] == old_cited:
                moved_to = start + 1
                break
    if moved_to is not None:
        new_l2 = moved_to + (anchor.l2 - anchor.l1)
        span = f"{moved_to}-{new_l2}" if new_l2 != moved_to else f"{moved_to}"
        new_raw = f"{anchor.path}:{span}" + (f" ({anchor.symbol})" if anchor.symbol else "")
        report.moves.append((anchor.spec_line, anchor.raw, new_raw))
        report.add("warn", anchor.spec_line,
                   f"cited text moved: {anchor.path}:{anchor.l1}-{anchor.l2} is now "
                   f"{span} at {new.rev} (content unchanged; update the line numbers)",
                   anchor.raw)
        return
    hint = ""
    if anchor.symbol:
        at = find_symbol(new_lines, anchor.symbol, 1, len(new_lines))
        hint = f"; symbol {anchor.symbol!r} now at line {at}" if at else \
               f"; symbol {anchor.symbol!r} no longer in file"
    report.stale.append((anchor.spec_line, anchor.raw))
    report.add("error", anchor.spec_line,
               f"cited text changed: {anchor.path}:{anchor.l1}-{anchor.l2} differs at "
               f"{new.rev}{hint} — re-verify this claim", anchor.raw)


# --------------------------------------------------------------------------- output


def render_show(anchors: list[Anchor], repos: dict[str, Repo], out):
    for a in anchors:
        repo = repos.get(a.kind)
        print(f"--- spec L{a.spec_line}: {a.claim[:240]}", file=out)
        print(f"    [{a.kind}: {a.raw}]", file=out)
        if repo is None:
            print("    (repository for this anchor kind not given)", file=out)
            continue
        file_lines = repo.lines(a.path)
        if file_lines is None or a.l2 > len(file_lines):
            print("    (unresolvable — see findings)", file=out)
            continue
        for n in range(a.l1, a.l2 + 1):
            print(f"    {n:6d} | {file_lines[n - 1]}", file=out)
        print(file=out)


def rewrite_spec(spec_path: str, text: str, report: Report, new_rev: str) -> int:
    """Apply moves, stale markers and the new Source pin to the spec file. Returns edits made."""
    lines = text.split("\n")
    edits = 0
    for spec_line, old_raw, new_raw in report.moves:
        idx = spec_line - 1
        if old_raw in lines[idx]:
            lines[idx] = lines[idx].replace(old_raw, new_raw, 1)
            edits += 1
    old_rev = report.pins.get("source", {}).get("rev", "?")
    for spec_line, raw in report.stale:
        idx = spec_line - 1
        tag_re = re.compile(r"(\[(?:src|impl):[^\]]*" + re.escape(raw) + r"[^\]]*\])")
        new_line, n = tag_re.subn(r"\1 [stale: was " + old_rev + "]", lines[idx], count=1)
        if n:
            lines[idx] = new_line
            edits += 1
    for idx, line in enumerate(lines):
        m = PIN_RE.match(line.strip())
        if m and m.group(1) in ("Source", "Impl"):
            lines[idx] = f"{m.group(1)} pin: {m['name']}@{new_rev}"
            edits += 1
    Path(spec_path).write_text("\n".join(lines), encoding="utf-8")
    return edits


def render_report(report: Report, out):
    print(f"spec: {report.spec}", file=out)
    for kind, pin in sorted(report.pins.items()):
        print(f"{kind} pin: {pin['name']}@{pin['rev']}", file=out)
    print(f"anchors: {report.anchors}  doc tags: {report.doc_tags}", file=out)
    errors = report.errors
    warns = [f for f in report.findings if f.level == "warn"]
    for f in sorted(report.findings, key=lambda f: (f.level != "error", f.spec_line)):
        tag = "ERROR" if f.level == "error" else "warn "
        print(f"{tag} L{f.spec_line}: {f.message}", file=out)
    print(f"result: {'FAIL' if errors else 'PASS'} "
          f"({len(errors)} errors, {len(warns)} warnings)", file=out)


# --------------------------------------------------------------------------- main


def repo_arg(value: str | None, pin: dict | None, label: str) -> Repo | None:
    """Parse --repo PATH[@REV]; REV defaults to the spec's pin."""
    if value is None:
        return None
    path, _, rev = value.partition("@")
    if not rev:
        if pin is None:
            raise SystemExit(f"error: --{label} has no @rev and the spec states no "
                             f"'{label.capitalize()} pin:' line")
        rev = pin["rev"]
    return Repo(path, rev)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("spec", help="path to the spec markdown file")
    ap.add_argument("--repo", "--impl-repo", metavar="PATH[@REV]",
                    help="source repository for [src:]/[impl:] anchors (REV defaults to the "
                         "spec's Source/Impl pin)")
    ap.add_argument("--target-repo", "--ref-repo", metavar="PATH[@REV]",
                    help="target-OS repository for [tgt:]/[ref:] anchors (REV defaults to the "
                         "Target/Ref pin)")
    ap.add_argument("--show", action="store_true",
                    help="print each claim with its cited source lines (review sheet)")
    ap.add_argument("--drift", metavar="REV",
                    help="compare [src:] anchors at the pin against REV in the source repo")
    ap.add_argument("--rewrite", action="store_true",
                    help="with --drift: rewrite moved anchors and the Source pin in the spec file")
    ap.add_argument("--strict", action="store_true",
                    help="every table row and list item must carry a tag, not just hex/bit facts")
    ap.add_argument("--json", action="store_true", help="emit the report as JSON")
    ap.add_argument("--output", "-o", help="write the report here instead of stdout")
    args = ap.parse_args(argv)

    try:
        text = Path(args.spec).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    report = Report(spec=args.spec)
    anchors = parse_spec(text, report, args.strict)

    try:
        repos: dict[str, Repo] = {}
        r = repo_arg(args.repo, report.pins.get("source"), "repo")
        if r:
            repos["src"] = r
        t = repo_arg(args.target_repo, report.pins.get("target"), "target-repo")
        if t:
            repos["tgt"] = t
        drift_repo = Repo(repos["src"].path, args.drift) if args.drift and "src" in repos else None
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    if args.drift and "src" not in repos:
        print("error: --drift needs --repo", file=sys.stderr)
        return 2
    if args.rewrite and not args.drift:
        print("error: --rewrite needs --drift REV", file=sys.stderr)
        return 2

    for kind, pin_key in (("src", "source"), ("tgt", "target")):
        pin = report.pins.get(pin_key)
        repo = repos.get(kind)
        if repo and pin and not repo.full_rev.startswith(pin["rev"]) and pin["rev"] != repo.rev:
            report.add("warn", 0, f"{pin_key} pin in spec is {pin['rev']} but checking at "
                                  f"{repo.rev} ({repo.full_rev[:12]})")
    for kind in ("src", "tgt"):
        if kind not in repos and any(a.kind == kind for a in anchors):
            n = sum(1 for a in anchors if a.kind == kind)
            report.add("warn", 0, f"{n} [{kind}:] anchors not resolved (no repository given)")

    cited_by_anchor: dict[int, list[str]] = {}
    for idx, a in enumerate(anchors):
        repo = repos.get(a.kind)
        if repo is None:
            continue
        cited = resolve(a, repo, report)
        if cited is not None:
            cited_by_anchor[idx] = cited
            if drift_repo is not None and a.kind == "src":
                check_drift(a, repo, drift_repo, report)
    check_hex_consistency(anchors, cited_by_anchor, report)

    if args.rewrite:
        n = rewrite_spec(args.spec, text, report, args.drift)
        report.add("warn", 0, f"made {n} edits in {args.spec}: pin is now {args.drift}; "
                              f"{len(report.stale)} anchors marked [stale:] for re-verification")

    out = open(args.output, "w", encoding="utf-8") if args.output else sys.stdout
    try:
        if args.show:
            render_show(anchors, repos, out)
        if args.json:
            payload = asdict(report)
            payload["result"] = "FAIL" if report.errors else "PASS"
            json.dump(payload, out, indent=2)
            print(file=out)
        else:
            render_report(report, out)
    finally:
        if out is not sys.stdout:
            out.close()
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
