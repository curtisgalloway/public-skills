#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""depscore: Dependency Fitness Score (DFS) for open-source packages.

Stdlib-only. See SKILL.md for the metric definition.
Usage:
  depscore.py [cargo:NAME|npm:NAME|pypi:NAME ...] [--repo owner/name ...]
              [--manifest FILE] [--json] [--licenses CSV] [--no-cache]
"""
import argparse, hashlib, json, math, os, re, statistics, sys, time
import urllib.request, urllib.error
from datetime import datetime, timezone, timedelta

UA = "depscore/0.1 (dep-quality skill)"
CACHE_DIR = os.path.expanduser("~/.cache/depscore")
CACHE_TTL = 7 * 86400
NOW = datetime.now(timezone.utc)

DEFAULT_LICENSES = {
    "MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0",
    "LGPL-2.1", "LGPL-3.0", "Zlib", "Unlicense", "CC0-1.0", "0BSD",
    "Apache-2.0 OR MIT", "MIT OR Apache-2.0", "BSD-3-Clause OR MIT",
}

BOT_NAME_PAT = re.compile(
    r"dependabot|renovate|github-actions|greenkeeper|snyk-?bot|mergify|"
    r"allcontributors|imgbot|codecov|semantic-release|devin-ai|sweep-ai|"
    r"cursor-?agent|copilot|claude(-code)?\b|openhands|aider", re.I)
AGENT_COAUTHOR_PAT = re.compile(
    r"co-authored-by:.*(noreply@anthropic\.com|copilot@|claude|"
    r"devin-ai-integration|cursoragent|aider)", re.I)

DDEV_SYS = {"cargo": "CARGO", "npm": "NPM", "pypi": "PYPI"}
GH_ADVISORY_ECO = {"cargo": "rust", "npm": "npm", "pypi": "pip"}

# ---------------------------------------------------------------- HTTP layer

def _cache_path(url):
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".json")

def http_json(url, token=None, use_cache=True):
    """GET url, parse JSON. Returns (data, err). Caches successes."""
    cp = _cache_path(url)
    if use_cache and os.path.exists(cp) and time.time() - os.path.getmtime(cp) < CACHE_TTL:
        with open(cp) as f:
            return json.load(f), None
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode())
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cp, "w") as f:
        json.dump(data, f)
    return data, None

def days_ago(iso):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return (NOW - dt).days
    except ValueError:
        return None

def clamp(x, lo=0.0, hi=10.0):
    return max(lo, min(hi, x))

# ------------------------------------------------------------- registry layer

def resolve_registry(eco, name, use_cache):
    """Return dict: repo (owner/name or None), license, dependents, downloads,
    deprecated, plus 'notes' list."""
    out = {"repo": None, "license": None, "dependents": None, "downloads": None,
           "deprecated": False, "release_dates": None, "notes": []}
    if eco == "cargo":
        d, err = http_json(f"https://crates.io/api/v1/crates/{name}", use_cache=use_cache)
        if err:
            out["notes"].append(f"crates.io: {err}"); return out
        c = d.get("crate", {})
        out["license"] = (d.get("versions") or [{}])[0].get("license")
        out["downloads"] = c.get("downloads")
        out["repo"] = _gh_repo_from_url(c.get("repository"))
        out["release_dates"] = [v.get("created_at") for v in d.get("versions") or []]
        rd, err = http_json(
            f"https://crates.io/api/v1/crates/{name}/reverse_dependencies?per_page=1",
            use_cache=use_cache)
        if not err:
            out["dependents"] = rd.get("meta", {}).get("total")
    elif eco == "npm":
        d, err = http_json(f"https://registry.npmjs.org/{name}", use_cache=use_cache)
        if err:
            out["notes"].append(f"npm registry: {err}"); return out
        latest = d.get("dist-tags", {}).get("latest")
        v = d.get("versions", {}).get(latest, {})
        out["license"] = v.get("license") if isinstance(v.get("license"), str) else None
        out["deprecated"] = bool(v.get("deprecated"))
        out["repo"] = _gh_repo_from_url((v.get("repository") or {}).get("url")
                                        if isinstance(v.get("repository"), dict)
                                        else v.get("repository"))
        out["release_dates"] = [ts for k, ts in (d.get("time") or {}).items()
                                if k not in ("created", "modified")]
    elif eco == "pypi":
        d, err = http_json(f"https://pypi.org/pypi/{name}/json", use_cache=use_cache)
        if err:
            out["notes"].append(f"pypi: {err}"); return out
        info = d.get("info", {})
        out["license"] = _spdx_guess(info.get("license") or "")
        urls = info.get("project_urls") or {}
        for k in ("Source", "Source Code", "Repository", "Homepage", "Code"):
            r = _gh_repo_from_url(urls.get(k))
            if r:
                out["repo"] = r; break
        if not out["repo"]:
            out["repo"] = _gh_repo_from_url(info.get("home_page"))
        if info.get("yanked"):
            out["deprecated"] = True
        out["release_dates"] = [files[0].get("upload_time_iso_8601")
                                for files in (d.get("releases") or {}).values() if files]
    return out

def _gh_repo_from_url(url):
    if not url:
        return None
    m = re.search(r"github\.com[/:]([\w.-]+)/([\w.-]+?)(?:\.git)?(?:[/#?].*)?$", url)
    return f"{m.group(1)}/{m.group(2)}" if m else None

def _spdx_guess(text):
    t = text.strip()
    if len(t) <= 40 and t:
        return t
    for pat, spdx in [("MIT", "MIT"), ("Apache", "Apache-2.0"), ("BSD", "BSD-3-Clause"),
                      ("Mozilla", "MPL-2.0"), ("LGPL", "LGPL-3.0"), ("ISC", "ISC")]:
        if pat.lower() in t.lower():
            return spdx
    return None

def try_depsdev(eco, name, use_cache):
    """Preferred source: dependents + scorecard. Often unreachable in sandboxes."""
    sysname = DDEV_SYS.get(eco)
    if not sysname:
        return None
    d, err = http_json(
        f"https://api.deps.dev/v3/systems/{sysname}/packages/{urllib.request.quote(name, safe='')}",
        use_cache=use_cache)
    return None if err else d

def depsdev_dependents(eco, name, ddev, use_cache):
    """Dependent count for the package's default version (v3alpha endpoint).
    Per-version, so it reflects the current default version's adoption —
    useful for npm/pypi where no registry-native dependents source exists."""
    sysname = DDEV_SYS.get(eco)
    if not sysname or not isinstance(ddev, dict):
        return None
    ver = next(((v.get("versionKey") or {}).get("version")
                for v in ddev.get("versions") or [] if v.get("isDefault")), None)
    if not ver:
        return None
    d, err = http_json(
        f"https://api.deps.dev/v3alpha/systems/{sysname}/packages/"
        f"{urllib.request.quote(name, safe='')}/versions/{ver}:dependents",
        use_cache=use_cache)
    return None if err or not isinstance(d, dict) else d.get("dependentCount")

# --------------------------------------------------------------- GitHub layer

def gh(path, token, use_cache):
    return http_json(f"https://api.github.com{path}", token=token, use_cache=use_cache)

def is_bot_user(u):
    """True if this GitHub user is a bot/agent identity.

    Takes a GitHub user dict, so it serves issue/PR filers as well as
    commit authors.
    """
    u = u or {}
    if u.get("type") == "Bot" or (u.get("login") or "").endswith("[bot]"):
        return True
    return bool(BOT_NAME_PAT.search(u.get("login") or ""))

def is_bot_commit(c):
    """True if this commit's author is a bot/agent identity."""
    if is_bot_user(c.get("author")):
        return True
    ca = (c.get("commit") or {}).get("author") or {}
    ident = f"{ca.get('name','')} {ca.get('email','')}"
    if BOT_NAME_PAT.search(ident):
        return True
    if "noreply@anthropic.com" in ident:
        return True
    return False

def human_author_key(c):
    a = c.get("author") or {}
    if a.get("login"):
        return a["login"]
    ca = (c.get("commit") or {}).get("author") or {}
    return ca.get("email") or ca.get("name") or "unknown"

# ------------------------------------------------------------------- scoring

class Component:
    def __init__(self, name, weight):
        self.name, self.weight = name, weight
        self.score, self.primary, self.reason = None, False, "no data"

    def set(self, score, reason, primary=True):
        self.score, self.reason, self.primary = round(clamp(score), 1), reason, primary

def score_package(spec, args, token):
    eco, _, name = spec.partition(":")
    if not name:                       # --repo mode
        eco, name = None, None
        repo = spec
        reg = {"repo": repo, "license": None, "dependents": None, "downloads": None,
               "deprecated": False, "release_dates": None,
               "notes": ["repo mode: no registry data"]}
        ddev = None
    else:
        reg = resolve_registry(eco, name, not args.no_cache)
        repo = reg["repo"]
        ddev = try_depsdev(eco, name, not args.no_cache)

    label = spec
    gates, notes = [], list(reg["notes"])
    comps = {k: Component(k, w) for k, w in
             [("responsiveness", .30), ("adoption", .25), ("bus-factor", .20),
              ("security", .15), ("releases", .10)]}

    # ---- GitHub-side data
    repo_d = commits = issues = releases = None
    if repo:
        repo_d, err = gh(f"/repos/{repo}", token, not args.no_cache)
        if err:
            notes.append(f"github /repos: {err}"); repo_d = None
        else:
            since = (NOW - timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%SZ")
            commits, e1 = gh(f"/repos/{repo}/commits?since={since}&per_page=100",
                             token, not args.no_cache)
            issues, e2 = gh(f"/repos/{repo}/issues?state=all&per_page=30&sort=created"
                            f"&direction=desc", token, not args.no_cache)
            releases, e3 = gh(f"/repos/{repo}/releases?per_page=20", token, not args.no_cache)
            for e in (e1, e2, e3):
                if e:
                    notes.append(f"github: {e}")
            if not isinstance(commits, list): commits = None
            if not isinstance(issues, list): issues = None
            if not isinstance(releases, list): releases = None
    else:
        notes.append("no source repo resolved")

    # ---- gates
    lic = None
    if repo_d and repo_d.get("license"):
        lic = repo_d["license"].get("spdx_id")
    lic = reg["license"] or lic
    allow = set(args.licenses.split(",")) if args.licenses else DEFAULT_LICENSES
    if lic and lic not in allow and lic != "NOASSERTION":
        gates.append(f"license '{lic}' not in allowlist")
    elif not lic or lic == "NOASSERTION":
        notes.append("license undetermined — verify manually")
    if repo_d and repo_d.get("archived"):
        gates.append("repository is archived")
    if reg["deprecated"]:
        gates.append("package marked deprecated/yanked in registry")

    advisories = None
    if eco in GH_ADVISORY_ECO and name:
        advisories, err = gh(f"/advisories?affects={name}&ecosystem={GH_ADVISORY_ECO[eco]}"
                             f"&per_page=50", token, not args.no_cache)
        if err:
            notes.append(f"github advisories: {err}"); advisories = None
    if isinstance(advisories, list):
        unpatched_crit = [a for a in advisories
                          if a.get("severity") == "critical"
                          and not all(v.get("first_patched_version")
                                      for v in a.get("vulnerabilities") or [{}])]
        if unpatched_crit:
            gates.append(f"{len(unpatched_crit)} unpatched critical advisory(ies)")

    # ---- responsiveness (conditional on *external* demand)
    # Items filed by people who committed in the trailing year are excluded:
    # a maintainer opening and same-day-closing their own PRs is routine
    # development, not evidence anyone answers outside contributors.
    # Bot-filed items are excluded too. `maintainer_logins` deliberately omits
    # bots so they cannot be credited as stewards by bus-factor; reusing that
    # set here would invert the intent and promote dependabot to "outside
    # contributor", scoring the project on how fast it merges its own robots.
    maintainer_logins = set()
    if commits:
        for c in commits:
            if not is_bot_commit(c) and (c.get("author") or {}).get("login"):
                maintainer_logins.add(c["author"]["login"])
    if issues is not None:
        recent = [i for i in issues if (days_ago(i["created_at"]) or 999) <= 365
                  and (i.get("user") or {}).get("login") not in maintainer_logins
                  and not is_bot_user(i.get("user"))]
        inflow = len(recent)
        if inflow >= 5:
            responded = [i for i in recent if i.get("comments", 0) > 0
                         or i.get("state") == "closed"]
            frac = len(responded) / inflow
            close_days = [days_ago(i["created_at"]) - (days_ago(i.get("closed_at")) or 0)
                          for i in recent if i.get("closed_at")]
            med = statistics.median(close_days) if close_days else None
            s = 10 * frac
            if med is not None and med > 90:
                s *= 0.5
            comps["responsiveness"].set(
                s, f"{len(responded)}/{inflow} recent external issues/PRs engaged"
                   + (f", median close {med:.0f}d" if med is not None else ""))
        else:
            lr = days_ago(releases[0]["published_at"]) if releases else \
                 days_ago(repo_d.get("pushed_at")) if repo_d else None
            lr = 9999 if lr is None else lr
            s = 8 if lr < 365 else 6 if lr < 730 else 4 if lr < 1095 else 2
            comps["responsiveness"].set(
                s, f"low external demand ({inflow} issues/yr); scored by recency "
                   f"({lr}d since last release/push)", primary=False)

    # ---- adoption
    dep_n = reg["dependents"]
    dep_src = "reverse dependencies"
    if dep_n is None and ddev:
        dep_n = depsdev_dependents(eco, name, ddev, not args.no_cache)
        dep_src = "dependents of default version (deps.dev)"
    if dep_n is not None:
        comps["adoption"].set(10 * math.log10(1 + dep_n) / 4,
                              f"{dep_n} {dep_src}")
    elif repo_d:
        stars = repo_d.get("stargazers_count", 0)
        comps["adoption"].set(10 * math.log10(1 + stars / 3) / 4,
                              f"fallback: {stars} stars (no dependents source)",
                              primary=False)

    # ---- bus factor (humans only)
    if commits is not None:
        human = [c for c in commits if not is_bot_commit(c)]
        agent_flagged = sum(1 for c in commits
                            if AGENT_COAUTHOR_PAT.search(
                                (c.get("commit") or {}).get("message", "")))
        counts = {}
        for c in human:
            counts[human_author_key(c)] = counts.get(human_author_key(c), 0) + 1
        h = len(counts)
        top = max(counts.values()) / len(human) if human else 1.0
        s = {0: 0, 1: 2, 2: 4, 3: 6, 4: 6}.get(h, 8)
        if h >= 2 and top < 0.5:
            s += 2
        detail = f"{h} human committer(s) in trailing yr, top share {top:.0%}"
        if len(commits) - len(human):
            detail += f"; {len(commits)-len(human)} bot/agent commits excluded"
        if agent_flagged:
            detail += f"; {agent_flagged} agent-coauthored (counted to human sponsor)"
        comps["bus-factor"].set(s, detail)

    # ---- security hygiene
    if isinstance(advisories, list):
        if not advisories:
            comps["security"].set(8, "no known advisories")
        else:
            patched = [a for a in advisories
                       if all(v.get("first_patched_version")
                              for v in a.get("vulnerabilities") or [{}])]
            frac = len(patched) / len(advisories)
            comps["security"].set(3 + 6 * frac,
                                  f"{len(patched)}/{len(advisories)} advisories patched")
    elif repo_d:
        comps["security"].set(5, "no advisory data for this ecosystem", primary=False)
    if ddev and isinstance(ddev, dict) and ddev.get("scorecard"):
        sc = ddev["scorecard"].get("overallScore")
        if sc is not None and comps["security"].score is not None:
            comps["security"].set((comps["security"].score + sc) / 2,
                                  comps["security"].reason + f"; scorecard {sc}")

    # ---- release discipline
    # Registry version history is preferred: GitHub releases mislead for
    # crates living in monorepos (tags belong to other components, or the
    # repo publishes to the registry without cutting releases at all).
    src = None
    dated = sorted(d for iso in reg["release_dates"] or []
                   if (d := days_ago(iso)) is not None)
    if dated:
        src = "registry"
    elif releases is not None:
        dated = sorted(d for r in releases
                       if (d := days_ago(r.get("published_at"))) is not None)
        src = "github"
    if src is not None:
        n24 = sum(1 for d in dated if d <= 730)
        s = 2 if n24 == 0 else 5 if n24 <= 2 else 8 if n24 <= 6 else 9
        gaps = [b - a for a, b in zip(dated, dated[1:])]
        if len(gaps) >= 3 and max(gaps) < 3 * statistics.median(gaps):
            s += 1
        comps["releases"].set(s, f"{n24} releases in 24mo ({src})"
                              + (", regular cadence" if s in (9, 10) else ""))
        if src == "github" and n24 == 0 and repo_d \
                and (days_ago(repo_d.get("pushed_at")) or 9999) < 90:
            comps["releases"].set(4, "no releases but active pushes (rolling repo?)",
                                  primary=False)

    # ---- aggregate
    scored = [c for c in comps.values() if c.score is not None]
    if gates:
        dfs = None
    elif scored:
        wsum = sum(c.weight for c in scored)
        dfs = round(math.exp(sum(c.weight / wsum * math.log(c.score + 0.5)
                                 for c in scored)) - 0.5, 1)
    else:
        dfs = None
    confidence = round(sum(c.weight for c in scored if c.primary) /
                       sum(c.weight for c in comps.values()), 2)
    return {"package": label, "repo": repo, "license": lic, "gates": gates,
            "dfs": dfs, "confidence": confidence, "notes": notes,
            "components": {c.name: {"score": c.score, "weight": c.weight,
                                    "reason": c.reason, "primary": c.primary}
                           for c in comps.values()}}

# ------------------------------------------------------------------ manifests

def _cargo_workspace_deps(manifest_path):
    """[workspace.dependencies] of the enclosing workspace root, as
    {name: value-string}. Empty dict if no workspace root is found."""
    d = os.path.dirname(os.path.abspath(manifest_path))
    for _ in range(6):
        root = os.path.join(d, "Cargo.toml")
        if os.path.exists(root) and "[workspace" in open(root).read():
            deps, section = {}, None
            for line in open(root).read().splitlines():
                line = line.split("#")[0].strip()
                if line.startswith("["):
                    section = line.strip("[]")
                elif section == "workspace.dependencies" and "=" in line:
                    name, _, val = line.partition("=")
                    deps[name.strip().strip('"')] = val
            return deps
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return {}

def deps_from_manifest(path):
    base = os.path.basename(path)
    text = open(path).read()
    if base == "Cargo.toml":
        # path deps are workspace-internal; workspace = true deps resolve
        # through the root manifest, whose entry may itself be a path dep.
        # Anything unresolvable is skipped loudly rather than scored as a
        # same-named stranger crate on crates.io.
        ws = None
        deps, section, skipped = [], None, []
        for line in text.splitlines():
            line = line.split("#")[0].strip()
            if line.startswith("["):
                section = line.strip("[]")
            elif section in ("dependencies", "dev-dependencies", "build-dependencies") \
                    and "=" in line:
                name, _, val = line.partition("=")
                name = name.strip().strip('"')
                if re.search(r"\bpath\s*=", val):
                    skipped.append(name); continue
                if name.endswith(".workspace") or re.search(r"\bworkspace\s*=\s*true", val):
                    name = name.removesuffix(".workspace")
                    if ws is None:
                        ws = _cargo_workspace_deps(path)
                    if re.search(r"\bpath\s*=", ws.get(name, "path =")):
                        skipped.append(name); continue
                deps.append("cargo:" + name)
        if skipped:
            print(f"note: skipped path/workspace-internal deps: {', '.join(skipped)}",
                  file=sys.stderr)
        return deps
    if base == "package.json":
        d = json.loads(text)
        keys = list(d.get("dependencies", {})) + list(d.get("devDependencies", {}))
        return ["npm:" + k for k in keys]
    if base in ("requirements.txt",):
        return ["pypi:" + re.split(r"[<>=!~\[; ]", l.strip())[0]
                for l in text.splitlines()
                if l.strip() and not l.strip().startswith(("#", "-"))]
    if base == "pyproject.toml":
        deps = re.findall(r'^\s*"([A-Za-z0-9_.-]+)', 
                          text.split("dependencies = [", 1)[-1].split("]", 1)[0],
                          re.M) if "dependencies = [" in text else []
        return ["pypi:" + d for d in deps]
    raise SystemExit(f"unsupported manifest: {base}")

# ------------------------------------------------------------------------ CLI

def fmt_result(r):
    lines = [f"\n{'='*72}", f"{r['package']}"
             + (f"   [{r['repo']}]" if r["repo"] else "   [no repo]")
             + (f"   license: {r['license']}" if r["license"] else "")]
    if r["gates"]:
        lines.append("  GATE FAILURE — rejected:")
        lines += [f"    x {g}" for g in r["gates"]]
    else:
        lc = "  ** LOW CONFIDENCE — mostly fallback/missing data **" \
             if r["confidence"] < 0.5 else ""
        lines.append(f"  DFS: {r['dfs'] if r['dfs'] is not None else 'n/a'} / 10"
                     f"    confidence: {r['confidence']}{lc}")
    for name, c in r["components"].items():
        s = "-" if c["score"] is None else f"{c['score']:>4}"
        flag = "" if (c["primary"] or c["score"] is None) else "  (fallback)"
        lines.append(f"    {name:<15} {s}  {c['reason']}{flag}")
    for n in r["notes"]:
        lines.append(f"    note: {n}")
    return "\n".join(lines)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("specs", nargs="*", help="eco:name (cargo:/npm:/pypi:)")
    ap.add_argument("--repo", action="append", default=[], help="owner/name")
    ap.add_argument("--manifest")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--licenses", help="comma-separated SPDX allowlist override")
    ap.add_argument("--no-cache", action="store_true")
    args = ap.parse_args()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("warning: no GITHUB_TOKEN — unauthenticated GitHub API is 60 req/hr",
              file=sys.stderr)
    specs = list(args.specs) + [r for r in args.repo]
    if args.manifest:
        specs += deps_from_manifest(args.manifest)
    if not specs:
        ap.error("nothing to score")
    results = [score_package(s, args, token) for s in dict.fromkeys(specs)]
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        ranked = sorted(results, key=lambda r: (r["dfs"] is None, -(r["dfs"] or 0)))
        for r in ranked:
            print(fmt_result(r))
        print()

if __name__ == "__main__":
    main()
