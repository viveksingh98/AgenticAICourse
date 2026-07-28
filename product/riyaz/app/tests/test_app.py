"""Tests for Riyaz v0. Every one runs with no API key (spec A7.3).

Organised by the spec section each group verifies, so a failure points at a criterion
rather than at a function.
"""

from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

RIYAZ_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RIYAZ_ROOT))

# pylint: disable=wrong-import-position  # the path shim above must run first
from app import content, progression  # noqa: E402
from app.grading import GRADED, REJECTED, grade_deterministic  # noqa: E402
from app.store import Store  # noqa: E402


@pytest.fixture(name="store")
def store_fixture():
    with tempfile.TemporaryDirectory() as tmp:
        store = Store(Path(tmp) / "t.db")
        yield store
        store.close()


def _exercise(lesson_id: str, kind: str):
    lesson = content.lesson_by_id(lesson_id)
    return next(e for e in lesson.exercises if e.kind == kind)


# ------------------------------------------------------------ T2 / content (A1.4, A7.4)


def test_all_three_lessons_load_and_validate():
    lessons = content.all_lessons()
    assert len(lessons) == 3
    assert [le.day_index for le in lessons] == sorted(le.day_index for le in lessons)


def test_broken_lesson_is_rejected_naming_its_file(tmp_path):
    (tmp_path / "broken.json").write_text(json.dumps({"id": "nope"}), encoding="utf-8")
    content.all_lessons.cache_clear()
    with pytest.raises(content.ContentError, match="broken.json"):
        content.all_lessons(tmp_path)
    content.all_lessons.cache_clear()


def test_next_lesson_is_lowest_unfinished_then_none():
    lessons = content.all_lessons()
    assert content.next_lesson_for(set()).id == lessons[0].id
    assert content.next_lesson_for({lessons[0].id}).id == lessons[1].id
    assert content.next_lesson_for({le.id for le in lessons}) is None


# --------------------------------------------------- T6 / answers withheld (A2.6, A3.7)


@pytest.mark.parametrize("kind", ["choice", "order", "contract"])
def test_browser_payload_never_carries_the_answer(kind):
    lesson_id = {"choice": "t1-l03-context-window", "order": "t3-l04-premature-stop",
                 "contract": "t2-l07-output-contract"}[kind]
    payload = _exercise(lesson_id, kind).for_browser()
    for leaked in ("correct_index", "correct_order", "target_schema", "explanation"):
        assert leaked not in payload, f"{leaked} leaked to the browser"


# ------------------------------------------------------ T5 / deterministic grading (A2.4)


def test_choice_grading_both_ways():
    exercise = _exercise("t1-l03-context-window", "choice")
    correct = exercise.payload["correct_index"]
    assert grade_deterministic(exercise, correct).passed
    assert not grade_deterministic(exercise, (correct + 1) % 4).passed


def test_choice_result_carries_the_explanation_either_way():
    exercise = _exercise("t1-l03-context-window", "choice")
    for answer in (exercise.payload["correct_index"], (exercise.payload["correct_index"] + 1) % 4):
        assert grade_deterministic(exercise, answer).explanation  # spec A2.5


def test_order_grading_gives_partial_credit():
    exercise = _exercise("t3-l04-premature-stop", "order")
    correct = exercise.payload["correct_order"]
    assert grade_deterministic(exercise, correct).score == 1.0
    swapped = list(correct)
    swapped[0], swapped[1] = swapped[1], swapped[0]
    partial = grade_deterministic(exercise, swapped)
    assert 0.0 < partial.score < 1.0


def test_contract_grading_accepts_complete_and_rejects_incomplete():
    exercise = _exercise("t2-l07-output-contract", "contract")
    complete = json.dumps({
        "type": "object",
        "properties": {
            "team": {"enum": ["billing", "tech", "sales", "account", "shipping", "unknown"]},
            "urgent": {"type": "boolean"},
        },
        "required": ["team", "urgent"],
        "additionalProperties": False,
    })
    assert grade_deterministic(exercise, complete).passed
    assert not grade_deterministic(exercise, exercise.payload["starter"]).passed


def test_malformed_json_is_rejected_not_crashed():
    exercise = _exercise("t2-l07-output-contract", "contract")
    result = grade_deterministic(exercise, "{not json")
    assert result.status == REJECTED and not result.passed


def test_deterministic_grading_needs_no_api_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    exercise = _exercise("t1-l03-context-window", "choice")
    assert grade_deterministic(exercise, exercise.payload["correct_index"]).status == GRADED


# ------------------------------------------------------------- T4 / progression (A6.3, A6.4)


@pytest.mark.parametrize(
    "slot,score,expected",
    [("warmup", 1.0, 8), ("rep", 1.0, 49), ("rep", 0.7, 38), ("rep", 0.3, 19), ("twist", 1.0, 32)],
)
def test_xp_table(slot, score, expected):
    assert progression.xp_for(slot, score) == expected


def test_a_failed_attempt_still_earns_xp():
    assert progression.xp_for("rep", 0.0) > 0  # blueprint §10: showing up is the behaviour


def test_streak_counts_consecutive_days():
    today = date(2026, 7, 28)
    days = [(today - timedelta(days=i)).isoformat() for i in range(5)]
    assert progression.streak_from_days(days, today) == 5


def test_streak_survives_a_two_day_gap():
    today = date(2026, 7, 28)
    days = [today.isoformat(), (today - timedelta(days=3)).isoformat(),
            (today - timedelta(days=4)).isoformat()]
    assert progression.streak_from_days(days, today) == 3


def test_streak_breaks_on_a_three_day_gap():
    today = date(2026, 7, 28)
    days = [today.isoformat(), (today - timedelta(days=4)).isoformat()]
    assert progression.streak_from_days(days, today) == 1


def test_no_days_means_no_streak():
    assert progression.streak_from_days([], date(2026, 7, 28)) == 0


def test_mastery_blends_rather_than_replaces():
    assert progression.mastery_after(None, 0.8) == 0.8
    blended = progression.mastery_after(1.0, 0.0)
    assert 0.0 < blended < 1.0


# ------------------------------------------------------------------ T3 / store (A6.1, A6.2)


def test_xp_ledger_is_append_only_and_idempotent(store):
    learner = store.learner()["id"]
    assert store.add_xp(learner, "exercise", "1:e1", 30) is True
    assert store.add_xp(learner, "exercise", "1:e1", 30) is False  # spec A5.5
    assert store.total_xp(learner) == 30


def test_total_xp_is_always_a_sum_of_the_ledger(store):
    learner = store.learner()["id"]
    for i in range(4):
        store.add_xp(learner, "exercise", f"1:e{i}", 10)
    rows = store.conn.execute(
        "SELECT amount FROM xp_ledger WHERE learner_id = ?", (learner,)
    ).fetchall()
    assert store.total_xp(learner) == sum(r["amount"] for r in rows)


def test_state_survives_a_restart(tmp_path):
    path = tmp_path / "restart.db"
    first = Store(path)
    learner = first.learner()["id"]
    first.add_xp(learner, "exercise", "1:e1", 42)
    first.record_session_day(learner, "2026-07-28")
    first.close()

    second = Store(path)
    assert second.total_xp(second.learner()["id"]) == 42
    assert second.session_days(second.learner()["id"]) == ["2026-07-28"]
    second.close()


def test_completing_a_session_twice_is_a_no_op(store):
    learner = store.learner()["id"]
    session_id = store.start_session(learner, "t1-l03-context-window")
    assert store.complete_session(session_id) is True
    assert store.complete_session(session_id) is False


def test_starting_the_same_lesson_resumes_rather_than_duplicating(store):
    learner = store.learner()["id"]
    first = store.start_session(learner, "t1-l03-context-window")
    assert store.start_session(learner, "t1-l03-context-window") == first


# ---------------------------------------------------------------- T7 / boundaries (A3.2, N3)


def test_app_code_never_imports_anthropic_directly():
    """Prompt construction and model choice belong to grader/, not to the app (plan D4)."""
    offenders = [
        path.name
        for path in (RIYAZ_ROOT / "app").rglob("*.py")
        if re.search(r"^\s*(import|from)\s+anthropic", path.read_text(encoding="utf-8"), re.M)
    ]
    assert not offenders, f"anthropic imported directly in: {offenders}"


def test_grading_module_is_the_only_door_to_the_grader():
    offenders = [
        path.name
        for path in (RIYAZ_ROOT / "app").rglob("*.py")
        if path.name not in {"grading.py"}
        and re.search(r"^\s*from\s+grader\s+import", path.read_text(encoding="utf-8"), re.M)
    ]
    assert not offenders, f"grader imported outside grading.py: {offenders}"


# ------------------------------------------------------------------- T8-T11 / routes


@pytest.fixture(name="client")
def client_fixture(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("RIYAZ_DB", str(tmp_path / "routes.db"))
    # Imported here, not at module scope: RIYAZ_DB must be set before app.main opens
    # its store, and TestClient before the app module is first imported.
    # pylint: disable=import-outside-toplevel
    from fastapi.testclient import TestClient

    from app import main

    main._store = None  # pylint: disable=protected-access
    with TestClient(main.app) as client:
        yield client
    main._store = None  # pylint: disable=protected-access


def test_open_screen_shows_streak_and_todays_lesson(client):
    body = client.get("/").text
    assert "🔥" in body                                   # spec A1.2
    assert content.all_lessons()[0].title in body         # spec A1.1
    assert "Aaj ka riyaz shuru karo" in body              # spec A1.3


def test_healthz_reports_grading_not_configured(client):
    assert client.get("/healthz").json() == {"ok": True, "grading_configured": False}


def test_a_full_session_can_be_completed_without_an_api_key(client):
    """The whole point of spec A3.6: a fresh clone can finish a session."""
    start = client.post("/session/start", follow_redirects=False)
    assert start.status_code == 303
    session_url = start.headers["location"]
    session_id = int(session_url.split("/")[2])

    lesson = content.all_lessons()[0]
    for exercise in lesson.exercises:
        page = client.get(f"/session/{session_id}/exercise/{exercise.ordinal}")
        assert page.status_code == 200
        submission = (
            exercise.payload.get("correct_index")
            if exercise.kind == "choice"
            else exercise.payload.get("correct_order")
        )
        posted = client.post(
            f"/session/{session_id}/exercise/{exercise.ordinal}",
            json={"submission": submission},
        )
        assert posted.status_code == 200

    complete = client.get(f"/session/{session_id}/complete")
    assert complete.status_code == 200
    assert "XP is session" in complete.text        # spec A5.1
    assert "🔥" in complete.text                    # spec A5.2


def test_reloading_the_close_screen_awards_nothing_further(client):
    start = client.post("/session/start", follow_redirects=False)
    session_id = int(start.headers["location"].split("/")[2])
    first = client.get(f"/session/{session_id}/complete").text
    second = client.get(f"/session/{session_id}/complete").text

    def total(page: str) -> int:
        return int(re.search(r"<span class=\"big\">(\d+)</span><small>total XP", page).group(1))

    assert total(first) == total(second)           # spec A5.5


def test_unknown_session_redirects_home_rather_than_erroring(client):
    assert client.get("/session/9999/exercise/1", follow_redirects=False).status_code == 303
