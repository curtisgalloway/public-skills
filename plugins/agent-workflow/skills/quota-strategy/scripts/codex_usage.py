#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Print Codex's rate-limit usage from its own session logs.

Codex records the current rate limits in each session's rollout log
(~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl) with every response. This script
reads the newest record, so it needs no token and makes no network call. The
reading is only as fresh as the last Codex run; the output gives its age.

Usage:  python3 codex_usage.py [--json]
Exit code: 0 ok, 1 no rate-limit record found.
"""
import glob
import json
import os
import sys
import time

SESSIONS = os.path.join(os.path.expanduser("~"), ".codex", "sessions")


def find_rate_limits(obj):
    """Return the first dict under a "rate_limits" key, searching depth-first."""
    if isinstance(obj, dict):
        value = obj.get("rate_limits")
        if isinstance(value, dict):
            return value
        children = obj.values()
    elif isinstance(obj, list):
        children = obj
    else:
        return None
    for child in children:
        found = find_rate_limits(child)
        if found is not None:
            return found
    return None


def newest_record():
    files = glob.glob(os.path.join(SESSIONS, "*", "*", "*", "*.jsonl"))
    for path in sorted(files, key=os.path.getmtime, reverse=True):
        last = None
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                if '"rate_limits"' not in line:
                    continue
                try:
                    found = find_rate_limits(json.loads(line))
                except json.JSONDecodeError:
                    continue
                if found is not None:
                    last = found
        if last is not None:
            return path, os.path.getmtime(path), last
    return None


def window_name(minutes):
    if minutes == 10080:
        return "weekly"
    if minutes == 300:
        return "5-hour"
    return f"{minutes}-minute"


def main():
    record = newest_record()
    if record is None:
        print("no Codex rate-limit record found", file=sys.stderr)
        sys.exit(1)
    path, mtime, limits = record
    age_min = int((time.time() - mtime) / 60)
    windows = []
    for key in ("primary", "secondary"):
        w = limits.get(key)
        if isinstance(w, dict):
            windows.append({
                "window": window_name(w.get("window_minutes")),
                "used_percent": w.get("used_percent"),
                "resets_at": time.strftime(
                    "%Y-%m-%d %H:%M %Z", time.localtime(w.get("resets_at", 0))),
            })
    if "--json" in sys.argv:
        print(json.dumps({
            "age_minutes": age_min,
            "plan_type": limits.get("plan_type"),
            "limit_reached": limits.get("rate_limit_reached_type"),
            "windows": windows,
        }, indent=2))
    else:
        for w in windows:
            print(f"Codex {w['window']}: {w['used_percent']}% used, "
                  f"resets {w['resets_at']}  [log, {age_min} min old]")
        if limits.get("rate_limit_reached_type"):
            print(f"limit reached: {limits['rate_limit_reached_type']}")
    sys.exit(0)


if __name__ == "__main__":
    main()
