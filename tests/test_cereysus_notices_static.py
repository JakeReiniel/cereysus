"""Static checks for the Cereysus modification notice and license integrity (Batch 0E)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTICE_SENTENCE = (
    "Cereysus is a modified version of Odysseus (https://github.com/odysseus-dev/odysseus), "
    "licensed under the GNU AGPL-3.0-or-later. Modifications (c) 2026 Cereysus."
)
PLANNING_FILES = {
    "cereysus_development_prompt.md",
    "cereysus_agent_capability_catalog.md",
    "cereysus_project_instructions.md",
}


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_notice_file_carries_the_modification_notice() -> None:
    assert NOTICE_SENTENCE in _read("NOTICE-CEREYSUS.md")


def test_readme_names_the_fork_and_links_the_notice() -> None:
    readme = _read("README.md")
    assert NOTICE_SENTENCE in readme
    assert "[NOTICE-CEREYSUS.md](NOTICE-CEREYSUS.md)" in readme
    assert 'href="NOTICE-CEREYSUS.md"' in readme
    assert "assets/branding/cereysus/cereysus-wordmark.png" in readme


def test_license_is_intact_and_acknowledgments_were_only_appended() -> None:
    assert _read("LICENSE").startswith("GNU AFFERO GENERAL PUBLIC LICENSE")
    acknowledgments = _read("ACKNOWLEDGMENTS.md")
    assert "## Thanks to" in acknowledgments
    tail = acknowledgments.split("## Thanks to", 1)[1]
    assert "## Cereysus" in tail, "the Cereysus section is appended after the original content"
    assert "NOTICE-CEREYSUS.md" in tail


def test_sync_guide_documents_the_procedure() -> None:
    guide = _read("docs/cereysus/SYNC.md")
    for needle in ("git merge --ff-only upstream/dev", "tools/rebrand/rebrand.py --apply", "--check", "RULE DRIFT"):
        assert needle in guide


def test_no_planning_documents_are_in_the_repository() -> None:
    names = {
        path.name.lower()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.relative_to(ROOT).parts
    }
    assert not (names & PLANNING_FILES)
