# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Evaluator-only source export. An export is NOT an approved implementer packet.

Read a pinned upstream tar without extracting it on the host. Write a new tar and
an inventory into a new directory. Verify transfers on a case-sensitive guest.
Only the standard library is required; Python 3.10 or later.
"""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile

COMMIT = "adc218676eef25575469234709c2d87185ca223a"
TREE = "ac4266ccaf1cf79e8fb22ad3e0d86deac358ffb9"
ARCHIVE_SHA256 = "8787cc90ca7740ab7c955b6fad83010dc600f14a6d94511b548703e4f0f40caa"
PREFIX = f"linux-{COMMIT}"
REMOVED = {
    "Documentation/devicetree/bindings/net/microchip,enc28j60.txt",
    "drivers/net/ethernet/microchip/enc28j60.c",
    "drivers/net/ethernet/microchip/enc28j60_hw.h",
    "MAINTAINERS",
    ".mailmap",
}
EDITED = {
    "drivers/net/ethernet/microchip/Kconfig",
    "drivers/net/ethernet/microchip/Makefile",
    "arch/arm/configs/mxs_defconfig",
}
DEVICE = re.compile(rb"enc28j60|en28j60|framethrower", re.IGNORECASE)
VENDOR = re.compile(rb"microchip", re.IGNORECASE)


def sha256_file(path):
    """Hash a file without loading the archive into memory."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_object(kind, data):
    """Return the pinned Git format's object identity."""
    return hashlib.sha1(kind + b" " + str(len(data)).encode() + b"\x00" + data).digest()


def git_tree(entries):
    """Reconstruct a Git tree from {path: (mode, blob digest)} without extraction."""
    root = {}
    for path, value in entries.items():
        node = root
        parts = path.split("/")
        for part in parts[:-1]:
            child = node.setdefault(part, {})
            if not isinstance(child, dict):
                raise ValueError(f"Non-directory ancestor: {path}")
            node = child
        if parts[-1] in node:
            raise ValueError(f"Conflicting path: {path}")
        node[parts[-1]] = value

    def digest(node):
        children = []
        for name, value in node.items():
            encoded = name.encode("utf-8")
            if isinstance(value, dict):
                mode, value_hash, sort_key = "40000", digest(value), encoded + b"/"
            else:
                mode, value_hash = value
                sort_key = encoded
            children.append(
                (sort_key, mode.encode() + b" " + encoded + b"\x00" + value_hash)
            )
        return git_object(b"tree", b"".join(item for _, item in sorted(children)))

    return digest(root).hex()


def clean_name(name):
    """Reject ambiguous paths, not merely traversal after normalization."""
    if (
        not name
        or name.startswith("/")
        or any(part in ("", ".", "..") for part in name.split("/"))
    ):
        raise ValueError(f"Unsafe archive path: {name!r}")
    if any(ord(char) < 32 or ord(char) == 127 for char in name):
        raise ValueError("Control character in archive path")
    return name


def validate_links(entries, links):
    """Reject dangling links, cycles and traversal through any symlink ancestor."""
    directories = {
        str(parent) for path in entries for parent in PurePosixPath(path).parents
    }
    for path in entries:
        if any(str(parent) in links for parent in PurePosixPath(path).parents):
            raise ValueError(f"Symlink ancestor: {path}")
    for path, target in links.items():
        if target.startswith("/"):
            raise ValueError(f"Absolute symlink: {path}")
        parts = path.split("/")[:-1]
        for part in target.split("/"):
            if "/".join(parts) in links:
                raise ValueError(f"Traversal through symlink target: {path}")
            if part == "..":
                if not parts:
                    raise ValueError(f"Escaping symlink: {path}")
                parts.pop()
            elif part not in ("", "."):
                parts.append(part)
        resolved = "/".join(parts)
        if resolved not in entries and resolved not in directories:
            raise ValueError(f"Dangling symlink target: {path}")
        if (
            resolved in links
            or resolved in ("", ".")
            or path.startswith(resolved + "/")
        ):
            raise ValueError(f"Cyclic or chained symlink target: {path}")
        if any(str(parent) in links for parent in PurePosixPath(resolved).parents):
            raise ValueError(f"Indirect symlink target: {path}")


def transform(path, data):
    """Apply only the declared device-registration removals."""
    if path.endswith("/microchip/Kconfig"):
        start = b"config ENC28J60\n"
        end = b"config ENCX24J600\n"
        if data.count(start) != 1 or data.count(end) != 1:
            raise ValueError("Kconfig anchors changed")
        first, last = data.index(start), data.index(end)
        if first >= last:
            raise ValueError("Kconfig anchors reordered")
        return data[:first] + data[last:]
    line = {
        "drivers/net/ethernet/microchip/Makefile": (
            b"obj-$(CONFIG_ENC28J60) += enc28j60.o\n"
        ),
        "arch/arm/configs/mxs_defconfig": b"CONFIG_ENC28J60=y\n",
    }[path]
    if data.splitlines(keepends=True).count(line) != 1:
        raise ValueError(f"Registration line changed: {path}")
    return data.replace(line, b"", 1)


def inventory_entry(path, mode, data):
    """Describe the bytes and executable mode, or symlink target bytes."""
    return {
        "path": path,
        "mode": mode,
        "size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def export_archive(source, destination):
    """Export pinned bytes; failed directories remain without a completion record."""
    if sha256_file(source) != ARCHIVE_SHA256:
        raise ValueError("Upstream archive SHA-256 mismatch")
    destination.mkdir(parents=True, exist_ok=False)
    upstream, exported, links = {}, {}, {}
    inventory, changes, vendor_hits = [], [], []
    seen = set()
    output = destination / "source.tar"
    with tarfile.open(source, "r:gz") as original, tarfile.open(
        output, "x"
    ) as supplied:
        for member in original:
            name = member.name.rstrip("/") if member.isdir() else member.name
            clean_name(name)
            if name in seen:
                raise ValueError(f"Duplicate archive member: {name}")
            seen.add(name)
            if name == PREFIX and member.isdir():
                continue
            if not name.startswith(PREFIX + "/"):
                raise ValueError("Unexpected archive root")
            path = name[len(PREFIX) + 1 :]
            if member.isdir():
                continue
            if member.issym():
                mode, data = "120000", member.linkname.encode("utf-8")
            elif member.isfile():
                mode = "100755" if member.mode & 0o111 else "100644"
                data = original.extractfile(member).read()
            else:
                raise ValueError(f"Unsupported archive entry: {path}")
            upstream[path] = (mode, git_object(b"blob", data))
            before = hashlib.sha256(data).hexdigest()
            if path in REMOVED:
                changes.append({"path": path, "action": "remove", "before": before})
                continue
            if path in EDITED:
                data = transform(path, data)
                changes.append(
                    {
                        "path": path,
                        "action": "edit",
                        "before": before,
                        "after": hashlib.sha256(data).hexdigest(),
                    }
                )
            if DEVICE.search(path.encode()) or DEVICE.search(data):
                raise ValueError(f"Unresolved device-name hit: {path}")
            if VENDOR.search(path.encode()) or VENDOR.search(data):
                vendor_hits.append(path)
            exported[path] = (mode, git_object(b"blob", data))
            inventory.append(inventory_entry(path, mode, data))
            item = tarfile.TarInfo("source/" + path)
            if member.issym():
                links[path] = member.linkname
                item.type, item.linkname, item.mode = (
                    tarfile.SYMTYPE,
                    member.linkname,
                    0o777,
                )
                supplied.addfile(item)
            else:
                item.mode = 0o755 if mode == "100755" else 0o644
                item.size = len(data)
                supplied.addfile(item, io.BytesIO(data))
    if git_tree(upstream) != TREE:
        raise ValueError("Upstream whole-tree identity mismatch")
    if {item["path"] for item in changes} != REMOVED | EDITED:
        raise ValueError("Expected removal/edit missing")
    validate_links(exported, links)
    manifest = {
        "schema": "enc28j60-source-export-1",
        "status": "preparation-only-not-approved-for-implementation",
        "upstream_commit": COMMIT,
        "upstream_tree": TREE,
        "upstream_archive_sha256": ARCHIVE_SHA256,
        "exported_tree": git_tree(exported),
        "archive_sha256": sha256_file(output),
        "entries": sorted(inventory, key=lambda item: item["path"]),
        "changes": sorted(changes, key=lambda item: item["path"]),
        "vendor_hit_paths_pending_review": sorted(vendor_hits),
    }
    # This record is written last. Its presence alone is not an acceptance decision.
    with (destination / "manifest.json").open("x") as stream:
        json.dump(manifest, stream, indent=2)
        stream.write("\n")
    return manifest


def verify_directory(root, manifest):
    """Compare every extracted file/link against the evaluator's retained inventory."""

    def fail_walk(error):
        raise error

    if root.is_symlink() or not root.is_dir():
        raise ValueError("Source root must be a real directory")
    actual, entries, links = [], {}, {}
    for directory, dirs, files in os.walk(root, followlinks=False, onerror=fail_walk):
        for name in dirs + files:
            item = Path(directory) / name
            info = item.lstat()
            path = item.relative_to(root).as_posix()
            clean_name(path)
            if stat.S_ISLNK(info.st_mode):
                links[path] = os.readlink(item)
                mode, data = "120000", links[path].encode("utf-8")
            elif stat.S_ISREG(info.st_mode):
                mode = "100755" if info.st_mode & 0o111 else "100644"
                data = item.read_bytes()
            elif stat.S_ISDIR(info.st_mode):
                continue
            else:
                raise ValueError(f"Unexpected file type: {path}")
            actual.append(inventory_entry(path, mode, data))
            entries[path] = (mode, git_object(b"blob", data))
    validate_links(entries, links)
    if sorted(actual, key=lambda item: item["path"]) != manifest["entries"]:
        raise ValueError("Extracted inventory mismatch (content, path, mode or link)")
    if git_tree(entries) != manifest["exported_tree"]:
        raise ValueError("Extracted tree mismatch")
    return {"match": True, "entries": len(actual), "tree": manifest["exported_tree"]}


def main():
    """Run one evaluator-side export or extracted-tree verification."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    export = commands.add_parser(
        "export", help="write a new preparation-only directory"
    )
    export.add_argument("archive", type=Path)
    export.add_argument("destination", type=Path)
    verify = commands.add_parser(
        "verify", help="compare an extraction to a retained manifest"
    )
    verify.add_argument("root", type=Path)
    verify.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "export":
            result = export_archive(args.archive, args.destination)
            print(
                json.dumps(
                    {
                        key: result[key]
                        for key in ("status", "exported_tree", "archive_sha256")
                    }
                )
            )
        else:
            result = verify_directory(args.root, json.loads(args.manifest.read_text()))
            print(json.dumps(result))
    except (OSError, ValueError, tarfile.TarError) as exc:
        parser.exit(1, f"{exc}\n")


if __name__ == "__main__":
    main()
