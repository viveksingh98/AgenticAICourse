"""Stages 1 and 2 of the grading pipeline — everything before the LLM call.

These stages exist for two reasons. Pedagogically, a learner who submits four words
deserves an instant, specific nudge rather than a rubric verdict. Economically, every
submission rejected here is a grade we never pay for.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

MIN_CHARS_DEFAULT = 80
MAX_CHARS_DEFAULT = 2000

# Phrases that only appear when someone is talking *to the grader* rather than doing the
# exercise. This is a signal for logging and review, not a rejection: the constitution
# already tells the judge to treat the submission as data, and a learner who tries this
# will fail on the merits anyway. Flagging it lets us watch how often it is attempted.
_INJECTION_PATTERNS = [
    r"ignore (all |any )?(previous|prior|above) instructions",
    r"disregard (the |your )?(previous|prior|above|system)",
    r"you are now",
    r"\bsystem\s*:",
    r"grading[- ]bypass",
    r"(award|give|set) (me )?(full|maximum|all) (marks|score|credit)",
    r"met\s*:\s*true",
    r"pre-?approved by (the )?curriculum",
]
_INJECTION_RE = re.compile("|".join(_INJECTION_PATTERNS), re.IGNORECASE)


@dataclass
class GuardResult:
    """Outcome of a pre-LLM stage: whether to proceed, and why not if not."""

    ok: bool
    reason: str = ""
    feedback: str = ""
    flags: tuple[str, ...] = ()


def run_guards(
    submission: str,
    *,
    min_chars: int = MIN_CHARS_DEFAULT,
    max_chars: int = MAX_CHARS_DEFAULT,
) -> GuardResult:
    text = submission.strip()

    if not text:
        return GuardResult(False, "empty", "Kuch likha hi nahi. Ek line se hi shuru karo.")

    if len(text) < min_chars:
        words = len(text.split())
        return GuardResult(
            False,
            "too_short",
            f"Yeh {words} shabd hain. Is task ke liye kam se kam {min_chars} characters chahiye — "
            "constraints ko address karo, phir submit karo.",
        )

    if len(text) > max_chars:
        return GuardResult(
            False,
            "too_long",
            f"{len(text)} characters — limit {max_chars} hai. Jo constraint address nahi karta, "
            "woh nikaal do.",
        )

    flags: list[str] = []
    if _INJECTION_RE.search(text):
        # Not a rejection. Graded normally; recorded for review.
        flags.append("possible_injection")

    return GuardResult(True, flags=tuple(flags))


def run_hard_checks(submission: str, checks: list[dict] | None) -> GuardResult:
    """Stage 2: deterministic, exercise-specific checks.

    Each check is ``{"kind": "must_match"|"must_not_match", "pattern": ..., "feedback": ...}``.
    A failure here short-circuits with feedback far more specific than a rubric could give
    ("your JSON is missing `required`"), and costs nothing.
    """
    for check in checks or []:
        pattern = re.compile(check["pattern"], re.IGNORECASE | re.MULTILINE)
        found = bool(pattern.search(submission))
        kind = check["kind"]
        if kind == "must_match" and not found:
            return GuardResult(False, "hard_check", check["feedback"])
        if kind == "must_not_match" and found:
            return GuardResult(False, "hard_check", check["feedback"])
    return GuardResult(True)
