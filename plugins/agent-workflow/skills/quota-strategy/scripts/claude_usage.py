#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Print Claude subscription usage for every pool: 5-hour, weekly, per-model weekly.

Sources, in order:
  1. Live: GET https://api.anthropic.com/api/oauth/usage (undocumented; the
     endpoint Claude Code's /usage uses). Auth = Claude Code's OAuth token.
  2. Fallback: Claude Code's cache in ~/.claude.json
     (cachedUsageUtilization.utilization), stale but offline.

Pools come from the response's limits[] list:
  kind "session"        -> the 5-hour window
  kind "weekly_all"     -> the general weekly limit
  kind "weekly_scoped"  -> a separate weekly limit for one model (scope.model)
When limits[] is absent, the older five_hour / seven_day fields are used.

Usage:  python3 claude_usage.py [--cache-only] [--json] [--model NAME]
Exit code: 0 ok, 1 --model given but that model has no separate limit,
           2 no auth and no cache.
"""
import json
import os
import subprocess
import sys
import urllib.request

USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
HOME = os.path.expanduser("~")
KIND_NAMES = {"session": "5-hour", "weekly_all": "weekly"}


def get_token():
    # macOS Keychain (Claude Code stores credentials here on a Mac)
    if sys.platform == "darwin":
        try:
            raw = subprocess.run(
                ["/usr/bin/security", "find-generic-password",
                 "-s", "Claude Code-credentials", "-w"],
                capture_output=True, text=True, timeout=10,
            ).stdout.strip()
            if raw:
                return json.loads(raw)["claudeAiOauth"]["accessToken"]
        except Exception:
            pass
    # Linux, or a Mac without a Keychain entry
    try:
        with open(os.path.join(HOME, ".claude", ".credentials.json")) as f:
            return json.load(f)["claudeAiOauth"]["accessToken"]
    except Exception:
        return None


def fetch_live(token):
    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def read_cache():
    with open(os.path.join(HOME, ".claude.json")) as f:
        return json.load(f)["cachedUsageUtilization"]["utilization"]


def pools(data):
    """Return [{pool, model, percent, resets_at}] from a usage response."""
    out = []
    for lim in data.get("limits") or []:
        kind = lim.get("kind")
        model = ((lim.get("scope") or {}).get("model") or {})
        model_name = model.get("display_name") or model.get("id")
        if kind == "weekly_scoped" and model_name:
            name = f"{model_name} weekly"
        else:
            name = KIND_NAMES.get(kind, kind)
        out.append({
            "pool": name,
            "model": model_name,
            "percent": lim.get("percent"),
            "resets_at": lim.get("resets_at"),
        })
    if out:
        return out
    for key, name in (("five_hour", "5-hour"), ("seven_day", "weekly")):
        window = data.get(key)
        if isinstance(window, dict):
            out.append({
                "pool": name,
                "model": None,
                "percent": window.get("utilization"),
                "resets_at": window.get("resets_at"),
            })
    return out


def main(argv):
    cache_only = "--cache-only" in argv
    as_json = "--json" in argv
    want_model = None
    if "--model" in argv:
        i = argv.index("--model")
        if i + 1 >= len(argv):
            print("--model needs a name", file=sys.stderr)
            return 2
        want_model = argv[i + 1].lower()

    data, source = None, None
    if not cache_only:
        token = get_token()
        if token:
            try:
                data, source = fetch_live(token), "live"
            except Exception as e:
                print(f"live fetch failed: {e}", file=sys.stderr)
        else:
            print("no Claude Code OAuth token found", file=sys.stderr)
    if data is None:
        try:
            data, source = read_cache(), "cache (~/.claude.json, may be stale)"
        except Exception as e:
            print(f"no cached usage either: {e}", file=sys.stderr)
            return 2

    found = pools(data)
    if as_json:
        print(json.dumps({"source": source, "pools": found}, indent=2))
    else:
        for p in found:
            print(f"{p['pool']}: {p['percent']}% used, resets {p['resets_at']}"
                  f"  [{source}]")
    if want_model is not None:
        if not any(want_model in (p["model"] or "").lower() for p in found):
            print(f"no separate weekly limit for {want_model}", file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
