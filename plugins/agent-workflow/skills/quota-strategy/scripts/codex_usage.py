#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Print Codex rate-limit pools using the app server or timestamped rollout logs.

Usage:  python3 codex_usage.py [--offline] [--json]
Exit code: 0 main pool observed, 1 main pool unavailable.
"""

import argparse
import datetime
import glob
import io
import json
import math
import os
import queue
import subprocess
import sys
import threading
import time

APP_SERVER_COMMAND = ("codex", "app-server")
LIVE_TIMEOUT_SECONDS = 5
MAIN_POOL = "codex"
MAX_AGE_SECONDS = 15 * 60


def app_server_rate_limits():
    """Complete the stdio handshake and read account limits within one deadline."""
    deadline = time.monotonic() + LIVE_TIMEOUT_SECONDS
    replies = queue.Queue()

    def collect(stream):
        try:
            with io.BufferedReader(stream) as lines:
                for line in lines:
                    try:
                        msg = json.loads(line)
                    except ValueError:
                        continue
                    if (isinstance(msg, dict) and "method" not in msg
                            and type(msg.get("id")) is int and msg["id"] in (0, 1)):
                        replies.put(msg)
        except (OSError, ValueError):
            pass
        finally:
            replies.put(None)

    def result(request_id):
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return None
            reply = replies.get(timeout=remaining)
            if reply is None:
                return None
            if reply["id"] == request_id:
                return reply.get("result")

    def send(stream, message):
        stream.write((json.dumps(message) + "\n").encode("utf-8"))

    try:
        with subprocess.Popen(
            APP_SERVER_COMMAND, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, bufsize=0,
        ) as server:
            # Keep buffering in the reader so process cleanup never waits on its read.
            reader = threading.Thread(target=collect, args=(server.stdout,), daemon=True)
            reader.start()
            reading = None
            try:
                send(server.stdin, {
                    "id": 0,
                    "method": "initialize",
                    "params": {"clientInfo": {
                        "name": "quota_strategy",
                        "version": "1",
                    }},
                })
                if not isinstance(result(0), dict):
                    return None
                send(server.stdin, {"method": "initialized", "params": {}})
                send(server.stdin, {"id": 1, "method": "account/rateLimits/read"})
                reading = result(1)
                return reading
            finally:
                if isinstance(reading, dict):
                    server.stdin.close()
                    try:
                        server.wait(timeout=0.2)
                    except subprocess.TimeoutExpired:
                        server.kill()
                else:
                    server.kill()
                reader.join(timeout=0.1)
    except (OSError, queue.Empty):
        return None


def sessions_dir():
    """Resolve the active Codex state directory at call time."""
    home = os.environ.get("CODEX_HOME") or os.path.expanduser("~/.codex")
    return os.path.join(os.path.expanduser(home), "sessions")


def rollout_rate_limits(event):
    """Read telemetry from a Codex token-count event."""
    if not isinstance(event, dict) or event.get("type") != "event_msg":
        return None
    payload = event.get("payload")
    if not isinstance(payload, dict) or payload.get("type") != "token_count":
        return None
    return payload.get("rate_limits")


def record_timestamp(obj):
    """Return an aware ISO-8601 event timestamp, or None when age is unknown."""
    value = obj.get("timestamp") if isinstance(obj, dict) else None
    if not isinstance(value, str):
        return None
    try:
        stamp = datetime.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if stamp.tzinfo is None:
            return None
        return stamp.astimezone(datetime.timezone.utc).timestamp()
    except (ValueError, OverflowError, OSError):
        return None


def pool_id(limits, id_key, name_key, legacy):
    if not isinstance(limits, dict):
        return None
    identifier = limits.get(id_key)
    if legacy and identifier is None and not limits.get(name_key):
        # Older single-pool snapshots omitted the ID.
        return MAIN_POOL
    return identifier if isinstance(identifier, str) and identifier else None


def has_reading(limits, percent_key, reached_key):
    if not isinstance(limits, dict):
        return False
    windows = (limits.get("primary"), limits.get("secondary"))
    return bool(limits.get(reached_key)) or any(
        isinstance(window, dict) and nonnegative_number(window.get(percent_key))
        for window in windows
    )


def newest_records():
    """Find the newest dated snapshot for each pool, ignoring file mtimes."""
    files = glob.glob(os.path.join(sessions_dir(), "*", "*", "*", "rollout-*.jsonl"))
    newest = {}
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
                    limits = rollout_rate_limits(obj)
                    timestamp = record_timestamp(obj)
                    identifier = pool_id(limits, "limit_id", "limit_name", legacy=True)
                    if identifier is None or timestamp is None:
                        continue
                    if not has_reading(limits, "used_percent", "rate_limit_reached_type"):
                        continue
                    if identifier not in newest or timestamp >= newest[identifier][0]:
                        newest[identifier] = timestamp, limits
        except OSError:
            continue
    return newest


def live_records(result, timestamp):
    """Preserve each ID in the documented multi-pool response."""
    if not isinstance(result, dict):
        return {}
    pools = result.get("rateLimitsByLimitId")
    records = {}
    if isinstance(pools, dict):
        for identifier, limits in pools.items():
            if not identifier or not has_reading(limits, "usedPercent", "rateLimitReachedType"):
                continue
            if limits.get("limitId") in (None, identifier):
                records[identifier] = timestamp, limits
    legacy = result.get("rateLimits")
    identifier = pool_id(legacy, "limitId", "limitName", legacy=pools is None)
    if identifier and has_reading(legacy, "usedPercent", "rateLimitReachedType"):
        records.setdefault(identifier, (timestamp, legacy))
    return records


def window_name(minutes):
    if minutes == 10080:
        return "weekly"
    if minutes == 300:
        return "5-hour"
    if type(minutes) is int and minutes > 0:
        return f"{minutes}-minute"
    return "unknown"


def nonnegative_number(value):
    return (type(value) is int or (isinstance(value, float) and math.isfinite(value))) and value >= 0


def render_pool(record, source, now):
    if record is None:
        return {
            "status": "unknown", "reason": "pool_missing", "source": None,
            "observed_at": None, "age_minutes": None, "limit_name": None,
            "plan_type": None, "limit_reached": None, "windows": [],
        }

    timestamp, limits = record
    elapsed = now - timestamp
    if elapsed < 0:
        reason = "future_timestamp"
    elif elapsed > MAX_AGE_SECONDS:
        reason = "stale"
    else:
        reason = None
    live = source == "live"
    windows = []
    for key in ("primary", "secondary"):
        window = limits.get(key)
        if not isinstance(window, dict):
            continue
        minutes = window.get("windowDurationMins" if live else "window_minutes")
        percent = window.get("usedPercent" if live else "used_percent")
        reset = window.get("resetsAt" if live else "resets_at")
        reset_text = None
        if type(reset) is int and reset > 0:
            try:
                reset_text = time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(reset))
            except (ValueError, OverflowError, OSError):
                pass
        name = window_name(minutes)
        percent = percent if nonnegative_number(percent) else None
        windows.append({"window": name, "used_percent": percent, "resets_at": reset_text})
        if reason is None:
            if name == "unknown" or percent is None or reset_text is None:
                reason = "missing_window_fields"
            elif reset <= now:
                reason = "reset_passed"
    if not windows and reason is None:
        reason = "missing_windows"
    return {
        "status": "unknown" if reason else "known",
        "reason": reason,
        "source": source,
        "observed_at": datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat(),
        "age_minutes": int(elapsed // 60) if elapsed >= 0 else None,
        "limit_name": limits.get("limitName" if live else "limit_name"),
        "plan_type": limits.get("planType" if live else "plan_type"),
        "limit_reached": limits.get("rateLimitReachedType" if live else "rate_limit_reached_type"),
        "windows": windows,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--offline", action="store_true", help="read local logs only")
    args = parser.parse_args(argv)

    records = {}
    if not args.offline:
        result = app_server_rate_limits()
        records = live_records(result, time.time())
    source = "live" if records else "log"
    if source == "log":
        records = newest_records()
    now = time.time()
    identifiers = [MAIN_POOL, *sorted(records.keys() - {MAIN_POOL})]
    pools = {identifier: render_pool(records.get(identifier), source, now)
             for identifier in identifiers}
    main_pool = pools[MAIN_POOL]
    if args.json:
        # Keep the original fields scoped to the main pool for existing callers.
        summary = {key: main_pool[key] for key in (
            "age_minutes", "plan_type", "limit_reached", "windows"
        )}
        print(json.dumps({**summary, "pools": pools}, indent=2))
    else:
        for identifier, pool in pools.items():
            label = "Codex" if identifier == MAIN_POOL else f"Codex [{identifier}]"
            age = pool["age_minutes"]
            detail = f"{pool['source']}, {age} min old" if age is not None else pool["source"]
            for window in pool["windows"]:
                used = window["used_percent"]
                usage = "unknown usage" if used is None else f"{used}% used"
                reset = window["resets_at"] or "unknown"
                print(f"{label} {window['window']}: {usage}, resets {reset}  [{detail}]")
            if pool["limit_reached"]:
                prefix = "" if identifier == MAIN_POOL else f"{label} "
                print(f"{prefix}limit reached: {pool['limit_reached']}")
            if pool["status"] == "unknown":
                print(f"{label} capacity unknown ({pool['reason'].replace('_', ' ')})")
    return 0 if MAIN_POOL in records else 1


if __name__ == "__main__":
    sys.exit(main())
