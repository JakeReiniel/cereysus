"""Static checks for the persisted markers that were renamed with a dual match (P-1).

New reminder e-mails and auto-reply events carry the Cereysus wording; everything that
recognises them still accepts the wording written before the rename.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_new_reminder_emails_use_the_cereysus_subject() -> None:
    assert 'msg["Subject"] = f"Reminder (Cereysus): {_t}"' in _read("routes/note/note_routes.py")


def test_reminders_filter_matches_the_header_and_both_subjects() -> None:
    routes = _read("routes/email/email_routes.py")
    assert (
        'OR HEADER X-Odysseus-Kind "reminder" OR SUBJECT "Reminder (Odysseus):" SUBJECT "Reminder (Cereysus):"'
        in routes
    )


def test_clear_reminders_searches_both_subjects_with_and_without_sender() -> None:
    routes = _read("routes/email/email_routes.py")
    for subject in ("Reminder (Odysseus):", "Reminder (Cereysus):"):
        assert f'(SUBJECT {{_search_quote("{subject}")}})' in routes
        assert f'(FROM {{addr_q}} SUBJECT {{_search_quote("{subject}")}})' in routes


def test_inbox_scanner_drops_its_own_reminders_under_either_subject() -> None:
    scanner = _read("src/builtin_actions.py")
    assert '_raw_subj.startswith("reminder (odysseus):")' in scanner
    assert '_raw_subj.startswith("reminder (cereysus):")' in scanner


def test_auto_reply_event_is_written_with_the_new_marker_and_found_under_both() -> None:
    page = _read("static/js/emailLibrary/settingsPage.js")
    assert "description: `Cereysus email auto reply - account:${String(accountId || '')}`," in page
    assert "`Cereysus email auto reply - account:${String(accountId || '')}`," in page
    assert "`Odysseus email auto reply - account:${String(accountId || '')}`," in page
    assert "markers.some(marker => String(ev?.description || '').startsWith(marker))" in page
