#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
"""
leak_scan.py - mechanical clean-room leak scanner (stdlib only).

Compares CANDIDATE documents (a clean-room spec, or newly written driver
code for the pre-merge output scan) against encumbered SOURCE files (the
spec's provenance map) for two things:

  1. Shared token runs: maximal matching sequences of >= --min-run tokens
     (case-insensitive) that contain >= --min-alpha non-numeric tokens.
     Register tables legitimately share numbers with the source, so
     pure-numeric overlap never triggers on its own.

  2. Identifier reuse: code-shaped identifiers (interior underscore or
     camelCase, length >= 4) that appear in both the sources and the
     candidate, minus a --whitelist of hardware/databook nomenclature.
     lowercase/camelCase hits are HIGH-SIGNAL (likely source-invented);
     ALL-CAPS hits are listed separately as whitelist candidates, since
     databook register/field names are often all-caps.

The report cites locations, lengths, and digests but NEVER prints matched
text from the sources. (Identifier names are printed: a bare name is
needed to act on the finding and is not protectable expression.)

Exit codes: 0 = no findings, 1 = findings, 2 = usage or I/O error.
"""

import argparse
import hashlib
import pathlib
import re
import sys

TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|0[xX][0-9A-Fa-f]+|\d+")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

SOURCE_EXTS = {".c", ".h", ".s", ".S", ".rs", ".dts", ".dtsi", ".inc", ".asm"}

# C/Rust keywords and ubiquitous type names: never interesting on their own.
STOPWORDS = {
    "if", "else", "for", "while", "return", "static", "const", "struct",
    "enum", "union", "void", "int", "char", "unsigned", "signed", "long",
    "short", "sizeof", "switch", "case", "break", "continue", "goto", "do",
    "volatile", "extern", "inline", "typedef", "default", "register",
    "true", "false", "null", "bool", "let", "mut", "impl", "match", "loop",
    "u8", "u16", "u32", "u64", "s8", "s16", "s32", "s64", "usize", "isize",
    "uint8_t", "uint16_t", "uint32_t", "uint64_t", "int8_t", "int16_t",
    "int32_t", "int64_t", "size_t", "ssize_t", "uintptr_t", "u_int",
    "__iomem", "__init", "__exit", "__user",
}


def die(msg):
    print(f"leak_scan: error: {msg}", file=sys.stderr)
    sys.exit(2)


def read_text(path):
    try:
        return pathlib.Path(path).read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        die(f"cannot read {path}: {e}")


def collect_sources(paths):
    """Expand files/dirs into a list of source files (dirs filtered by ext)."""
    out = []
    for p in paths:
        pp = pathlib.Path(p)
        if pp.is_dir():
            for f in sorted(pp.rglob("*")):
                if f.is_file() and f.suffix in SOURCE_EXTS:
                    out.append(f)
        elif pp.is_file():
            out.append(pp)
        else:
            die(f"source path not found: {p}")
    if not out:
        die("no source files found under --against paths")
    return out


def tokenize(text):
    """Return (tokens_lowercased, line_numbers) aligned lists."""
    toks, lines = [], []
    for ln, line in enumerate(text.splitlines(), 1):
        for m in TOKEN_RE.finditer(line):
            toks.append(m.group(0).lower())
            lines.append(ln)
    return toks, lines


def is_numericish(tok):
    return tok[:1].isdigit() or tok.startswith("0x")


def alpha_count(tokens):
    return sum(1 for t in tokens if not is_numericish(t))


def looks_code_shaped(ident):
    if len(ident) < 4:
        return False
    if "_" in ident.strip("_"):
        return True
    return re.search(r"[a-z][A-Z]", ident) is not None


def find_runs(cand_toks, src_toks, k):
    """Maximal matching token runs between candidate and one source token
    stream. `covered` (candidate indices already reported) is threaded by
    the caller so the same candidate passage isn't reported once per
    source file. Greedy; adequate for flagging, not for exact measure."""
    runs = []
    if len(cand_toks) < k or len(src_toks) < k:
        return runs
    index = {}
    for i in range(len(cand_toks) - k + 1):
        index.setdefault(hash(tuple(cand_toks[i:i + k])), []).append(i)
    j = 0
    while j <= len(src_toks) - k:
        advanced = False
        for i in index.get(hash(tuple(src_toks[j:j + k])), ()):
            if cand_toks[i:i + k] != src_toks[j:j + k]:
                continue
            if any((i + d) in find_runs.covered for d in range(k)):
                continue
            a, b = i, j
            while (a > 0 and b > 0 and (a - 1) not in find_runs.covered
                   and cand_toks[a - 1] == src_toks[b - 1]):
                a -= 1
                b -= 1
            ea, eb = i + k, j + k
            while (ea < len(cand_toks) and eb < len(src_toks)
                   and ea not in find_runs.covered
                   and cand_toks[ea] == src_toks[eb]):
                ea += 1
                eb += 1
            runs.append((a, ea, b, eb))
            find_runs.covered.update(range(a, ea))
            j = eb
            advanced = True
            break
        if not advanced:
            j += 1
    return runs


def scan_identifiers(text, restrict=None):
    """Map identifier -> sorted line numbers, filtered to code-shaped
    identifiers not in STOPWORDS (and, optionally, in `restrict`)."""
    found = {}
    for ln, line in enumerate(text.splitlines(), 1):
        for m in IDENT_RE.finditer(line):
            ident = m.group(0)
            if ident.lower() in STOPWORDS or not looks_code_shaped(ident):
                continue
            if restrict is not None and ident not in restrict:
                continue
            found.setdefault(ident, set()).add(ln)
    return {k: sorted(v) for k, v in found.items()}


def main():
    ap = argparse.ArgumentParser(
        description="Mechanical clean-room leak scanner: shared token runs "
                    "and identifier reuse between candidate docs and "
                    "encumbered source files.")
    ap.add_argument("candidate", nargs="+",
                    help="spec file(s) or new driver source file(s) to check")
    ap.add_argument("--against", nargs="+", required=True, metavar="PATH",
                    help="encumbered source files or directories "
                         "(the provenance map, at the pinned commit)")
    ap.add_argument("--whitelist", metavar="FILE",
                    help="hardware/databook nomenclature, one identifier "
                         "per line, '#' comments (case-insensitive)")
    ap.add_argument("--min-run", type=int, default=10,
                    help="min matching-run length in tokens (default 10)")
    ap.add_argument("--min-alpha", type=int, default=5,
                    help="min non-numeric tokens in a flagged run (default 5)")
    ap.add_argument("--k", type=int, default=8,
                    help="shingle seed size in tokens (default 8)")
    ap.add_argument("--max-report", type=int, default=100,
                    help="cap on reported runs per candidate (default 100)")
    args = ap.parse_args()
    if args.k > args.min_run:
        die("--k must be <= --min-run")

    whitelist = set()
    if args.whitelist:
        for line in read_text(args.whitelist).splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                whitelist.add(line.lower())

    sources = collect_sources(args.against)
    src_data = []          # (path, tokens, line_numbers)
    src_idents = {}        # identifier -> first source path seen in
    for sp in sources:
        text = read_text(sp)
        toks, lines = tokenize(text)
        src_data.append((sp, toks, lines))
        for ident in scan_identifiers(text):
            src_idents.setdefault(ident, str(sp))

    print("leak_scan report")
    print(f"  candidates : {', '.join(args.candidate)}")
    print(f"  against    : {len(sources)} source file(s)")
    print(f"  params     : min-run={args.min_run} min-alpha={args.min_alpha} "
          f"k={args.k} whitelist={len(whitelist)} entries")

    total_runs = 0
    total_high = 0
    total_caps = 0

    for cand in args.candidate:
        text = read_text(cand)
        cand_toks, cand_lines = tokenize(text)
        print(f"\n== {cand} ==")

        # --- Check 1: shared token runs ---
        find_runs.covered = set()
        flagged = []
        for sp, stoks, slines in src_data:
            for a, ea, b, eb in find_runs(cand_toks, stoks, args.k):
                n = ea - a
                na = alpha_count(cand_toks[a:ea])
                if n >= args.min_run and na >= args.min_alpha:
                    digest = hashlib.sha1(
                        " ".join(cand_toks[a:ea]).encode()).hexdigest()[:10]
                    flagged.append((n, na, cand_lines[a], cand_lines[ea - 1],
                                    str(sp), slines[b], slines[eb - 1], digest))
        flagged.sort(reverse=True)
        total_runs += len(flagged)
        print(f"[runs] {len(flagged)} shared run(s) >= {args.min_run} tokens "
              f"with >= {args.min_alpha} non-numeric tokens")
        for n, na, c1, c2, sp, s1, s2, dg in flagged[:args.max_report]:
            print(f"  - {n} tokens ({na} non-numeric)  candidate L{c1}-L{c2}"
                  f"  <->  {sp} L{s1}-L{s2}  [sha1:{dg}]")
        if len(flagged) > args.max_report:
            print(f"  ... {len(flagged) - args.max_report} more suppressed "
                  f"(--max-report)")

        # --- Check 2: identifier reuse ---
        cand_idents = scan_identifiers(text, restrict=src_idents)
        high, caps = [], []
        for ident, lines in sorted(cand_idents.items()):
            if ident.lower() in whitelist:
                continue
            entry = (ident, src_idents[ident], lines)
            (caps if ident.isupper() else high).append(entry)
        total_high += len(high)
        total_caps += len(caps)
        print(f"[idents] {len(high)} high-signal (lowercase/camelCase) "
              f"identifier(s) shared with source")
        for ident, sp, lines in high:
            loc = ",".join(f"L{n}" for n in lines[:5])
            more = f" +{len(lines) - 5}" if len(lines) > 5 else ""
            print(f"  - {ident}  (in {sp})  candidate {loc}{more}")
        print(f"[idents] {len(caps)} ALL-CAPS identifier(s) shared with "
              f"source - review: databook nomenclature belongs in the "
              f"whitelist, anything else is a failure")
        for ident, sp, lines in caps:
            loc = ",".join(f"L{n}" for n in lines[:5])
            more = f" +{len(lines) - 5}" if len(lines) > 5 else ""
            print(f"  - {ident}  (in {sp})  candidate {loc}{more}")

    findings = total_runs + total_high + total_caps
    print(f"\nsummary: {total_runs} run(s), {total_high} high-signal "
          f"identifier(s), {total_caps} all-caps identifier(s) to review")
    print("verdict:", "FINDINGS - review required" if findings else "clean")
    sys.exit(1 if findings else 0)


if __name__ == "__main__":
    main()
