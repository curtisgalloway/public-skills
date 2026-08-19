---
name: dep-quality
description: Score the health of open-source packages so you can choose between dependency alternatives on evidence instead of fame. Use this skill whenever you are about to add, recommend, or evaluate a third-party dependency; whenever the user asks "which library should I use", "is X maintained", "X vs Y", or asks you to audit existing dependencies; and before pinning any new package in a manifest (Cargo.toml, package.json, pyproject.toml, go.mod). Run it even if you already "know" the popular choice — popularity is one input, not the answer.
---

<!--
SPDX-FileCopyrightText: 2026 contributors
SPDX-License-Identifier: Apache-2.0
-->

# dep-quality: Dependency Fitness Score (DFS)

Computes a 0–10 health score for open-source packages, designed for
*comparing alternatives*. It measures **project health, not fitness for
purpose** — use it as a veto and a tiebreaker, then still read the docs
and API of the finalists before choosing.

## Quick start

```bash
export GITHUB_TOKEN=...   # fine-grained, read-only public access; required in practice
python3 scripts/depscore.py cargo:serde npm:express pypi:requests
python3 scripts/depscore.py --repo rust-lang/regex        # score a repo directly
python3 scripts/depscore.py --manifest path/to/Cargo.toml # score all direct deps
python3 scripts/depscore.py --json cargo:serde            # machine-readable output
```

Ecosystem prefixes: `cargo:`, `npm:`, `pypi:`. Anything else: use `--repo owner/name`.

## How to interpret output

Each package gets:

- **GATE FAILURES** — hard rejections, no score. Archived repo, license
  outside the allowlist, or an unpatched critical advisory. A gated
  package is out regardless of how good the alternatives look.
- **DFS score (0–10)** — weighted geometric mean of five components.
  Geometric, so a near-zero in any one component tanks the total:
  popularity cannot compensate for abandonment.
- **Reason codes** — per-component evidence (e.g. `bus-factor 2/10:
  single maintainer, 94% of trailing-year commits`). Always relay the
  reason codes when recommending, not just the number.
- **Confidence (0–1)** — fraction of components computed from primary
  data. Below 0.6, treat the score as a hint, say so explicitly, and
  weigh qualitative inspection more heavily.

Rules of thumb when comparing alternatives:

- Difference < 1.0 point → treat as a tie; decide on API fit, docs, weight.
- Any component ≤ 2 → investigate that reason code manually before adopting.
- Never present the score as a verdict on code quality. It measures
  stewardship: will this project still be alive and patched in two years.

## The metric

**Stage 1 — gates** (fail ⇒ reject):
1. License in allowlist (default: MIT, Apache-2.0, BSD-2/3-Clause, ISC,
   MPL-2.0, LGPL-2.1/3.0, Zlib, Unlicense, CC0-1.0; override with
   `--licenses`).
2. Repository not archived/deprecated.
3. No unpatched advisory of critical severity.

**Stage 2 — components** (each 0–10):

| Component | Weight | What it measures |
|---|---|---|
| Responsiveness | 0.30 | Maintainer response to *external* issue/PR inflow — items filed by anyone who committed in the trailing year are excluded, so a solo maintainer merging their own PRs can't self-score. Conditional on demand: quiet-but-finished projects are scored by release recency instead of penalized for silence; ignored inflow is what signals abandonment. |
| Adoption | 0.25 | Reverse-dependency count (log-scaled), not stars. Stars measure marketing; dependents measure other engineers betting on the project. crates.io reports this natively; for npm/PyPI it is the deps.dev dependent count of the default version (an undercount of all-versions use — the log scale absorbs most of the difference). Falls back to stars with a confidence penalty where no dependents source exists. |
| Bus factor | 0.20 | Distinct **human** stewards in trailing-year commits. Bots and AI agents are excluded: accounts with GitHub `type: Bot`, `*[bot]` logins, known bot/agent author names, and commits whose only human trace is an agent `Co-Authored-By` trailer. Agent-authored commits landed under a human identity count for that human — they reviewed and carry stewardship. Heavy concentration in one human is penalized. |
| Security hygiene | 0.15 | Advisory *fix latency* (how fast past CVEs were patched), not CVE count — counting CVEs punishes popular, well-audited projects. Blends in OpenSSF Scorecard when reachable. |
| Release discipline | 0.10 | Cadence over trailing 24 months and gap regularity, from registry version history when available — GitHub releases mislead for crates living in monorepos, whose tags belong to other components or don't exist at all. |

**Aggregation:** weighted geometric mean over (component + 0.5), minus 0.5.

## Data sources and fallbacks

1. **deps.dev API** (preferred when reachable): OpenSSF Scorecard, and the
   default-version dependent count (v3alpha `:dependents` endpoint) for
   npm/PyPI adoption.
2. **Registry-native**: crates.io (reverse deps, downloads, version dates),
   npm registry (metadata, version dates), PyPI JSON (metadata, upload
   dates). Used to resolve package → source repo and for release cadence.
3. **GitHub REST**: repo metadata, trailing-year commit sample (bus
   factor + agent-trailer detection), recent issues (responsiveness),
   releases, advisories. Needs `GITHUB_TOKEN` — unauthenticated is
   60 req/hr and the script spends ~5 per package.

Every fallback lowers the confidence field rather than silently
substituting. Results are cached in `~/.cache/depscore/` for 7 days;
pass `--no-cache` to force refresh.

## Known limitations (tell the user when relevant)

- Registry dependents only see open-source consumers; private/vendored
  use is invisible.
- Git-pinned or vendored dependencies skip registry data entirely
  (`--repo` mode, lower confidence).
- `--manifest` on a Cargo.toml skips `path` and workspace-internal
  dependencies (announced on stderr) rather than scoring a same-named
  stranger crate from crates.io.
- A license GitHub reports as `NOASSERTION` passes the gate but is
  flagged "verify manually" — check the repo's LICENSE file yourself.
- Non-GitHub hosting (GitLab, sourcehut, codeberg) currently scores
  registry-side components only.
- The responsiveness sample reads the most recent ~30 issues; very
  high-traffic projects are undersampled but such projects rarely fail
  this component.
