#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Print Codex's rate-limit usage from its own session logs.

Codex records the current rate limits in each session's rollout log
($CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl, default ~/.codex). This script
compares usage-event timestamps across logs, so it needs no token or network.
The output gives the age of the usage event, never the log's modification time.

Usage:  python3 codex_usage.py [--json]
Exit code: 0 ok, 1 no timestamped rate-limit record found.
"""

import datetime
import glob
import json
import os
import sys
import time


def sessions_dir():
    """Resolve the active Codex state directory at call time."""
    home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    return os.path.join(os.path.expanduser(home), "sessions")


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


def record_timestamp(obj):
    """Return an aware ISO-8601 event timestamp, or None when age is unknown."""
    value = obj.get("timestamp") if isinstance(obj, dict) else None
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.timestamp()
    except (ValueError, OverflowError):
        return None


def newest_record():
    """Find the newest dated usage event across all logs, ignoring file mtimes."""
    files = glob.glob(os.path.join(sessions_dir(), "*", "*", "*", "*.jsonl"))
    newest = None
    newest_timestamp = float("-inf")
    for path in sorted(files):
        try:
            with open(path, encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    if '"rate_limits"' not in line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    found = find_rate_limits(obj)
                    timestamp = record_timestamp(obj)
                    if not found or timestamp is None:
                        continue
                    if timestamp >= newest_timestamp:
                        newest = path, timestamp, found
                        newest_timestamp = timestamp
        except FileNotFoundError:
            continue
    return newest


def window_name(minutes):
    if minutes == 10080:
        return "weekly"
    if minutes == 300:
        return "5-hour"
    return f"{minutes}-minute"


def main():
    record = newest_record()
    if record is None:
        print("no timestamped Codex rate-limit record found", file=sys.stderr)
        sys.exit(1)
    _, timestamp, limits = record
    age_min = int((time.time() - timestamp) / 60)
    windows = []
    for key in ("primary", "secondary"):
        w = limits.get(key)
        if isinstance(w, dict):
            windows.append(
                {
                    "window": window_name(w.get("window_minutes")),
                    "used_percent": w.get("used_percent"),
                    "resets_at": time.strftime(
                        "%Y-%m-%d %H:%M %Z", time.localtime(w.get("resets_at", 0))
                    ),
                }
            )
    if "--json" in sys.argv:
        print(
            json.dumps(
                {
                    "age_minutes": age_min,
                    "plan_type": limits.get("plan_type"),
                    "limit_reached": limits.get("rate_limit_reached_type"),
                    "windows": windows,
                },
                indent=2,
            )
        )
    else:
        for w in windows:
            name = w["window"]
            used = w["used_percent"]
            reset = w["resets_at"]
            print(
                f"Codex {name}: {used}% used, "
                f"resets {reset}  [log, {age_min} min old]"
            )
        if limits.get("rate_limit_reached_type"):
            print("limit reached:", limits["rate_limit_reached_type"])
    sys.exit(0)


if __name__ == "__main__":
    main()
