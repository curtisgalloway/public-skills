#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 contributors
# SPDX-License-Identifier: Apache-2.0
"""Check board specs against SPEC-FORMAT.md.

A root is a directory holding ``board-specs.yaml``; every ``*.spec.md``
below it is a spec (or an overlay, when its frontmatter has ``overlays:``).
Give one or more roots; references (``parts``, ``instances[].ip``,
``overlays``) resolve across all of them together, the way the reader sees
them.

What fails (exit 1):

  * frontmatter that does not parse, or is missing a key its kind requires
  * an unknown ``kind`` or root ``layer``; a duplicate ``id``
  * a ``parts`` entry, an ``instances[].ip``, an ``overlays`` target, or a
    ``variant_of`` that resolves to nothing across the given roots
  * an ``instances[]`` row whose ``reg`` is not an integer or null, or whose
    ``irq`` is not null or a mapping with ``kind`` (SPI | PPI | extended)
    and an integer ``number``; an ``extended`` irq without ``parent``, or a
    SPI/PPI irq with one
  * a ``variants[]`` entry without a ``name``
  * a ``resources.series`` entry with ``cite: true``; a ``fetch:`` value
    other than ok | blocked | truncated; a ``status:`` other than
    unmerged | merged | superseded, on an entry or on one of its ``files``
  * under a ``public`` root: any ``access: internal`` entry, or a ``via:``
    naming a skill not passed with ``--public-skill``
  * an ``ip`` spec with no ``docs`` entry marked ``cite: true``
  * a fact bullet that does not END with its tag clause (one or more
    ``[tag]``, each optionally followed by a parenthetical citation, then at
    most one closing ``TODO (verify on hardware)`` sentence); a tag in the
    middle of the prose does not count.  A bullet whose text, after an
    optional bold lead-in, starts with ``TODO (verify on hardware)`` is a gap
    and needs no tag
  * a ``[source-observed]`` or ``[press]`` bullet without
    ``TODO (verify on hardware)``; a ``[doc]`` or ``[DT]`` not followed by a
    parenthetical naming its source (for ``[DT]``: the file, and its origin
    when it is a decompiled blob rather than a source ``.dts``)
  * a stub (``--stub PATH``, or every stub found by ``--stubs-from DIR``: a
    ``*/SKILL.md`` whose frontmatter says "stub over") whose ``spec: <id>``
    does not resolve

What warns (reported, exit stays 0):

  * two overlays for the same id in the same layer
  * a part whose ``cache`` differs from its board's

Stdlib only.  PyYAML is used when importable; otherwise a parser for the
YAML subset the format uses (block mappings and lists, flow lists, one-level
flow mappings, folded and literal scalars, comments) reads the frontmatter.
The subset parser rejects ``: `` inside an unquoted scalar, as PyYAML does,
so the two never disagree on that trap.  ``--no-pyyaml`` forces the subset
parser, which is what the tests exercise so the fallback never rots; the
output names the parser that ran (``parser: pyyaml`` or ``parser: subset``).

Exit codes follow the dev-tools/cli-conventions contract:

  0  clean (warnings allowed)
  1  findings
  2  usage error
  3  missing precondition (a root has no board-specs.yaml)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

KINDS = ("board", "soc", "chip", "ip")
LAYERS = ("public", "ip-vendor", "soc-vendor", "product", "local")
REQUIRED = {
    "board": ("kind", "id", "name", "triggers", "parts", "cache"),
    "soc": ("kind", "id", "name", "triggers", "instances"),
    "chip": ("kind", "id", "name", "triggers"),
    "ip": ("kind", "id", "name", "triggers", "resources"),
}
IRQ_KINDS = ("SPI", "PPI", "extended")
FETCH_VALUES = ("ok", "blocked", "truncated")
STATUS_VALUES = ("unmerged", "merged", "superseded")
FACT_SECTIONS = {
    "Quick-facts",
    "Gotchas",
    "Standards and databook",
    "Programming model",
    "Known variants and quirks",
}
TAG_NAMES = "databook|standard|DT|source-observed|doc|hardware|press"
TAG_RE = re.compile(rf"\[({TAG_NAMES})\]")
TODO_RE = re.compile(r"TODO \(verify on hardware\)")
# One tag with an optional parenthetical citation (one level of nesting allowed).
_TAG_CLAUSE = rf"`?\[(?:{TAG_NAMES})\]`?(?:\s*\((?:[^()]|\([^()]*\))*\))?"
# The tail a fact bullet must end with: tag clauses, then at most one TODO sentence.
TAIL_RE = re.compile(
    rf"(?:{_TAG_CLAUSE})(?:\s*[,;]?\s*{_TAG_CLAUSE})*\.?"
    rf"(?:\s*`?TODO \(verify on hardware\)`?[^\[\]]*)?\s*$"
)
GAP_RE = re.compile(r"^- (?:\*\*[^*]+\*\*\s*)?`?TODO \(verify on hardware\)")
# Tags that must be followed by a parenthetical naming their source.
NAMED_TAGS = ("doc", "DT")
UNNAMED_RES = {
    tag: re.compile(rf"\[{tag}\](?:`|(?!`))(?!\s*\()") for tag in NAMED_TAGS
}
DOC_UNNAMED_RE = UNNAMED_RES["doc"]
FRONTMATTER_RE = re.compile(r"\A---\n(.*?)\n---\n(.*)\Z", re.S)


# ----------------------------------------------------------------------------
# YAML subset parser (fallback when PyYAML is absent)
# ----------------------------------------------------------------------------


class YamlError(ValueError):
    pass


def _scalar(text: str, key: str | None = None):
    text = text.strip()
    if text == "" or text == "null" or text == "~":
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if text == "[]":
        return []
    if text.startswith("["):
        if not text.endswith("]"):
            raise YamlError(f"unterminated flow sequence: {text!r}")
        inner = text[1:-1].strip()
        return [_scalar(p) for p in _split_flow(inner)] if inner else []
    if text.startswith("{"):
        if not text.endswith("}"):
            raise YamlError(f"unterminated flow mapping: {text!r}")
        inner = text[1:-1].strip()
        result = {}
        for part in _split_flow(inner) if inner else []:
            fkey, sep, value = part.partition(":")
            if not sep:
                raise YamlError(f"flow mapping entry without a colon: {part!r}")
            result[fkey.strip()] = _scalar(value, fkey.strip())
        return result
    if (text[0] == text[-1]) and text[0] in "\"'" and len(text) >= 2:
        return text[1:-1]
    if ": " in text or text.endswith(":"):
        where = f"the value of {key!r}" if key else "an unquoted value"
        raise YamlError(f"{where} contains ': ' (mapping values are not allowed here); quote it")
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    if re.fullmatch(r"0x[0-9a-fA-F]+", text):
        return int(text, 16)
    return text


def _split_flow(inner: str) -> list[str]:
    parts, buf, quote = [], [], None
    for ch in inner:
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf.append(ch)
        elif ch == ",":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf or not parts:
        parts.append("".join(buf))
    return [p for p in parts if p.strip()]


def _strip_comment(line: str) -> str:
    out, quote = [], None
    for i, ch in enumerate(line):
        if quote:
            out.append(ch)
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            out.append(ch)
        elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
            break
        else:
            out.append(ch)
    return "".join(out).rstrip()


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def parse_yaml_subset(text: str):
    lines = []
    for raw in text.splitlines():
        stripped = _strip_comment(raw)
        if stripped.strip() == "":
            lines.append(None)
        else:
            lines.append(stripped)
    pos = 0

    def skip_blank():
        nonlocal pos
        while pos < len(lines) and lines[pos] is None:
            pos += 1

    def block_scalar(indent: int, style: str) -> str:
        nonlocal pos
        collected = []
        while pos < len(lines):
            line = lines[pos]
            if line is None:
                collected.append("")
                pos += 1
                continue
            if _indent(line) <= indent:
                break
            collected.append(line.strip())
            pos += 1
        while collected and collected[-1] == "":
            collected.pop()
        joiner = "\n" if style.startswith("|") else " "
        return joiner.join(collected)

    def parse_value(after_colon: str, indent: int, key: str | None = None):
        nonlocal pos
        value = after_colon.strip()
        if value in (">", ">-", "|", "|-"):
            pos += 1
            return block_scalar(indent, value)
        if value != "":
            pos += 1
            return _scalar(value, key)
        pos += 1
        skip_blank()
        if pos >= len(lines):
            return None
        nxt = lines[pos]
        if _indent(nxt) <= indent and not nxt.lstrip().startswith("- "):
            return None
        return parse_node(max(_indent(nxt), indent))

    def parse_mapping(indent: int) -> dict:
        nonlocal pos
        result: dict = {}
        while True:
            skip_blank()
            if pos >= len(lines):
                break
            line = lines[pos]
            if _indent(line) < indent:
                break
            if _indent(line) > indent:
                raise YamlError(f"unexpected indentation at line {pos + 1}: {line!r}")
            body = line.strip()
            if body.startswith("- "):
                break
            m = re.match(r"([A-Za-z0-9_.\-]+):(.*)", body)
            if not m:
                raise YamlError(f"expected 'key: value' at line {pos + 1}: {line!r}")
            key, rest = m.group(1), m.group(2)
            result[key] = parse_value(rest, indent, key)
        return result

    def parse_list(indent: int) -> list:
        nonlocal pos
        result: list = []
        while True:
            skip_blank()
            if pos >= len(lines):
                break
            line = lines[pos]
            if _indent(line) != indent or not line.strip().startswith("- "):
                break
            item = line.strip()[2:]
            item_indent = indent + 2
            m = re.match(r"([A-Za-z0-9_.\-]+):(.*)", item)
            if m and not item.startswith(("'", '"', "[")):
                # mapping starting on the dash line: rewrite in place and parse
                lines[pos] = " " * item_indent + item
                result.append(parse_mapping(item_indent))
            else:
                pos += 1
                result.append(_scalar(item))
        return result

    def parse_node(indent: int):
        skip_blank()
        if pos >= len(lines):
            return None
        if lines[pos].strip().startswith("- "):
            return parse_list(_indent(lines[pos]))
        return parse_mapping(indent)

    result = parse_node(0)
    skip_blank()
    if pos < len(lines):
        raise YamlError(f"trailing content at line {pos + 1}: {lines[pos]!r}")
    return result


def _dates_to_strings(node):
    """PyYAML turns ``verified: 2026-09-18`` into a date; the subset parser keeps the string."""
    import datetime

    if isinstance(node, dict):
        return {k: _dates_to_strings(v) for k, v in node.items()}
    if isinstance(node, list):
        return [_dates_to_strings(v) for v in node]
    if isinstance(node, datetime.date):
        return node.isoformat()
    return node


def pyyaml_available() -> bool:
    try:
        import yaml  # type: ignore  # noqa: F401
    except ImportError:
        return False
    return True


def parser_name(use_pyyaml: bool) -> str:
    """Which parser load_yaml will actually run: 'pyyaml' or 'subset'."""
    return "pyyaml" if use_pyyaml and pyyaml_available() else "subset"


def load_yaml(text: str, use_pyyaml: bool):
    if use_pyyaml and pyyaml_available():
        import yaml  # type: ignore

        return _dates_to_strings(yaml.safe_load(text))
    return parse_yaml_subset(text)


# ----------------------------------------------------------------------------
# Model
# ----------------------------------------------------------------------------


@dataclass
class Finding:
    level: str  # "error" | "warning"
    path: str
    message: str


@dataclass
class Spec:
    path: Path
    root: Path
    layer: str
    meta: dict
    body: str

    @property
    def is_overlay(self) -> bool:
        return "overlays" in self.meta

    @property
    def id(self):
        return self.meta.get("overlays") if self.is_overlay else self.meta.get("id")


def read_root(root: Path, use_pyyaml: bool) -> tuple[dict | None, str | None]:
    marker = root / "board-specs.yaml"
    if not marker.exists():
        return None, f"{root}: no board-specs.yaml (not a spec root)"
    try:
        data = load_yaml(marker.read_text(), use_pyyaml) or {}
    except Exception as exc:  # noqa: BLE001
        return None, f"{marker}: cannot parse: {exc}"
    return data, None


def load_specs(
    roots: list[Path], use_pyyaml: bool, findings: list[Finding]
) -> tuple[list[Spec], list[str]]:
    specs: list[Spec] = []
    preconditions: list[str] = []
    for root in roots:
        marker, err = read_root(root, use_pyyaml)
        if err:
            preconditions.append(err)
            continue
        layer = marker.get("layer")
        if layer not in LAYERS:
            findings.append(
                Finding("error", str(root / "board-specs.yaml"), f"unknown layer {layer!r}")
            )
            layer = str(layer)
        for path in sorted(root.rglob("*.spec.md")):
            text = path.read_text()
            m = FRONTMATTER_RE.match(text)
            if not m:
                findings.append(Finding("error", str(path), "no YAML frontmatter"))
                continue
            try:
                meta = load_yaml(m.group(1), use_pyyaml)
            except Exception as exc:  # noqa: BLE001
                findings.append(Finding("error", str(path), f"frontmatter does not parse: {exc}"))
                continue
            if not isinstance(meta, dict):
                findings.append(Finding("error", str(path), "frontmatter is not a mapping"))
                continue
            specs.append(Spec(path, root, layer, meta, m.group(2)))
    return specs, preconditions


# ----------------------------------------------------------------------------
# Checks
# ----------------------------------------------------------------------------


def check_frontmatter(spec: Spec, findings: list[Finding]) -> None:
    p = str(spec.path)
    check_resources(spec, findings)
    if spec.is_overlay:
        if not isinstance(spec.meta.get("overlays"), str):
            findings.append(Finding("error", p, "overlays: must name one spec id"))
        for key in ("kind", "id", "parts"):
            if key in spec.meta:
                findings.append(Finding("error", p, f"an overlay may not carry {key!r}"))
        return
    kind = spec.meta.get("kind")
    if kind not in KINDS:
        findings.append(Finding("error", p, f"unknown kind {kind!r}"))
        return
    for key in REQUIRED[kind]:
        if key not in spec.meta:
            findings.append(Finding("error", p, f"kind {kind}: missing required key {key!r}"))
    if kind == "ip":
        docs = (spec.meta.get("resources") or {}).get("docs") or []
        if not any(isinstance(d, dict) and d.get("cite") is True for d in docs):
            findings.append(Finding("error", p, "ip spec has no docs entry with cite: true"))
    for row in spec.meta.get("instances") or []:
        check_instance_shape(p, row, findings)
    for variant in spec.meta.get("variants") or []:
        if not isinstance(variant, dict) or not variant.get("name"):
            findings.append(Finding("error", p, "variants: entry without a name"))
    if "variant_of" in spec.meta and kind != "board":
        findings.append(Finding("error", p, "variant_of is only valid on a board spec"))


def check_instance_shape(p: str, row, findings: list[Finding]) -> None:
    if not isinstance(row, dict):
        findings.append(Finding("error", p, "instances: row is not a mapping"))
        return
    name = row.get("name")
    reg = row.get("reg")
    if reg is not None and (not isinstance(reg, int) or isinstance(reg, bool)):
        findings.append(
            Finding("error", p, f"instance {name!r}: reg must be an integer or null, not {reg!r}")
        )
    irq = row.get("irq")
    if irq is None:
        return
    if not isinstance(irq, dict):
        findings.append(
            Finding("error", p, f"instance {name!r}: irq must be null or a mapping, not {irq!r}")
        )
        return
    if irq.get("kind") not in IRQ_KINDS:
        findings.append(
            Finding("error", p, f"instance {name!r}: irq.kind must be one of {IRQ_KINDS}")
        )
    number = irq.get("number")
    if not isinstance(number, int) or isinstance(number, bool):
        findings.append(Finding("error", p, f"instance {name!r}: irq.number must be an integer"))
    intid = irq.get("intid")
    if intid is not None and (not isinstance(intid, int) or isinstance(intid, bool)):
        findings.append(Finding("error", p, f"instance {name!r}: irq.intid must be an integer"))
    parent = irq.get("parent")
    if irq.get("kind") == "extended":
        if not isinstance(parent, str) or not parent:
            findings.append(
                Finding("error", p, f"instance {name!r}: irq.kind extended requires irq.parent")
            )
        if intid is not None:
            findings.append(
                Finding("error", p, f"instance {name!r}: irq.intid is not valid for kind extended")
            )
    elif parent is not None:
        findings.append(
            Finding("error", p, f"instance {name!r}: irq.parent is only valid for kind extended")
        )


def check_resources(spec: Spec, findings: list[Finding]) -> None:
    p = str(spec.path)
    for group, entry in iter_resources(spec.meta):
        label = entry.get("name") or entry.get("title") or entry.get("url") or "?"
        if group == "series" and entry.get("cite") is True:
            findings.append(
                Finding("error", p, f"series entry {label!r}: a series is a map, never cite: true")
            )
        fetch = entry.get("fetch")
        if fetch is not None and fetch not in FETCH_VALUES:
            findings.append(
                Finding("error", p, f"{group} entry {label!r}: fetch must be one of {FETCH_VALUES}")
            )
        verified = entry.get("verified")
        if verified is not None and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(verified)):
            findings.append(
                Finding("error", p, f"{group} entry {label!r}: verified must be an ISO date (YYYY-MM-DD)")
            )
        status = entry.get("status")
        if status is not None and status not in STATUS_VALUES:
            findings.append(
                Finding("error", p, f"{group} entry {label!r}: status must be one of {STATUS_VALUES}")
            )
        for item in entry.get("files") or []:
            if isinstance(item, str):
                continue
            if not isinstance(item, dict) or not item.get("path"):
                findings.append(
                    Finding("error", p, f"{group} entry {label!r}: files entry must be a path or a mapping with path")
                )
                continue
            fstatus = item.get("status")
            if fstatus is not None and fstatus not in STATUS_VALUES:
                findings.append(
                    Finding(
                        "error",
                        p,
                        f"{group} entry {label!r}: file {item['path']!r}: status must be one of {STATUS_VALUES}",
                    )
                )


def iter_resources(meta: dict):
    resources = meta.get("resources") or {}
    if not isinstance(resources, dict):
        return
    for group, entries in resources.items():
        for entry in entries or []:
            if isinstance(entry, dict):
                yield group, entry


def check_public(spec: Spec, public_skills: set[str], findings: list[Finding]) -> None:
    if spec.layer != "public":
        return
    p = str(spec.path)
    for group, entry in iter_resources(spec.meta):
        label = entry.get("name") or entry.get("title") or entry.get("url") or "?"
        if entry.get("access") == "internal":
            findings.append(
                Finding("error", p, f"{group} entry {label!r}: access: internal under a public root")
            )
        via = entry.get("via")
        if isinstance(via, str):
            skill = via.split(":", 1)[1] if via.startswith("skill:") else via
            if skill not in public_skills:
                findings.append(
                    Finding(
                        "error",
                        p,
                        f"{group} entry {label!r}: via {via!r} is not a public skill "
                        "(pass --public-skill NAME if it is)",
                    )
                )


def check_references(specs: list[Spec], findings: list[Finding]) -> None:
    by_id: dict[str, list[Spec]] = {}
    for spec in specs:
        if not spec.is_overlay and isinstance(spec.id, str):
            by_id.setdefault(spec.id, []).append(spec)
    for sid, owners in by_id.items():
        if len(owners) > 1:
            for owner in owners:
                findings.append(
                    Finding("error", str(owner.path), f"duplicate id {sid!r} ({len(owners)} specs)")
                )
    overlays_seen: dict[tuple[str, str], list[Spec]] = {}
    for spec in specs:
        p = str(spec.path)
        if spec.is_overlay:
            target = spec.meta.get("overlays")
            if target not in by_id:
                findings.append(Finding("error", p, f"overlays {target!r} resolves to nothing"))
            overlays_seen.setdefault((str(target), spec.layer), []).append(spec)
            continue
        base = spec.meta.get("variant_of")
        if base is not None:
            if base not in by_id:
                findings.append(Finding("error", p, f"variant_of {base!r} resolves to nothing"))
            elif by_id[base][0].meta.get("kind") != "board":
                findings.append(Finding("error", p, f"variant_of {base!r} is not a board spec"))
        for part in spec.meta.get("parts") or []:
            if part not in by_id:
                findings.append(Finding("error", p, f"parts entry {part!r} resolves to nothing"))
                continue
            part_cache = by_id[part][0].meta.get("cache")
            if part_cache and spec.meta.get("cache") and part_cache != spec.meta.get("cache"):
                findings.append(
                    Finding(
                        "warning",
                        p,
                        f"part {part!r} names cache {part_cache!r}, this board {spec.meta.get('cache')!r}",
                    )
                )
        for row in spec.meta.get("instances") or []:
            if not isinstance(row, dict):
                continue
            ip = row.get("ip")
            if ip not in by_id:
                findings.append(
                    Finding("error", p, f"instance {row.get('name')!r}: ip {ip!r} resolves to nothing")
                )
            elif by_id[ip][0].meta.get("kind") != "ip":
                findings.append(
                    Finding("error", p, f"instance {row.get('name')!r}: {ip!r} is not an ip spec")
                )
    for (target, layer), owners in overlays_seen.items():
        if len(owners) > 1:
            for owner in owners:
                findings.append(
                    Finding(
                        "warning",
                        str(owner.path),
                        f"{len(owners)} overlays for {target!r} in layer {layer!r}; merge order undefined",
                    )
                )


def iter_fact_bullets(body: str):
    """Yield (line_number, bullet_text) for every top-level bullet in a fact section."""
    section = None
    current: list[str] = []
    start = 0
    for n, line in enumerate(body.splitlines(), 1):
        if line.startswith("## "):
            if current:
                yield start, "\n".join(current)
                current = []
            section = line[3:].strip()
            continue
        if section not in FACT_SECTIONS:
            continue
        if line.startswith("- "):
            if current:
                yield start, "\n".join(current)
            current = [line]
            start = n
        elif current and (line.startswith("  ") or line.strip() == ""):
            if line.strip():
                current.append(line)
        elif current:
            yield start, "\n".join(current)
            current = []
    if current:
        yield start, "\n".join(current)


def check_tags(spec: Spec, findings: list[Finding]) -> None:
    p = str(spec.path)
    for line_no, raw in iter_fact_bullets(spec.body):
        where = f"{p}:{line_no}"
        if GAP_RE.match(raw):
            continue  # a gap-only bullet: "- **Topic.** TODO (verify on hardware) ..."
        bullet = " ".join(line.strip() for line in raw.splitlines())
        tags = TAG_RE.findall(bullet)
        has_todo = bool(TODO_RE.search(bullet))
        if not tags:
            findings.append(Finding("error", where, "fact bullet has no provenance tag"))
            continue
        if not TAIL_RE.search(bullet):
            findings.append(
                Finding(
                    "error",
                    where,
                    "fact bullet does not end with its tag clause "
                    "(tags, each with an optional parenthetical, then at most one TODO sentence)",
                )
            )
        for needs_todo in ("source-observed", "press"):
            if needs_todo in tags and not has_todo:
                findings.append(
                    Finding("error", where, f"[{needs_todo}] fact without 'TODO (verify on hardware)'")
                )
        for tag, unnamed_re in UNNAMED_RES.items():
            if unnamed_re.search(bullet):
                what = "its source" if tag == "doc" else "the file (and its origin, for a blob)"
                findings.append(
                    Finding("error", where, f"[{tag}] must be followed by a parenthetical naming {what}")
                )


STUB_RE = re.compile(r"`spec:\s*([a-z0-9][a-z0-9\-]*)`")


def find_stubs(skills_dir: Path) -> list[Path]:
    """Every */SKILL.md under skills_dir whose frontmatter calls itself a stub."""
    stubs = []
    for path in sorted(skills_dir.glob("*/SKILL.md")):
        m = FRONTMATTER_RE.match(path.read_text())
        if m and "stub over" in m.group(1):
            stubs.append(path)
    return stubs


def check_stub(path: Path, ids: set[str], findings: list[Finding]) -> None:
    if not path.exists():
        findings.append(Finding("error", str(path), "stub file not found"))
        return
    found = STUB_RE.findall(path.read_text())
    if not found:
        findings.append(Finding("error", str(path), "stub names no `spec: <id>`"))
        return
    for sid in found:
        if sid not in ids:
            findings.append(Finding("error", str(path), f"stub spec id {sid!r} resolves to nothing"))


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("roots", nargs="+", type=Path, help="spec root directories")
    parser.add_argument(
        "--stub", action="append", default=[], type=Path, help="a stub SKILL.md to check"
    )
    parser.add_argument(
        "--stubs-from",
        action="append",
        default=[],
        type=Path,
        help="a plugin skills directory; every */SKILL.md whose frontmatter says 'stub over' is checked",
    )
    parser.add_argument(
        "--public-skill",
        action="append",
        default=[],
        help="a skill name that may appear in via: under a public root",
    )
    parser.add_argument("--no-pyyaml", action="store_true", help="force the subset parser")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)

    findings: list[Finding] = []
    use_pyyaml = not args.no_pyyaml
    parser_used = parser_name(use_pyyaml)
    specs, preconditions = load_specs(args.roots, use_pyyaml, findings)
    if preconditions:
        for msg in preconditions:
            print(f"missing precondition: {msg}", file=sys.stderr)
        return 3

    public_skills = set(args.public_skill)
    for spec in specs:
        check_frontmatter(spec, findings)
        check_public(spec, public_skills, findings)
        check_tags(spec, findings)
    check_references(specs, findings)
    ids = {s.id for s in specs if not s.is_overlay and isinstance(s.id, str)}
    stubs = list(args.stub)
    for skills_dir in args.stubs_from:
        if not skills_dir.is_dir():
            print(f"missing precondition: {skills_dir} is not a directory", file=sys.stderr)
            return 3
        stubs += find_stubs(skills_dir)
    for stub in stubs:
        check_stub(stub, ids, findings)

    errors = [f for f in findings if f.level == "error"]
    warnings = [f for f in findings if f.level == "warning"]
    if args.json:
        json.dump(
            {
                "specs": len(specs),
                "stubs": len(stubs),
                "parser": parser_used,
                "findings": [asdict(f) for f in findings],
            },
            sys.stdout,
            indent=2,
        )
        sys.stdout.write("\n")
    else:
        for f in findings:
            print(f"{f.level}: {f.path}: {f.message}", file=sys.stderr)
        if errors:
            print(
                f"FAIL: {len(errors)} error(s), {len(warnings)} warning(s) (parser: {parser_used})",
                file=sys.stderr,
            )
        else:
            print(
                f"OK: {len(specs)} specs checked, {len(warnings)} warning(s) (parser: {parser_used})"
            )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
