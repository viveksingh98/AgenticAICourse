"""T5-T7 — grading.

Two paths, and the split is the whole point:

* deterministic (choice, order, contract) — pure Python, zero cost, works with no API key
* free-form (rubric-backed) — delegates to the `grader` package and nothing deeper

This module is the only place in `app/` that knows `grader` exists. No prompt text, no
model IDs, no Anthropic import lives here or anywhere else under `app/` — `test_boundaries`
enforces that by scanning the tree (plan D4, spec A3.2).
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator

from .content import Exercise

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# pylint: disable=wrong-import-position  # the path shim above must run first
from grader import load_rubrics, run_guards  # noqa: E402
from grader import grade as grade_submission  # noqa: E402

GRADED = "graded"
REJECTED = "rejected"
UNAVAILABLE = "grading_unavailable"


@dataclass
class ExerciseResult:
    """What the learner is shown after submitting, and what gets persisted."""

    status: str
    score: float
    passed: bool
    feedback: str
    explanation: str = ""
    criteria: list[dict] | None = None
    reference_answer: str = ""
    rubric_id: str | None = None
    rubric_version: int | None = None
    grader_model: str | None = None
    cost_micro_usd: int = 0
    flipped_count: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def is_graded(self) -> bool:
        return self.status == GRADED


# ------------------------------------------------------------------ deterministic


def _grade_choice(payload: dict, submission) -> ExerciseResult:
    try:
        chosen = int(submission)
    except (TypeError, ValueError):
        return ExerciseResult(REJECTED, 0.0, False, "Koi option select nahi hua.")
    correct = payload["correct_index"]
    right = chosen == correct
    return ExerciseResult(
        status=GRADED,
        score=1.0 if right else 0.0,
        passed=right,
        feedback="Sahi." if right else "Galat.",
        explanation=payload.get("explanation", ""),
    )


def _grade_order(payload: dict, submission) -> ExerciseResult:
    correct = payload["correct_order"]
    if not isinstance(submission, list) or len(submission) != len(correct):
        return ExerciseResult(REJECTED, 0.0, False, "Poori list order karni hai.")
    try:
        order = [int(x) for x in submission]
    except (TypeError, ValueError):
        return ExerciseResult(REJECTED, 0.0, False, "Order samajh nahi aaya.")

    in_place = sum(1 for got, want in zip(order, correct) if got == want)
    score = in_place / len(correct)
    if not payload.get("partial_credit", True):
        score = 1.0 if in_place == len(correct) else 0.0

    return ExerciseResult(
        status=GRADED,
        score=round(score, 4),
        passed=score >= 0.999,
        feedback=(
            "Sahi order." if score >= 0.999 else f"{in_place}/{len(correct)} sahi jagah pe hain."
        ),
        explanation=payload.get("explanation", ""),
    )


def _grade_contract(payload: dict, submission) -> ExerciseResult:
    if not isinstance(submission, str) or not submission.strip():
        return ExerciseResult(REJECTED, 0.0, False, "Schema khaali hai.")
    try:
        parsed = json.loads(submission)
    except json.JSONDecodeError as exc:
        return ExerciseResult(REJECTED, 0.0, False, f"Ye valid JSON nahi hai — {exc.msg}.")

    for pattern in payload.get("forbidden_patterns", []):
        if re.search(pattern, submission):
            return ExerciseResult(REJECTED, 0.0, False, "Isme kuch aisa hai jo nahi hona chahiye.")

    errors = sorted(
        Draft202012Validator(payload["target_schema"]).iter_errors(parsed),
        key=lambda e: list(e.path),
    )
    if not errors:
        return ExerciseResult(
            GRADED, 1.0, True, "Contract poora hai.", payload.get("explanation", "")
        )

    first = errors[0]
    where = " -> ".join(str(p) for p in first.path) or "(root)"
    return ExerciseResult(
        status=GRADED,
        score=0.0,
        passed=False,
        feedback=f"Abhi bhi gap hai — {where}: {first.message[:160]}",
        explanation=payload.get("explanation", ""),
    )


_DETERMINISTIC = {"choice": _grade_choice, "order": _grade_order, "contract": _grade_contract}


def grade_deterministic(exercise: Exercise, submission) -> ExerciseResult:
    """Grade a warm-up. No network, no cost, works with no API key (spec A2.4)."""
    grader = _DETERMINISTIC.get(exercise.kind)
    if grader is None:
        return ExerciseResult(REJECTED, 0.0, False, f"'{exercise.kind}' grade nahi kar sakte.")
    return grader(exercise.payload, submission)


# ---------------------------------------------------------------------- free-form


def _rubric_for(exercise: Exercise):
    rubric_id = (exercise.rubric or {}).get("id")
    return load_rubrics().get(rubric_id) if rubric_id else None


def grade_freeform(exercise: Exercise, submission: str) -> ExerciseResult:
    """Grade a rep or twist through the rubric judge.

    Three outcomes, all of which keep the session usable:
      * guard rejection — specific feedback, no grading call spent (spec A3.5)
      * no credentials  — an explicit unavailable state, not a crash (spec A3.6)
      * graded          — score plus the per-criterion trace
    """
    rubric = _rubric_for(exercise)
    if rubric is None:
        return ExerciseResult(REJECTED, 0.0, False, "Is exercise ka rubric nahi mila.")

    payload = exercise.payload
    guard = run_guards(
        submission,
        min_chars=payload.get("min_chars", 80),
        max_chars=payload.get("max_chars", 2000),
    )
    if not guard.ok:
        return ExerciseResult(REJECTED, 0.0, False, guard.feedback)

    try:
        grade = grade_submission(
            rubric,
            submission,
            min_chars=payload.get("min_chars", 80),
            max_chars=payload.get("max_chars", 2000),
        )
    except Exception as exc:  # pylint: disable=broad-exception-caught
        # Missing credentials is the normal state for a fresh clone, and any other
        # grader-side failure should degrade the same way: the learner keeps their
        # session, and the reason is stated rather than swallowed (spec A3.6).
        return ExerciseResult(
            status=UNAVAILABLE,
            score=0.0,
            passed=False,
            feedback=(
                "Grading abhi available nahi hai — aapka jawab save ho gaya hai. "
                "ANTHROPIC_API_KEY set karke dobara try karo."
            ),
            reference_answer=rubric.reference_answer,
            rubric_id=rubric.id,
            rubric_version=rubric.version,
            meta={"error": type(exc).__name__},
        )

    if not hasattr(grade, "criteria"):  # a GuardResult came back from the pipeline
        return ExerciseResult(REJECTED, 0.0, False, getattr(grade, "feedback", "Try again."))

    criteria = [
        {
            "id": c.id,
            "met": c.met,
            "check": next((rc.check for rc in rubric.criteria if rc.id == c.id), ""),
            "negative": c.polarity == "negative",
            "feedback": next(
                (rc.feedback_if_missed for rc in rubric.criteria if rc.id == c.id), ""
            ),
        }
        for c in grade.criteria
    ]
    return ExerciseResult(
        status=GRADED,
        score=grade.score,
        passed=grade.passed,
        feedback=grade.feedback,
        criteria=criteria,
        reference_answer=rubric.reference_answer,
        rubric_id=grade.rubric_id,
        rubric_version=grade.rubric_version,
        grader_model=grade.meta.get("model"),
        cost_micro_usd=int(round(grade.meta.get("cost_usd", 0.0) * 1_000_000)),
        flipped_count=grade.flipped_count,
    )


def grade_exercise(exercise: Exercise, submission) -> ExerciseResult:
    """Route to the right grader. The only entry point routes should call."""
    if exercise.is_freeform:
        return grade_freeform(exercise, submission if isinstance(submission, str) else "")
    return grade_deterministic(exercise, submission)
