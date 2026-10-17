"""Tests for tools/rebrand/rebrand.py. Run:  python -m pytest tools/rebrand/test_rebrand.py -q"""
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rebrand  # noqa: E402

MAP = """
verified_against: test
paths:
  - {glob: [LICENSE], action: freeze, tier: T0, why: licence}
  - {glob: ["docs/**"], action: hold, tier: R, why: upstream docs}
  - {glob: [Odysseus.spec, Cereysus.spec], action: text, tier: T2, why: spec}
  - {glob: ["app/**", "static/**"], action: text, tier: T1, why: ui}
  - {glob: "**", action: hold, tier: R, why: no policy}
protect:
  - {re: '[\\w.:/@-]*odysseus-dev[\\w.:/@-]*', tier: T0, kind: org-url, why: upstream}
  - {re: 'X-Odysseus-[A-Za-z0-9-]+', tier: T3, kind: header, why: header}
keep_lines:
  - {id: quote, file: static/q.js, re: 'son of Laertes', tier: R, kind: quote, why: Homer}
rules:
  - {id: tagline, file: static/index.html, find: "A voyage begins.", replace: "A journey begins."}
  - {id: ref-spec, file: "**", find: "Odysseus.spec", replace: "Cereysus.spec", count: any, optional: true}
renames:
  - {from: Odysseus.spec, to: Cereysus.spec}
"""

FILES = {
    "LICENSE": "Copyright Odysseus contributors\n",
    "docs/guide.md": "Odysseus handbook. See Odysseus.spec\n",
    "Odysseus.spec": "name='Odysseus',\n",
    "static/index.html": '<title>Odysseus Chat</title>\n<div id="welcome-sub">A voyage begins.</div>\n',
    "static/q.js": "const q = ['I am Odysseus, son of Laertes'];\nconst a = 'Welcome to Odysseus';\n",
    "app/a.py": (
        '"""Odysseus module docstring."""\n'
        "# Odysseus comment stays\n"
        'MSG = "Create an Odysseus draft"\n'
        'HDR = "X-Odysseus-Run-Id"\n'
        'ENV = "ODYSSEUS_URL"\n'
        'KEY = "odysseus-theme"\n'
        'URL = "https://github.com/odysseus-dev/odysseus"\n'
        "def startOdysseusApp(): pass\n"
    ),
}


@pytest.fixture()
def repo(tmp_path):
    (tmp_path / "rebrand-map.yml").write_text(MAP, encoding="utf-8")
    for rel, text in FILES.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode("utf-8"))
    return tmp_path


def run(repo, *extra):
    return rebrand.main(["--root", str(repo), "--map", str(repo / "rebrand-map.yml"), *extra])


def read(repo, rel):
    return (repo / rel).read_text(encoding="utf-8")


def test_dry_run_changes_nothing(repo, capsys):
    before = {rel: read(repo, rel) for rel in FILES}
    assert run(repo) == 0
    assert {rel: read(repo, rel) for rel in FILES} == before
    assert "Cereysus Chat" in capsys.readouterr().out  # the diff is printed


def test_apply_renames_text_and_keeps_the_rest(repo):
    assert run(repo, "--apply") == 0
    py = read(repo, "app/a.py")
    assert 'MSG = "Create a Cereysus draft"' in py            # article agreement
    assert '"""Odysseus module docstring."""' in py           # docstring kept
    assert "# Odysseus comment stays" in py                   # comment kept
    for kept in ('"X-Odysseus-Run-Id"', '"ODYSSEUS_URL"', '"odysseus-theme"', "odysseus-dev/odysseus", "startOdysseusApp"):
        assert kept in py
    html = read(repo, "static/index.html")
    assert "<title>Cereysus Chat</title>" in html and "A journey begins." in html
    js = read(repo, "static/q.js")
    assert "I am Odysseus, son of Laertes" in js and "Welcome to Cereysus" in js
    assert read(repo, "LICENSE") == FILES["LICENSE"]          # frozen
    assert read(repo, "docs/guide.md") == "Odysseus handbook. See Cereysus.spec\n"  # held text kept, reference updated


def test_renamed_file_and_idempotency(repo):
    assert run(repo, "--apply") == 0
    assert not (repo / "Odysseus.spec").exists()
    assert read(repo, "Cereysus.spec") == "name='Cereysus',\n"
    snapshot = {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
    assert run(repo, "--apply") == 0                           # second pass: nothing left to do
    assert {p.relative_to(repo).as_posix(): p.read_bytes() for p in repo.rglob("*") if p.is_file()} == snapshot
    assert run(repo, "--check") == 0


def test_check_fails_while_changes_are_pending(repo):
    assert run(repo, "--check") == 1


def test_crlf_is_preserved(repo):
    (repo / "static/win.js").write_bytes(b"const t = 'Odysseus';\r\nconst u = 1;\r\n")
    assert run(repo, "--apply") == 0
    assert (repo / "static/win.js").read_bytes() == b"const t = 'Cereysus';\r\nconst u = 1;\r\n"


def test_inventory_is_written(repo):
    out = repo / "inv.md"
    assert run(repo, "--inventory", str(out)) == 0
    text = out.read_text(encoding="utf-8")
    assert "## 1. Summary" in text and "`Odysseus.spec`" in text
