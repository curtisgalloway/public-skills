#!/bin/bash
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
# A docs-only feature branch: the README gains a configuration section that
# contradicts the unchanged code (wrong default port, a flag that does not
# exist). review-swarm's planner should choose the light tier, so the review
# runs one reviewer, not seven, and still finds the contradiction.
set -e
git init -q -b main
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p tinyserve
cat > tinyserve/__main__.py <<'P'
import argparse
import http.server

DEFAULT_PORT = 9090


def main():
    parser = argparse.ArgumentParser(prog="tinyserve")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()
    server = http.server.HTTPServer(("127.0.0.1", args.port), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()


if __name__ == "__main__":
    main()
P
cat > README.md <<'R'
# tinyserve

Serve the current directory over HTTP on localhost.
R
git add -A
git commit -q -m "tinyserve: serve the current directory"
git checkout -q -b docs/configuration
cat >> README.md <<'R'

## Configuration

`tinyserve` listens on port 8080 unless you pass `--port`. Pass `--public` to listen on all
interfaces instead of localhost.
R
git add README.md
git commit -q -m "README: document configuration"
