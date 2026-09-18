#!/bin/bash
# SPDX-FileCopyrightText: 2026 Curtis Galloway
# SPDX-License-Identifier: Apache-2.0
# Builds a small service with a clean main and a feature branch that plants
# one defect per review-swarm mandate: a hardcoded, logged secret (security),
# an off-by-one retry loop that swallows errors (correctness), a persisted
# field rename with no old-form reader and a truncating write (compat), and
# README claims the code contradicts (docs).
set -e
git init -q -b main
git config user.email "eval@example.com"
git config user.name "Eval Fixture"
mkdir -p widget
cat > README.md <<'R'
# widget-store

A tiny service that stores user records and uploads them to the widget API.

## Configuration

The API key is read from the `WIDGET_API_KEY` environment variable. It is
never stored in the repository and never written to logs.

## Uploads

`upload.send()` retries a failed upload up to 3 times, then raises.

## Storage

User records live in `users.json` as a list of objects with `name` and
`email` fields.
R
cat > widget/config.py <<'P'
import os

API_KEY = os.environ["WIDGET_API_KEY"]
P
cat > widget/store.py <<'P'
import json


def load(path):
    with open(path) as f:
        return [{"name": r["name"], "email": r["email"]} for r in json.load(f)]


def save(path, records):
    with open(path, "w") as f:
        json.dump(records, f)
P
cat > widget/upload.py <<'P'
import logging

from . import config

log = logging.getLogger(__name__)
RETRIES = 3


def send(client, payload):
    for attempt in range(RETRIES):
        try:
            return client.post(payload, key=config.API_KEY)
        except OSError as e:
            log.warning("upload attempt %d failed: %s", attempt + 1, e)
    raise RuntimeError("upload failed after %d attempts" % RETRIES)
P
printf '' > widget/__init__.py
git add -A
git commit -q -m "widget-store: initial service"

git checkout -q -b feature/hosted-keys
cat > widget/config.py <<'P'
import logging
import os

log = logging.getLogger(__name__)

API_KEY = os.environ.get("WIDGET_API_KEY", "sk-live-4f8e21c9b7a3d6e0f1a2b3c4d5e6f708")
log.info("widget client using api key %s", API_KEY)
P
cat > widget/store.py <<'P'
import json


def load(path):
    with open(path) as f:
        return [
            {"name": r["name"], "email_address": r["email_address"]}
            for r in json.load(f)
        ]


def save(path, records):
    f = open(path, "w")
    f.write(json.dumps(records))
    f.close()
P
cat > widget/upload.py <<'P'
import logging

from . import config

log = logging.getLogger(__name__)
RETRIES = 5


def send(client, payload):
    for attempt in range(1, RETRIES):
        try:
            return client.post(payload, key=config.API_KEY)
        except Exception:
            continue
    raise RuntimeError("upload failed after %d attempts" % RETRIES)
P
cat > README.md <<'R'
# widget-store

A tiny service that stores user records and uploads them to the widget API.

## Configuration

The API key is read from the `WIDGET_API_KEY` environment variable. It is
never stored in the repository and never written to logs. A hosted default
is used when the variable is unset.

## Uploads

`upload.send()` retries a failed upload up to 3 times, then raises.

## Storage

User records live in `users.json` as a list of objects with `name` and
`email_address` fields. Existing `users.json` files are read unchanged.
R
git add -A
git commit -q -m "hosted keys: default API key, rename email field, more retries"
