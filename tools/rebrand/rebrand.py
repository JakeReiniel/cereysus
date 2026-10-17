#!/usr/bin/env python3
"""Cereysus rebrand tool: classify and rename product-name hits, idempotently.

The rename is applied by this script, not by hand, so that it can be re-run
after every upstream merge (see docs/cereysus/SYNC.md).  Rules live in
``rebrand-map.yml`` next to this file.

  python tools/rebrand/rebrand.py                    dry run: unified diff + residual-hit report
  python tools/rebrand/rebrand.py --apply            write the changes (safe to re-run)
  python tools/rebrand/rebrand.py --inventory FILE   write the classified inventory (markdown)
  python tools/rebrand/rebrand.py --check            exit 1 if changes are pending or a hit is unreviewed

Path policies (rebrand-map.yml): freeze = T0 file, hold = classify only, text = rename user-visible text,
skip = Cereysus-owned file that names the old name on purpose (not counted).

Tiers (see the Development Prompt, section 6.2)
  T0  never changed (licence, provenance, upstream org URLs, copyright)
  T1  user-visible text: renamed by this script
  T2  operator-facing names: renamed where decision DEC-1 says so
  T3  internal identifiers (env vars, keys, headers, CSS prefixes, comments): kept
  R   flagged for owner review, left unchanged

Only the standalone capitalised word is renamed in runtime text.  Identifiers,
URLs, headers, paths and source-code comments/docstrings are classified and left
alone, which keeps diffs small and upstream merges cheap.
"""
from __future__ import annotations

import argparse
import ast
import bisect
import difflib
import io
import os
import re
import subprocess
import sys
import tokenize
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("rebrand.py needs PyYAML:  pip install pyyaml")

HERE = Path(__file__).resolve().parent
NAME_RE = re.compile("odysseus", re.I)
OLD, NEW = "Odysseus", "Cereysus"
TIER_ORDER = ["T0", "T1", "T2", "T3", "R"]
TIER_TITLE = {
    "T0": "never change",
    "T1": "user-visible text, renamed",
    "T2": "operator-facing names (DEC-1)",
    "T3": "internal identifiers and developer text, kept (DEC-2)",
    "R": "flagged for owner review, left unchanged",
}


# --------------------------------------------------------------------------- config
def glob_to_re(pattern: str) -> re.Pattern:
    out, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                i += 2
                if pattern[i:i + 1] == "/":
                    out.append("(?:.*/)?")
                    i += 1
                else:
                    out.append(".*")
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "$")


def _globs(value) -> list[re.Pattern]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    return [glob_to_re(v) for v in value]


@dataclass
class Policy:
    globs: list
    action: str            # freeze | text | hold
    tier: str
    why: str = ""
    comments_text: bool = False    # treat code comments as runtime text (config templates, scripts)
    docstrings_text: bool = False  # treat docstrings as runtime text (tool descriptions)

    def matches(self, rel: str) -> bool:
        return any(g.match(rel) for g in self.globs)


@dataclass
class Protect:
    rx: re.Pattern
    tier: str
    kind: str
    why: str
    files: list


@dataclass
class KeepLine:
    id: str
    files: list
    rx: re.Pattern
    tier: str
    kind: str
    why: str


@dataclass
class Rule:
    id: str
    files: list
    find: str
    replace: str
    regex: bool
    count: object          # int or "any"
    optional: bool
    tier: str
    why: str


class Config:
    def __init__(self, data: dict):
        self.verified_against = data.get("verified_against", "")
        self.policies = []
        for p in data["paths"]:
            self.policies.append(Policy(
                globs=_globs(p.get("globs", p.get("glob"))), action=p["action"], tier=p["tier"],
                why=p.get("why", ""), comments_text=bool(p.get("comments_text")),
                docstrings_text=bool(p.get("docstrings_text"))))
        self.protect = [Protect(re.compile(p["re"], re.M), p["tier"], p["kind"], p.get("why", ""),
                                _globs(p.get("files", p.get("file")))) for p in data.get("protect", [])]
        self.keep_lines = [KeepLine(k["id"], _globs(k.get("files", k.get("file"))), re.compile(k["re"]), k["tier"],
                                    k.get("kind", "keep"), k.get("why", "")) for k in data.get("keep_lines", [])]
        self.rules = [Rule(r["id"], _globs(r.get("files", r.get("file"))), r["find"], r["replace"],
                           bool(r.get("regex")), r.get("count", 1), bool(r.get("optional")),
                           r.get("tier", "T1"), r.get("why", "")) for r in data.get("rules", [])]
        self.renames = data.get("renames", [])

    def policy_for(self, rel: str) -> Policy:
        for p in self.policies:
            if p.matches(rel):
                return p
        raise SystemExit(f"rebrand-map.yml has no path policy for {rel}; add a catch-all '**' entry")

    def rename_for(self, rel: str) -> Optional[dict]:
        for r in self.renames:
            if r["from"] == rel:
                return r
        return None


def load_config(path: Path) -> Config:
    cfg = Config(yaml.safe_load(path.read_text(encoding="utf-8")))
    cfg.map_path = path.resolve()  # the map names the old name on purpose: never rewrite it
    return cfg


# --------------------------------------------------------------------------- spans
def line_starts(text: str) -> list[int]:
    starts, pos = [0], 0
    while True:
        j = text.find("\n", pos)
        if j == -1:
            return starts
        pos = j + 1
        starts.append(pos)


def _bcol_to_ccol(line: str, col: int) -> int:
    return len(line.encode("utf-8")[:col].decode("utf-8", "ignore"))


def py_spans(text: str):
    """Comment and docstring spans of Python source, or None if it does not parse."""
    starts = line_starts(text)
    lines = text.split("\n")
    spans = []
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                spans.append((starts[tok.start[0] - 1] + tok.start[1], starts[tok.end[0] - 1] + tok.end[1], "comment"))
        tree = ast.parse(text)
    except (tokenize.TokenError, SyntaxError, ValueError):
        return None
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                s = starts[first.lineno - 1] + _bcol_to_ccol(lines[first.lineno - 1], first.col_offset)
                e = starts[first.end_lineno - 1] + _bcol_to_ccol(lines[first.end_lineno - 1], first.end_col_offset)
                spans.append((s, e, "docstring"))
    return spans


def c_spans(text: str, base: int = 0, line_comments: bool = True):
    """Comment spans of C-like source (JS, CSS, Swift). Strings and template literals are skipped."""
    spans, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c in "'\"":
            i += 1
            while i < n and text[i] != c and text[i] != "\n":
                i += 2 if text[i] == "\\" else 1
            i += 1
        elif c == "`":
            i, depth = i + 1, 0
            while i < n:
                if text[i] == "\\":
                    i += 2
                    continue
                if text[i] == "`" and depth == 0:
                    i += 1
                    break
                if text[i:i + 2] == "${":
                    depth += 1
                    i += 2
                    continue
                if text[i] == "}" and depth:
                    depth -= 1
                i += 1
        elif c == "/" and line_comments and text[i + 1:i + 2] == "/":
            j = text.find("\n", i)
            j = n if j == -1 else j
            spans.append((base + i, base + j, "comment"))
            i = j
        elif c == "/" and text[i + 1:i + 2] == "*":
            j = text.find("*/", i + 2)
            j = n if j == -1 else j + 2
            spans.append((base + i, base + j, "comment"))
            i = j
        else:
            i += 1
    return spans


def html_spans(text: str):
    spans = [(m.start(), m.end(), "comment") for m in re.finditer(r"<!--.*?-->", text, re.S)]
    for m in re.finditer(r"<script\b[^>]*>(.*?)</script>", text, re.S | re.I):
        spans += c_spans(m.group(1), m.start(1))
    for m in re.finditer(r"<style\b[^>]*>(.*?)</style>", text, re.S | re.I):
        spans += c_spans(m.group(1), m.start(1), line_comments=False)
    return spans


def hash_spans(text: str):
    spans, pos = [], 0
    for line in text.splitlines(keepends=True):
        body = line.lstrip()
        if body.startswith("#"):
            spans.append((pos + len(line) - len(body), pos + len(line.rstrip("\r\n")), "comment"))
        pos += len(line)
    return spans


def comment_spans(rel: str, text: str, pol: Policy):
    p = Path(rel)
    ext, name = p.suffix.lower(), p.name
    spans = None
    if ext == ".py" or ext == ".spec":
        spans = py_spans(text)
        if spans is None:
            spans = hash_spans(text)
    elif ext in (".js", ".mjs", ".cjs", ".ts", ".swift"):
        spans = c_spans(text)
    elif ext == ".css":
        spans = c_spans(text, line_comments=False)
    elif ext in (".html", ".htm"):
        spans = html_spans(text)
    elif ext == ".md":
        spans = [(m.start(), m.end(), "comment") for m in re.finditer(r"<!--.*?-->", text, re.S)]
    elif ext in (".sh", ".bash", ".zsh", ".yml", ".yaml", ".toml", ".service", ".ps1", ".cfg", ".ini", ".txt") \
            or name in (".env.example", ".gitignore", ".dockerignore", "Dockerfile"):
        spans = hash_spans(text)
    spans = spans or []
    return [s for s in spans if not ((s[2] == "comment" and pol.comments_text) or (s[2] == "docstring" and pol.docstrings_text))]


def span_kind(spans, pos: int) -> Optional[str]:
    for s, e, kind in spans:
        if s <= pos < e:
            return kind
    return None


# --------------------------------------------------------------------------- hits
@dataclass
class Hit:
    path: str
    line: int
    col: int
    match: str
    tier: str
    kind: str
    why: str
    changed: bool
    snippet: str


@dataclass
class FileResult:
    path: str
    policy: Policy
    hits: list = field(default_factory=list)
    new_text: Optional[str] = None
    drift: list = field(default_factory=list)


def _lower_kind(text: str, s: int, e: int) -> str:
    b = text[s - 1] if s else ""
    a = text[e] if e < len(text) else ""
    if b == "[" and a == "]":
        return "log-tag"
    if b in "/\\" or a in "/\\":
        return "path-or-url"
    if b in "_-.:" or a in "_-.:" or b.isalnum() or a.isalnum():
        return "identifier"
    return "bare-lowercase"


def _apply_edits(text: str, edits: list, rel: str = "?") -> str:
    edits = sorted(edits, key=lambda e: e[0])
    for (s1, e1, _), (s2, _e2, _n) in zip(edits, edits[1:]):
        if s2 < e1:
            raise SystemExit(f"{rel}: overlapping edits at offsets {s1}-{e1} and {s2}")
    for s, e, new in reversed(edits):
        text = text[:s] + new + text[e:]
    return text


def process_file(cfg: Config, rel: str, text: str) -> FileResult:
    pol = cfg.policy_for(rel)
    res = FileResult(rel, pol)
    starts = line_starts(text)
    lines_cache = {}

    def locate(pos: int):
        ln = bisect.bisect_right(starts, pos) - 1
        if ln not in lines_cache:
            end = starts[ln + 1] - 1 if ln + 1 < len(starts) else len(text)
            lines_cache[ln] = text[starts[ln]:end].rstrip("\r")
        return ln + 1, pos - starts[ln] + 1, lines_cache[ln].strip()[:200].rstrip()

    edits, rule_spans = [], []
    # explicit rules (run first; their spans are owned by the rule)
    if pol.action != "freeze":
        for r in cfg.rules:
            if not any(g.match(rel) for g in r.files):
                continue
            if r.regex:
                found = [(m.start(), m.end(), m.expand(r.replace)) for m in re.finditer(r.find, text, re.M)]
            else:
                found, i = [], 0
                while True:
                    j = text.find(r.find, i)
                    if j == -1:
                        break
                    found.append((j, j + len(r.find), r.replace))
                    i = j + len(r.find)
            if not found:
                if not r.optional and r.replace not in text:
                    res.drift.append(f"rule '{r.id}' found nothing in {rel} (upstream text changed?)")
                continue
            if r.count != "any" and len(found) != r.count:
                res.drift.append(f"rule '{r.id}' matched {len(found)}x in {rel}, expected {r.count}")
            for s, e, new in found:
                if any(s < ae and as_ < e for as_, ae, _ in rule_spans):
                    continue  # an earlier rule already owns this text
                edits.append((s, e, new))
                rule_spans.append((s, e, r))
        for s, e, r in rule_spans:
            for m in NAME_RE.finditer(text, s, e):
                ln, col, snip = locate(m.start())
                res.hits.append(Hit(rel, ln, col, m.group(), r.tier, f"rule:{r.id}", r.why, True, snip))

    if NAME_RE.search(text):
        spans = comment_spans(rel, text, pol) if pol.action != "freeze" else []
        prot = []
        for p in cfg.protect:
            if p.files and not any(g.match(rel) for g in p.files):
                continue
            prot += [(m.start(), m.end(), p) for m in p.rx.finditer(text)]
        keeps = []
        for k in cfg.keep_lines:
            if not any(g.match(rel) for g in k.files):
                continue
            for i, st in enumerate(starts):
                en = starts[i + 1] if i + 1 < len(starts) else len(text)
                if k.rx.search(text[st:en]):
                    keeps.append((st, en, k))
        for m in NAME_RE.finditer(text):
            s, e = m.span()
            if any(rs <= s < re_ for rs, re_, _ in rule_spans):
                continue
            ln, col, snip = locate(s)
            tok = m.group()
            tier = kind = why = None
            changed = False
            if pol.action == "freeze":
                tier, kind, why = pol.tier, "frozen", pol.why
            if tier is None:
                for ps, pe, p in prot:
                    if ps < e and s < pe:
                        tier, kind, why = p.tier, p.kind, p.why
                        break
            if tier is None:
                for ks, ke, k in keeps:
                    if ks <= s < ke:
                        tier, kind, why = k.tier, k.kind, k.why
                        break
            if tier is None:
                b = text[s - 1] if s else ""
                a = text[e] if e < len(text) else ""
                if tok.isupper():
                    tier, kind, why = "T3", "env-var" if "_" in (a, b) else "constant", "upper-case identifier"
                elif tok.islower():
                    tier, kind, why = "T3", _lower_kind(text, s, e), "lower-case identifier, path, key or URL"
                elif tok != OLD:
                    tier, kind, why = "T3", "identifier", "mixed-case identifier"
                elif b.isalnum() or b == "_" or a.isalnum() or a == "_":
                    tier, kind, why = "T3", "identifier", "part of a larger identifier"
                elif re.match(r"-[A-Z]|/\d", text[e:e + 2]):
                    tier, kind, why = "T3", "wire-id", "protocol or User-Agent identifier"
                else:
                    sk = span_kind(spans, s)
                    if sk:
                        tier, kind, why = "T3", sk, "developer-facing text, kept to keep merges cheap"
                    elif pol.action == "text":
                        tier, kind, why, changed = pol.tier, "text", pol.why or "user-visible text", True
                        art = re.search(r"(?<![A-Za-z])([Aa])n(\s+)$", text[max(0, s - 8):s])
                        if art:
                            edits.append((s - len(art.group(0)), e, art.group(1) + art.group(2) + NEW))
                        else:
                            edits.append((s, e, NEW))
                    else:
                        tier, kind, why = pol.tier, "held-text", pol.why
            res.hits.append(Hit(rel, ln, col, tok, tier, kind, why, changed, snip))

    if edits:
        res.new_text = _apply_edits(text, edits, rel)
        if res.new_text == text:
            res.new_text = None
    res.hits.sort(key=lambda h: (h.line, h.col))
    return res


# --------------------------------------------------------------------------- repo walk
def repo_files(root: Path) -> list[str]:
    try:
        # tracked and untracked-but-not-ignored files, so a re-run before `git add` still sees renames
        out = subprocess.run(["git", "-C", str(root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                             capture_output=True, check=True).stdout.decode("utf-8")
        return sorted({p for p in out.split("\0") if p and (root / p).exists()})
    except Exception:
        found = []
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if x != ".git"]
            found += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, "/") for f in fs]
        return sorted(found)


def read_text(path: Path) -> Optional[str]:
    try:
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:8192]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return None


def run(root: Path, cfg: Config):
    results, skipped = [], []
    for rel in repo_files(root):
        if (root / rel).resolve() == getattr(cfg, "map_path", None):
            continue
        pol = cfg.policy_for(rel)
        if pol.action == "skip":
            continue
        text = read_text(root / rel)
        if text is None:
            skipped.append(rel)
            continue
        if pol.action == "freeze" and not NAME_RE.search(text):
            continue
        res = process_file(cfg, rel, text)
        if res.hits or res.new_text is not None or res.drift:
            results.append((res, text))
    return results, skipped


# --------------------------------------------------------------------------- reports
def count_hits(results):
    tiers = Counter()
    kinds = Counter()
    for res, _ in results:
        for h in res.hits:
            tiers[h.tier] += 1
            kinds[(h.tier, h.kind, h.changed)] += 1
    return tiers, kinds


def name_hits_in_paths(files: list[str], cfg: Config):
    rows = []
    for rel in files:
        if NAME_RE.search(rel):
            pol = cfg.policy_for(rel)
            if pol.action == "skip":
                continue
            ren = cfg.rename_for(rel)
            if ren:
                rows.append((rel, "T2", f"renamed to {ren['to']}", ren.get("why", "")))
            else:
                rows.append((rel, pol.tier, "kept", pol.why))
    return rows


def print_report(results, skipped, cfg, files, pending, out=sys.stdout):
    tiers, kinds = count_hits(results)
    print("\n== residual-hit report ==", file=out)
    print(f"files with hits: {len(results)}   binary/unreadable skipped: {len(skipped)}", file=out)
    for t in TIER_ORDER:
        print(f"  {t:<3} {tiers[t]:>5} hits  - {TIER_TITLE[t]}", file=out)
    changed = sum(n for (_t, _k, c), n in kinds.items() if c)
    print(f"\n  changed by this run: {changed} hit(s) in {pending} file(s)", file=out)
    print("\n  by tier / kind (kept unless marked *):", file=out)
    for (t, k, c), n in sorted(kinds.items(), key=lambda x: (TIER_ORDER.index(x[0][0]), -x[1])):
        print(f"    {t:<3} {k:<18}{'*' if c else ' '} {n:>5}", file=out)
    review = [h for res, _ in results for h in res.hits if h.tier == "R"]
    if review:
        print(f"\n  flagged for review (R), first 40 of {len(review)}:", file=out)
        for h in review[:40]:
            print(f"    {h.path}:{h.line}  [{h.kind}] {h.why}", file=out)
    drift = [d for res, _ in results for d in res.drift]
    if drift:
        print("\n  RULE DRIFT (map needs attention):", file=out)
        for d in drift:
            print("    " + d, file=out)
    ren = [r for r in cfg.renames if r["from"] in files]
    for r in ren:
        print(f"  rename pending: {r['from']} -> {r['to']}", file=out)
    return drift


def make_diff(results, root: Path) -> str:
    chunks = []
    for res, text in results:
        if res.new_text is not None:
            chunks.append("".join(difflib.unified_diff(
                text.splitlines(keepends=True), res.new_text.splitlines(keepends=True),
                f"a/{res.path}", f"b/{res.path}", n=2)))
    return "".join(chunks)


THEMED = re.compile(r"\b(Ithaca|Ithacan|Penelope|Telemachus|Laertes|Polyphemus|Cyclops|Calypso|Circe|Aeolus|Scylla|"
                    r"Charybdis|Argos|Nobody mode|Homer|Odyssey|voyage|voyages|voyaging|set sail|sailing|sail)\b", re.I)


def write_inventory(path: Path, results, skipped, cfg, files, root: Path, withhold: set, header_extra: str):
    tiers, kinds = count_hits(results)
    lines_by_tier = defaultdict(set)
    files_by_tier = defaultdict(set)
    for res, _ in results:
        for h in res.hits:
            lines_by_tier[h.tier].add((h.path, h.line))
            files_by_tier[h.tier].add(h.path)
    out = io.StringIO()
    w = lambda s="": out.write(s + "\n")  # noqa: E731
    w("# Rebrand inventory")
    w()
    w(header_extra.rstrip())
    w()
    w("Every occurrence of the product name (any case) in a text file, classified by the tiers of the")
    w("Development Prompt (section 6.2). Generated by `tools/rebrand/rebrand.py --inventory`, so it can be")
    w("regenerated after every upstream sync. Rules live in `tools/rebrand/rebrand-map.yml`.")
    w()
    w("## 1. Summary")
    w()
    w("| Tier | Meaning | Hits | Lines | Files |")
    w("|---|---|---:|---:|---:|")
    for t in TIER_ORDER:
        w(f"| {t} | {TIER_TITLE[t]} | {tiers[t]} | {len(lines_by_tier[t])} | {len(files_by_tier[t])} |")
    total_lines = len({x for s in lines_by_tier.values() for x in s})
    w(f"| **all** | | **{sum(tiers.values())}** | **{total_lines}** | **{len({r.path for r, _ in results if r.hits})}** |")
    w()
    w(f"Binary or unreadable files skipped: {len(skipped)}. File names containing the name: see section 3.")
    w()
    w("Classification rules, in order: (1) path policy `freeze` (T0 files); (2) protected patterns (upstream org URLs, HTTP")
    w("headers, User-Agent and PRODID strings, persisted functional markers); (3) keep-lines (quotations, owner-review lines);")
    w("(4) token shape: UPPER or lower case, or part of a larger identifier, is T3; (5) a standalone capitalised word inside a")
    w("source comment or docstring is T3 developer text; (6) any other standalone capitalised word is user-visible text: T1 and")
    w("renamed where the path policy is `text`, otherwise labelled with the policy tier (`held-text`).")
    w()
    w("## 2. Hits by tier and kind")
    w()
    w("| Tier | Kind | Action | Hits |")
    w("|---|---|---|---:|")
    for (t, k, c), n in sorted(kinds.items(), key=lambda x: (TIER_ORDER.index(x[0][0]), -x[1])):
        w(f"| {t} | {k} | {'renamed' if c else 'kept'} | {n} |")
    w()
    w("## 3. File names containing the name")
    w()
    w("| File | Tier | Action | Note |")
    w("|---|---|---|---|")
    for rel, tier, action, why in name_hits_in_paths(files, cfg):
        w(f"| `{rel}` | {tier} | {action} | {why} |")
    w()

    def listing(title, tier_filter, changed=None, limit_kind_summary=False):
        w(title)
        w()
        by_file = defaultdict(list)
        for res, _ in results:
            for h in res.hits:
                if tier_filter(h) and (changed is None or h.changed == changed):
                    by_file[h.path].append(h)
        n = sum(len(v) for v in by_file.values())
        w(f"{n} hit(s) in {len(by_file)} file(s).")
        w()
        for p in sorted(by_file):
            w(f"**`{p}`** ({len(by_file[p])})")
            w()
            for h in by_file[p]:
                snip = "(text withheld)" if (p, h.line) in withhold or (p, 0) in withhold else h.snippet.replace("|", "\\|").replace("`", "'")
                w(f"- L{h.line} `{h.kind}`: {snip}")
            w()

    listing("## 4. T1 and T2 hits that this tool renames (every line)", lambda h: h.changed)
    listing("## 5. R: flagged for owner review, left unchanged (every line)", lambda h: h.tier == "R" and not h.changed)

    w("## 6. T0 and T3 hits, per file (kept)")
    w()
    w("| File | T0 | T3 | Kinds |")
    w("|---|---:|---:|---|")
    per = defaultdict(lambda: [0, 0, Counter()])
    for res, _ in results:
        for h in res.hits:
            if h.tier in ("T0", "T3") and not h.changed:
                per[h.path][0 if h.tier == "T0" else 1] += 1
                per[h.path][2][h.kind] += 1
    for p in sorted(per):
        t0, t3, ks = per[p]
        w(f"| `{p}` | {t0} | {t3} | {', '.join(f'{k} {n}' for k, n in ks.most_common())} |")
    w()

    w("## 7. Odyssey-themed copy not matched by the name rule (flagged for review)")
    w()
    w("Words from the epic that appear in feature copy or comments. They are not renamed by this tool.")
    w("Test files, upstream engineering docs and the upstream website are counted but not listed line by line.")
    w()
    themed_files = Counter()
    listed = []
    for rel in files:
        if cfg.policy_for(rel).action in ("freeze", "skip"):
            continue
        text = read_text(root / rel)
        if text is None:
            continue
        starts = line_starts(text)
        for m in THEMED.finditer(text):
            themed_files[rel] += 1
            if not re.match(r"(tests|docs|plans|specs|website|scripts|\.github)/", rel):
                ln = bisect.bisect_right(starts, m.start())
                end = starts[ln] if ln < len(starts) else len(text)
                snip = text[starts[ln - 1]:end].strip()[:160].rstrip()
                listed.append((rel, ln, m.group(), snip))
    seen = set()
    for rel, ln, word, snip in listed:
        if (rel, ln) in seen:
            continue
        seen.add((rel, ln))
        shown = "(text withheld)" if (rel, ln) in withhold else snip.replace("|", "\\|").replace("`", "'")
        w(f"- `{rel}:{ln}` ({word}): {shown}")
    w()
    other = sorted(((n, p) for p, n in themed_files.items() if re.match(r"(tests|docs|plans|specs|website|scripts|\.github)/", p)), reverse=True)
    w(f"Counted only: {sum(n for n, _ in other)} match(es) in {len(other)} file(s) under tests, docs, plans, specs, website, scripts and .github.")
    w()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(out.getvalue().rstrip("\n") + "\n", encoding="utf-8", newline="\n")


# --------------------------------------------------------------------------- main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Cereysus rebrand tool (dry run by default).")
    ap.add_argument("--root", default=None, help="repository root (default: git top-level of the cwd)")
    ap.add_argument("--map", default=str(HERE / "rebrand-map.yml"))
    ap.add_argument("--apply", action="store_true", help="write the changes")
    ap.add_argument("--check", action="store_true", help="exit 1 if changes are pending or rules drifted")
    ap.add_argument("--inventory", metavar="FILE", help="write the classified inventory (markdown) to FILE")
    ap.add_argument("--inventory-note", default="", help="extra header text for the inventory")
    ap.add_argument("--withhold", metavar="FILE", help="file of 'path:line' (or 'path') entries whose text is not printed")
    ap.add_argument("--diff-out", metavar="FILE", help="write the unified diff to FILE instead of stdout")
    args = ap.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # Windows consoles and pipes default to a legacy code page
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    root = Path(args.root) if args.root else Path(subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip())
    cfg = load_config(Path(args.map))
    files = repo_files(root)
    results, skipped = run(root, cfg)
    pending = sum(1 for r, _ in results if r.new_text is not None)
    renames = [r for r in cfg.renames if r["from"] in files]

    withhold = set()
    if args.withhold:
        for ln in Path(args.withhold).read_text(encoding="utf-8").splitlines():
            m = re.match(r"^(.+?):(\d+)$", ln.strip())
            if m:
                withhold.add((m.group(1), int(m.group(2))))
            elif ln.strip() and not ln.startswith("exclusion scan"):
                withhold.add((ln.strip().split(" ")[0], 0))

    if args.inventory:
        write_inventory(Path(args.inventory), results, skipped, cfg, files, root, withhold, args.inventory_note)
        print(f"inventory written: {args.inventory}")

    if args.apply:
        for res, text in results:
            if res.new_text is not None:
                (root / res.path).write_bytes(res.new_text.encode("utf-8"))
        for r in renames:
            src, dst = root / r["from"], root / r["to"]
            if dst.exists():
                print(f"WARNING: cannot rename {r['from']}: {r['to']} already exists", file=sys.stderr)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                os.replace(src, dst)
        print(f"applied: {pending} file(s) edited, {len(renames)} file(s) renamed")
        again, again_skipped = run(root, cfg)
        left = [r.path for r, _ in again if r.new_text is not None]
        drift = print_report(again, again_skipped, cfg, repo_files(root), len(left))
        if left:
            print("ERROR: a second pass still wants to change: " + ", ".join(left[:10]), file=sys.stderr)
            return 2
        return 1 if drift else 0

    diff = make_diff(results, root)
    if args.diff_out:
        Path(args.diff_out).write_text(diff, encoding="utf-8", newline="\n")
    elif not args.inventory and not args.check:
        sys.stdout.write(diff)
    drift = print_report(results, skipped, cfg, files, pending)
    if args.check:
        return 1 if (pending or renames or drift) else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
