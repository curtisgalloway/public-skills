#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0

"""Find and download the newest Bus Pirate 5/6 firmware build from upstream main.

Upstream publishes no tagged releases. Its CI bot posts a zip for every commit to
`main` in the forum thread "Bus Pirate 5 auto build: main branch", and
firmware.buspirate.com points users there. This script reads that thread through
the Discourse JSON API, picks the newest `ci-buspirate-main-<sha>.zip`, and pulls
the one `.uf2` your board needs out of it.

Usage:
    python3 bp_firmware.py latest                       # newest build: sha, date, URL
    python3 bp_firmware.py fetch --board rev10 OUT_DIR  # download + extract the .uf2

`OUT_DIR` must be missing or empty: the zip is downloaded content, so it gets a
directory of its own. Standard library only.
"""

import argparse
import json
import os
import re
import sys
import urllib.request
import zipfile

FORUM = "https://forum.buspirate.com"
TOPIC_ID = 20
BOT_USERNAME = "Bus-Pirate"
MAX_POSTS_SCANNED = 30

# Board name -> path of its image inside the CI zip. Verified against
# ci-buspirate-main-322c452.zip (2026-10-12); the 5XL and REV8 images sit in attic/.
BOARD_FILES = {
    "rev10": "bus_pirate5_rev10.uf2",
    "bp6": "bus_pirate6.uf2",
    "xl": "attic/bus_pirate5_xl.uf2",
    "rev8": "attic/bus_pirate5_rev8.uf2",
}

ATTACHMENT_RE = re.compile(
    r'<a class="attachment" href="(?P<href>[^"]+)">'
    r"(?P<name>ci-buspirate-main-(?P<sha>[0-9a-f]{7,40})\.zip)</a>"
)


def get_json(path):
    req = urllib.request.Request(
        FORUM + path,
        headers={"Accept": "application/json", "User-Agent": "bp_firmware.py"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def find_attachment(cooked):
    """Return (name, sha, href) for the CI zip linked in a post's HTML, or None."""
    match = ATTACHMENT_RE.search(cooked)
    if not match:
        return None
    return match.group("name"), match.group("sha"), match.group("href")


def latest_build():
    """Walk the thread from its newest post back to the newest bot post with a zip."""
    stream = get_json(f"/t/{TOPIC_ID}.json")["post_stream"]["stream"]
    for post_id in reversed(stream[-MAX_POSTS_SCANNED:]):
        post = get_json(f"/posts/{post_id}.json")
        if post.get("username") != BOT_USERNAME:
            continue
        found = find_attachment(post.get("cooked", ""))
        if found:
            name, sha, href = found
            return {
                "sha": sha,
                "zip_name": name,
                "url": href if href.startswith("http") else FORUM + href,
                "posted": post["created_at"],
                "post_url": f"{FORUM}/t/{TOPIC_ID}/{post['post_number']}",
            }
    raise SystemExit(
        f"no ci-buspirate-main-*.zip in the last {MAX_POSTS_SCANNED} posts of "
        f"{FORUM}/t/{TOPIC_ID}"
    )


def fetch(board, out_dir):
    if os.path.isdir(out_dir) and os.listdir(out_dir):
        raise SystemExit(f"{out_dir} is not empty; give the download its own directory")
    os.makedirs(out_dir, exist_ok=True)
    build = latest_build()
    zip_path = os.path.join(out_dir, build["zip_name"])
    urllib.request.urlretrieve(build["url"], zip_path)
    member = BOARD_FILES[board]
    with zipfile.ZipFile(zip_path) as archive:
        if member not in archive.namelist():
            raise SystemExit(
                f"{member} not in {build['zip_name']}; it contains: "
                + ", ".join(archive.namelist())
            )
        archive.extract(member, out_dir)
    build["uf2"] = os.path.join(out_dir, member)
    return build


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("latest", help="print the newest main-branch build")
    fetch_p = sub.add_parser("fetch", help="download the newest build and extract one .uf2")
    fetch_p.add_argument("--board", choices=sorted(BOARD_FILES), required=True)
    fetch_p.add_argument("out_dir")
    args = parser.parse_args(argv)

    if args.command == "latest":
        build = latest_build()
    else:
        build = fetch(args.board, args.out_dir)
    json.dump(build, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
