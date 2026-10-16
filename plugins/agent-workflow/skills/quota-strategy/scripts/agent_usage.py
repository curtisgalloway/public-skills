#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Sum token usage per day and model from Codex, agy and Muse session logs.

Each CLI keeps its own record of what every model call consumed; nothing here calls a
model or a provider. Optionally (--vertex) it also asks Google Cloud Monitoring for a
project's Vertex AI token counts, the provider-side view of metered Gemini traffic.

  codex  $CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl (default ~/.codex): the
         running total in each token_count event; a day gets the increase in that total
  agy    ~/.gemini/antigravity-cli/conversations/<id>.db (SQLite, protobuf rows): one
         gen_metadata row per model call; dated by the conversation's last step
  muse   ~/.local/share/muse/sessions/YYYY/MM/DD/<session>/session.jsonl and each
         subagent/*/session.jsonl: one usage record per model call
  vertex Cloud Monitoring aiplatform.googleapis.com/publisher/online_serving/token_count
         for the project named, via `gcloud auth print-access-token`

The agy and Muse formats are undocumented and were decoded from live runs (agy 1.2.x,
Muse Code 1.4.9, 2026-10). A source whose format has moved reports zero rows plus a
warning on stderr rather than a wrong number.

Usage:  python3 agent_usage.py [--days N] [--source codex|agy|muse ...]
                               [--vertex PROJECT] [--json]
Exit code: 0 ok, 1 no usage found in the window, 2 usage error, 3 --vertex failed.
"""

import argparse
import collections
import datetime
import glob
import json
import os
import sqlite3
import subprocess
import sys
import urllib.parse
import urllib.request

FIELDS = ("input", "cached", "output", "reasoning")
SOURCES = ("codex", "agy", "muse")


def warn(text):
    print("agent_usage: " + text, file=sys.stderr)


def day_of(seconds):
    return datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc).date().isoformat()


class Totals:
    """Token sums keyed by (source, day, model)."""

    def __init__(self):
        self.rows = collections.defaultdict(lambda: dict.fromkeys(FIELDS + ("calls",), 0))

    def add(self, source, day, model, calls=1, **tokens):
        row = self.rows[(source, day, model or "?")]
        row["calls"] += calls
        for name in FIELDS:
            row[name] += int(tokens.get(name) or 0)


def lines(path):
    """Read a log's lines, or warn and yield none: CLIs rotate logs while we read."""
    try:
        with open(path, encoding="utf-8", errors="replace") as stream:
            return stream.readlines()
    except OSError as exc:
        warn("skipped %s: %s" % (path, exc))
        return []


# --- Codex -----------------------------------------------------------------------------


def codex(totals, since):
    home = os.path.expanduser(os.environ.get("CODEX_HOME") or "~/.codex")
    for path in sorted(glob.glob(os.path.join(home, "sessions", "*", "*", "*", "*.jsonl"))):
        model, previous = None, dict.fromkeys(FIELDS, 0)
        for line in lines(path):
            if '"turn_context"' not in line and '"token_count"' not in line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            payload = event.get("payload") or {}
            if event.get("type") == "turn_context":
                model = payload.get("model") or model
                continue
            usage = ((payload.get("info") or {}).get("total_token_usage")
                     if payload.get("type") == "token_count" else None)
            if not isinstance(usage, dict):
                continue
            current = {"input": usage.get("input_tokens", 0),
                       "cached": usage.get("cached_input_tokens", 0),
                       "output": usage.get("output_tokens", 0),
                       "reasoning": usage.get("reasoning_output_tokens", 0)}
            delta = {k: current[k] - previous[k] for k in FIELDS}
            previous = current
            if not any(delta.values()) or min(delta.values()) < 0:
                continue
            try:
                parsed = datetime.datetime.fromisoformat(
                    event["timestamp"].replace("Z", "+00:00"))
            except (KeyError, AttributeError, ValueError):
                continue
            if parsed.tzinfo is None:
                continue  # a local-time stamp cannot be placed on a UTC day
            if parsed.timestamp() >= since:
                totals.add("codex", day_of(parsed.timestamp()), model, **delta)


# --- agy -------------------------------------------------------------------------------


def varint(data, i):
    value = shift = 0
    while True:
        byte = data[i]
        i += 1
        value |= (byte & 0x7F) << shift
        shift += 7
        if byte < 0x80:
            return value, i


def fields(data):
    """Yield (number, value) for one protobuf message; value is int or bytes."""
    i = 0
    while i < len(data):
        key, i = varint(data, i)
        number, wire = key >> 3, key & 7
        if wire == 0:
            value, i = varint(data, i)
        elif wire == 2:
            size, i = varint(data, i)
            value, i = data[i:i + size], i + size
        elif wire == 1:
            value, i = data[i:i + 8], i + 8
        elif wire == 5:
            value, i = data[i:i + 4], i + 4
        else:
            raise ValueError("unsupported wire type %d" % wire)
        yield number, value


def first(data, number):
    for found, value in fields(data):
        if found == number:
            return value
    return None


def agy_generation(blob):
    """Map one gen_metadata row to (model, tokens), from fields checked against a live
    run's reported usage: 1 = the call; in it 4 = counts, 19 = model."""
    call = first(blob, 1)
    counts = first(call, 4) if isinstance(call, bytes) else None
    if not isinstance(counts, bytes):
        return None
    numbers = {n: v for n, v in fields(counts) if isinstance(v, int)}
    model = first(call, 19)
    # 2 = input, 3 = output (thinking + reply), 9 = thinking, 5 = cache read
    return (model.decode() if isinstance(model, bytes) else None,
            {"input": numbers.get(2, 0), "output": numbers.get(3, 0),
             "reasoning": numbers.get(9, 0), "cached": numbers.get(5, 0)})


def agy_last_step(db):
    """Newest step creation time, seconds: steps.metadata field 1 is a Timestamp."""
    newest = None
    for (blob,) in db.execute("select metadata from steps where metadata is not null"):
        stamp = first(blob, 1)
        seconds = first(stamp, 1) if isinstance(stamp, bytes) else None
        if isinstance(seconds, int):
            newest = max(newest or 0, seconds)
    return newest


def agy(totals, since):
    root = os.path.expanduser("~/.gemini/antigravity-cli/conversations")
    for path in sorted(glob.glob(os.path.join(root, "*.db"))):
        db = None
        try:
            db = sqlite3.connect("file:%s?mode=ro" % path, uri=True)
            when = agy_last_step(db) or os.path.getmtime(path)
            if when < since:
                continue
            # Parse the whole file first: one bad row skips the file, never half of it.
            generations = [g for g in (agy_generation(blob) for (blob,) in
                                       db.execute("select data from gen_metadata order by idx"))
                           if g]
            for model, tokens in generations:
                totals.add("agy", day_of(when), model, **tokens)
        except (sqlite3.Error, ValueError, IndexError) as exc:
            warn("skipped %s: %s" % (os.path.basename(path), exc))
        finally:
            if db is not None:
                db.close()


# --- Muse ------------------------------------------------------------------------------


def find(obj, test):
    """Yield every dict under obj for which test(dict) is true."""
    if isinstance(obj, dict):
        if test(obj):
            yield obj
        obj = list(obj.values())
    if isinstance(obj, list):
        for child in obj:
            yield from find(child, test)


def muse(totals, since):
    root = os.path.expanduser("~/.local/share/muse/sessions")
    logs = (glob.glob(os.path.join(root, "*", "*", "*", "*", "session.jsonl"))
            + glob.glob(os.path.join(root, "*", "*", "*", "*", "subagent", "*",
                                     "session.jsonl")))
    for path in sorted(logs):
        model = None
        for line in lines(path):
            if '"model_id"' not in line and '"usage_family"' not in line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("payload_type") == "run.model.configured":
                for found in find(record, lambda d: "model_id" in d):
                    model = found["model_id"]
            for usage in find(record, lambda d: d.get("usage_family") == "provider"):
                quantity = usage.get("quantity") or {}
                stamp = (record.get("recorded_at") or 0) / 1e6
                if quantity.get("unit") != "tokens" or stamp < since:
                    continue
                if not any(quantity.get(k) for k in ("input_tokens", "output_tokens")):
                    continue  # Muse also logs empty records for calls that sent nothing
                totals.add("muse", day_of(stamp), model,
                           calls=quantity.get("main_llm_steps") or 1,
                           input=quantity.get("input_tokens"),
                           cached=quantity.get("cached_tokens"),
                           output=quantity.get("output_tokens"),
                           reasoning=quantity.get("reasoning_tokens"))


# --- Vertex AI (Cloud Monitoring) -------------------------------------------------------


def vertex(project, days):
    """Return {model: {"input": n, "output": n}} summed over the window."""
    token = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True,
                           text=True, check=True, timeout=60).stdout.strip()
    end = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    start = end - datetime.timedelta(days=days)
    params = {
        "filter": 'metric.type="aiplatform.googleapis.com/publisher/online_serving/'
                  'token_count"',
        "interval.startTime": start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "interval.endTime": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aggregation.alignmentPeriod": "%ds" % (days * 86400),
        "aggregation.perSeriesAligner": "ALIGN_SUM",
        "aggregation.crossSeriesReducer": "REDUCE_SUM",
        "aggregation.groupByFields": ["resource.label.model_user_id", "metric.label.type"],
    }
    url = ("https://monitoring.googleapis.com/v3/projects/%s/timeSeries?"
           % urllib.parse.quote(project) + urllib.parse.urlencode(params, doseq=True))
    request = urllib.request.Request(url, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(request, timeout=60) as response:
        data = json.load(response)
    models = collections.defaultdict(dict)
    for series in data.get("timeSeries", []):
        model = series["resource"]["labels"].get("model_user_id", "?")
        kind = series["metric"]["labels"].get("type", "?")
        models[model][kind] = sum(int(p["value"]["int64Value"]) for p in series["points"])
    return dict(models)


# --- Output ----------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--days", type=int, default=7, help="window, in days (default 7)")
    parser.add_argument("--source", action="append", choices=SOURCES,
                        help="limit to these CLIs (repeatable; default all)")
    parser.add_argument("--vertex", metavar="PROJECT",
                        help="also report this GCP project's Vertex AI token counts")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    if args.days <= 0:
        parser.error("--days must be positive")
    since = (datetime.datetime.now(datetime.timezone.utc)
             - datetime.timedelta(days=args.days)).timestamp()
    totals = Totals()
    readers = {"codex": codex, "agy": agy, "muse": muse}
    for source in dict.fromkeys(args.source or SOURCES):  # a repeated --source counts once
        readers[source](totals, since)
    rows = [dict(source=s, day=d, model=m, **v) for (s, d, m), v in sorted(totals.rows.items())]
    cloud, status = None, 0 if rows else 1
    if args.vertex:
        try:
            cloud = vertex(args.vertex, args.days)
            status = 0 if rows or cloud else 1
        except (OSError, subprocess.SubprocessError, ValueError, KeyError) as exc:
            warn("--vertex failed: %s" % exc)
            status = 3
    if args.json:
        print(json.dumps({"days": args.days, "rows": rows, "vertex": cloud}, indent=2))
        return status
    header = ("source", "day", "model", "calls") + FIELDS
    table = [header] + [tuple(str(r[k]) for k in header) for r in rows]
    widths = [max(len(row[i]) for row in table) for i in range(len(header))]
    for row in table:
        print("  ".join(cell.ljust(w) if i < 3 else cell.rjust(w)
                        for i, (cell, w) in enumerate(zip(row, widths))))
    if not rows:
        print("(no session-log usage in the last %d days)" % args.days)
    if cloud is not None:
        print("\nVertex AI, project %s, last %d days:" % (args.vertex, args.days))
        for model, kinds in sorted(cloud.items()) or [("(none)", {})]:
            print("  %s  %s" % (model, "  ".join("%s=%d" % kv for kv in sorted(kinds.items()))))
    return status


if __name__ == "__main__":
    sys.exit(main())
