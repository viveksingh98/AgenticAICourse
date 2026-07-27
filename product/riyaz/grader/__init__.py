"""Riyaz grading pipeline.

    guards -> hard checks -> rubric judge (one LLM call) -> score in code

Only the third stage costs money, and it is the only stage that involves a model at all.
"""

from __future__ import annotations

from .guards import GuardResult, run_guards, run_hard_checks
from .judge import JudgeVerdict, constitution, count_constitution_tokens, judge
from .models import HARD, STANDARD, GraderModel, for_tier
from .rubric import Criterion, Rubric, load_rubric, load_rubrics
from .score import Grade, score_grade, verify_evidence

__all__ = [
    "grade",
    "Grade",
    "GuardResult",
    "JudgeVerdict",
    "Rubric",
    "Criterion",
    "GraderModel",
    "STANDARD",
    "HARD",
    "for_tier",
    "load_rubric",
    "load_rubrics",
    "run_guards",
    "run_hard_checks",
    "score_grade",
    "verify_evidence",
    "constitution",
    "count_constitution_tokens",
    "judge",
]


def grade(
    rubric: Rubric,
    submission: str,
    *,
    client=None,
    min_chars: int = 80,
    max_chars: int = 2000,
    hard_checks: list[dict] | None = None,
) -> Grade | GuardResult:
    """Run the full pipeline. Returns a ``GuardResult`` if we rejected before the LLM call.

    A rejected submission costs nothing and gets more specific feedback than a rubric
    could give, which is why the guards come first rather than being bolted on later.
    """
    guard = run_guards(submission, min_chars=min_chars, max_chars=max_chars)
    if not guard.ok:
        return guard

    hard = run_hard_checks(submission, hard_checks)
    if not hard.ok:
        return hard

    verdict = judge(rubric, submission, client=client)
    return score_grade(
        rubric,
        submission,
        verdict.raw,
        flags=guard.flags,
        meta={
            "model": verdict.model_id,
            "cost_usd": verdict.cost_usd,
            "cache_hit": verdict.cache_hit,
            "cache_read_tokens": verdict.cache_read_tokens,
            "cache_write_tokens": verdict.cache_write_tokens,
            "latency_ms": verdict.latency_ms,
        },
    )
