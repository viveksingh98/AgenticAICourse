"""T8 — the HTTP surface.

Six endpoints, exactly as in plan.md section 4. Submissions POST as JSON and get back a
rendered HTML fragment the page swaps in — enough interactivity for a result reveal,
without a client-side router.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import content, progression
from .grading import GRADED, UNAVAILABLE, grade_exercise
from .store import Store

APP_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Riyaz", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=APP_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

# Mutable module state, not a constant: opened lazily so tests can point
# RIYAZ_DB at a temp file before the first request.
_store: Store | None = None  # pylint: disable=invalid-name


def store() -> Store:
    """Lazily opened so tests can point at a temp database before the first request."""
    global _store  # pylint: disable=global-statement
    if _store is None:
        _store = Store(os.environ.get("RIYAZ_DB", str(APP_DIR / "riyaz.db")))
    return _store


def _today() -> date:
    return date.today()


def _streak(learner_id: int) -> int:
    return progression.streak_from_days(store().session_days(learner_id), _today())


@app.get("/healthz")
def healthz() -> JSONResponse:
    """Liveness, plus whether free-form grading is configured at all."""
    return JSONResponse(
        {"ok": True, "grading_configured": bool(os.environ.get("ANTHROPIC_API_KEY"))}
    )


@app.get("/", response_class=HTMLResponse)
def open_screen(request: Request):
    """Streak first, then the ask. Reward before effort (spec A1.2)."""
    learner = store().learner()
    done = store().completed_lesson_ids(learner["id"])
    lesson = content.next_lesson_for(done)
    return templates.TemplateResponse(
        request,
        "open.html",
        {
            "lesson": lesson,
            "streak": _streak(learner["id"]),
            "total_xp": store().total_xp(learner["id"]),
            "all_done": lesson is None,
            "completed_count": len(done),
            "total_lessons": len(content.all_lessons()),
        },
    )


@app.post("/session/start")
def start_session():
    learner = store().learner()
    lesson = content.next_lesson_for(store().completed_lesson_ids(learner["id"]))
    if lesson is None:
        return RedirectResponse("/", status_code=303)
    session_id = store().start_session(learner["id"], lesson.id)
    first = lesson.exercises[0].ordinal
    return RedirectResponse(f"/session/{session_id}/exercise/{first}", status_code=303)


def _lesson_and_exercise(session_id: int, ordinal: int):
    row = store().session(session_id)
    if row is None:
        return None, None, None
    lesson = content.lesson_by_id(row["lesson_id"])
    if lesson is None:
        return row, None, None
    return row, lesson, lesson.exercise(ordinal)


@app.get("/session/{session_id}/exercise/{ordinal}", response_class=HTMLResponse)
def exercise_screen(request: Request, session_id: int, ordinal: int):
    session_row, lesson, exercise = _lesson_and_exercise(session_id, ordinal)
    if session_row is None or lesson is None or exercise is None:
        return RedirectResponse("/", status_code=303)

    prior = None
    if exercise.slot == "twist":
        twist_of = exercise.payload.get("twist_of")
        if twist_of:
            row = store().attempt_for(session_id, twist_of)
            prior = row["submission"] if row else None

    return templates.TemplateResponse(
        request,
        "exercise.html",
        {
            "session_id": session_id,
            "lesson": lesson,
            "exercise": exercise,
            "payload": exercise.for_browser(),
            "position": list(lesson.exercises).index(exercise) + 1,
            "total": len(lesson.exercises),
            "prior_submission": prior,
        },
    )


@app.post("/session/{session_id}/exercise/{ordinal}", response_class=HTMLResponse)
async def submit_exercise(request: Request, session_id: int, ordinal: int):
    session_row, lesson, exercise = _lesson_and_exercise(session_id, ordinal)
    if session_row is None or lesson is None or exercise is None:
        return HTMLResponse("<p class='error'>Ye exercise nahi mila.</p>", status_code=404)

    body = await request.json()
    submission = body.get("submission")

    result = grade_exercise(exercise, submission)
    attempt_id = store().record_attempt(session_id, exercise.id, submission)
    store().record_grade(attempt_id, result)

    learner_id = session_row["learner_id"]
    # XP is keyed on session+exercise, so a resubmit never double-awards (plan D6).
    if result.status in (GRADED, UNAVAILABLE):
        awarded = progression.xp_for(exercise.slot, result.score)
        store().add_xp(
            learner_id, "exercise", f"{session_id}:{exercise.id}", awarded, exercise.slot
        )
    else:
        awarded = 0

    nxt = next((e for e in lesson.exercises if e.ordinal > ordinal), None)
    return templates.TemplateResponse(
        request,
        "_result.html",
        {
            "result": result,
            "exercise": exercise,
            "xp": awarded,
            "next_url": (
                f"/session/{session_id}/exercise/{nxt.ordinal}"
                if nxt
                else f"/session/{session_id}/complete"
            ),
            "next_label": "Aage" if nxt else "Session khatam karo",
        },
    )


@app.get("/session/{session_id}/complete", response_class=HTMLResponse)
def complete_screen(request: Request, session_id: int):
    session_row = store().session(session_id)
    if session_row is None:
        return RedirectResponse("/", status_code=303)

    lesson = content.lesson_by_id(session_row["lesson_id"])
    learner_id = session_row["learner_id"]

    # First visit finalises; reloads are read-only (spec A5.5).
    first_completion = store().complete_session(session_id)
    if first_completion:
        store().record_session_day(learner_id, _today().isoformat())
        streak = _streak(learner_id)
        bonus = progression.streak_bonus(streak)
        # A day-1 streak rounds to a 0 bonus; writing that row puts a "+0" line on the
        # close screen, which reads as a bug rather than as arithmetic.
        if bonus > 0:
            store().add_xp(
                learner_id, "streak_bonus", f"{session_id}:streak", bonus, f"streak {streak}"
            )
        if lesson:
            scored = [
                r["score"] for r in store().session_attempts(session_id) if r["score"] is not None
            ]
            if scored:
                previous = store().mastery(learner_id).get(lesson.skill_id)
                store().record_mastery(
                    learner_id,
                    lesson.skill_id,
                    progression.mastery_after(previous, sum(scored) / len(scored)),
                )

    entries = store().xp_entries_for_session(learner_id, session_id)
    attempts = {r["exercise_id"]: r for r in store().session_attempts(session_id)}

    # Lead with a win even when the rep went badly (spec A5.3).
    win_count = sum(1 for row in attempts.values() if row["passed"])
    done = store().completed_lesson_ids(learner_id)
    return templates.TemplateResponse(
        request,
        "complete.html",
        {
            "lesson": lesson,
            "entries": entries,
            "session_xp": sum(e["amount"] for e in entries),
            "total_xp": store().total_xp(learner_id),
            "streak": _streak(learner_id),
            "advanced": first_completion,
            "win_count": win_count,
            "attempt_count": len(attempts),
            "tomorrow": content.next_lesson_for(done),
        },
    )
