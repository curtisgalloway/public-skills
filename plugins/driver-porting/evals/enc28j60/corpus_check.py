#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check the ENC28J60 pilot corpus manifest against the sources it pins.

"Frozen" is only a claim until something re-fetches the sources and compares hashes. This does
that: it re-downloads each pinned driver file at the pinned commit and each pinned document
edition at its recorded url, and reports any whose sha256 no longer matches.

A mismatch is not automatically a corrupted manifest. A vendor serving a new edition under a url
that does not name the edition looks exactly like drift, and that is the case worth catching: it
means the document a ledger row was authored from is no longer the document at that address.

Exit codes:
  0  every pinned source matches
  1  at least one source drifted (hash mismatch)
  2  usage error, or the manifest is unreadable
  3  a source could not be reached, and nothing drifted among those that could
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

RAW = "https://raw.githubusercontent.com/torvalds/linux/{commit}/{path}"
TIMEOUT = 60


def load_manifest(path: Path) -> dict:
    """Read the pins without a YAML dependency.

    Line-oriented on purpose: the fields are read under the section heading they appear beneath,
    so cosmetic alignment inside an entry cannot change what is checked. A heading or field that
    stops matching raises rather than silently checking nothing.
    """
    text = path.read_text()
    commit = re.search(r"^  commit: ([0-9a-f]{40})$", text, re.M)
    if not commit:
        raise ValueError("no driver commit pin found")

    files, documents = [], []
    section = None
    url_pattern = {}
    pending = {}
    for line in text.splitlines():
        if re.match(r"^  (datasheet|errata):\s*$", line):
            section = line.strip().rstrip(":")
        elif re.match(r"^[a-z_]+:", line):
            section = None

        m = re.match(r"^    url_pattern: (\S+)$", line)
        if m and section:
            url_pattern[section] = m.group(1)

        m = re.match(r"^    - path: (\S+)$", line)
        if m:
            pending = {"path": m.group(1)}
        m = re.match(r"^      bytes: (\d+)$", line)
        if m and pending:
            pending["bytes"] = int(m.group(1))
        m = re.match(r"^      sha256: ([0-9a-f]{64})$", line)
        if m and pending:
            pending["sha256"] = m.group(1)
            files.append(pending)
            pending = {}

        m = re.match(r"^      - \{rev: ([A-Z]),.*?bytes: (\d+),\s*sha256: ([0-9a-f]{64})", line)
        if m:
            if not section:
                raise ValueError(f"edition outside a document section: {line.strip()[:60]}")
            documents.append(
                {
                    "rev": m.group(1),
                    "bytes": int(m.group(2)),
                    "sha256": m.group(3),
                    "kind": section,
                }
            )

    if not files:
        raise ValueError("no driver file pins found")
    missing = {d["kind"] for d in documents} - set(url_pattern)
    if missing:
        raise ValueError(f"no url_pattern for {', '.join(sorted(missing))}")
    for d in documents:
        d["url"] = url_pattern[d["kind"]].replace("<rev>", d["rev"].lower())
    return {"commit": commit.group(1), "files": files, "documents": documents}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "corpus-check/1"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.read()


def check(manifest: dict) -> list[dict]:
    results = []
    for f in manifest["files"]:
        url = RAW.format(commit=manifest["commit"], path=f["path"])
        item = {"name": f["path"], "expected": f["sha256"]}
        try:
            blob = fetch(url)
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            item.update(status="unreachable", detail=str(exc))
        else:
            got = hashlib.sha256(blob).hexdigest()
            item.update(
                status="ok" if got == f["sha256"] else "drift",
                actual=got,
                bytes=len(blob),
                expected_bytes=f["bytes"],
            )
        results.append(item)
    for d in manifest["documents"]:
        item = {"name": f"{d['kind']} rev {d['rev']}", "expected": d["sha256"], "url": d["url"]}
        try:
            blob = fetch(d["url"])
        except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
            item.update(status="unreachable", detail=str(exc))
        else:
            got = hashlib.sha256(blob).hexdigest()
            item.update(
                status="ok" if got == d["sha256"] else "drift",
                actual=got,
                bytes=len(blob),
                expected_bytes=d["bytes"],
            )
        results.append(item)
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "manifest",
        nargs="?",
        type=Path,
        default=Path(__file__).with_name("corpus.yaml"),
        help="path to corpus.yaml (default: beside this script)",
    )
    parser.add_argument("--json", action="store_true", help="machine-readable output on stdout")
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
    except (OSError, ValueError) as exc:
        print(f"cannot read manifest: {exc}", file=sys.stderr)
        return 2

    results = check(manifest)
    drift = [r for r in results if r["status"] == "drift"]
    unreachable = [r for r in results if r["status"] == "unreachable"]

    if args.json:
        json.dump({"results": results, "drift": len(drift), "unreachable": len(unreachable)},
                  sys.stdout, indent=2)
        print()
    else:
        for r in results:
            if r["status"] == "ok":
                print(f"ok        {r['name']}")
            elif r["status"] == "drift":
                print(f"DRIFT     {r['name']}: expected {r['expected'][:16]}..., "
                      f"got {r['actual'][:16]}... ({r['expected_bytes']} -> {r['bytes']} bytes)")
            else:
                print(f"unreached {r['name']}: {r['detail']}")
        print(f"\n{len(results)} pinned sources, {len(drift)} drifted, "
              f"{len(unreachable)} unreachable")

    if drift:
        return 1
    if unreachable:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
