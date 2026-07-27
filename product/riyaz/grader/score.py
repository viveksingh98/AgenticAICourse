"""Stage 4 — evidence validation and scoring.

The judge never emits a number. It emits per-criterion booleans plus a verbatim quote,
and the score is arithmetic here. Two things follow from that: the score cannot drift
between runs for the same set of booleans, and every point is attributable to a named
criterion, which is what makes the feedback specific instead of a bare "6/10".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .rubric import Criterion, Rubric


@dataclass
class CriterionResult:
    id: str
    met: bool
    evidence: str
    # True when the judge claimed met and we could locate its quote in the submission.
    evidence_verified: bool
    # True when we overrode the judge because its quote was not in the submission.
    flipped: bool
    weight: float
    polarity: str


@dataclass
class Grade:
    rubric_id: str
    rubric_version: int
    score: float
    passed: bool
    criteria: list[CriterionResult]
    feedback: str
    weakest_id: str
    strongest_id: str
    flags: tuple[str, ...] = ()
    flipped_count: int = 0
    meta: dict = field(default_factory=dict)

    @property
    def met_ids(self) -> set[str]:
        return {c.id for c in self.criteria if c.met}


def _normalise(text: str) -> str:
    """Collapse whitespace so a quote survives re-wrapping, but nothing else.

    Deliberately case-sensitive and punctuation-preserving: the point of the evidence
    rule is that the judge copied something real, and a loose match would let a
    reconstructed-from-memory quote through.
    """
    return re.sub(r"\s+", " ", text).strip()


def verify_evidence(evidence: str, submission: str) -> bool:
    quote = _normalise(evidence).strip("\"'“”‘’ ")
    if len(quote) < 8:
        # Too short to demonstrate anything; also too short to be a meaningful check.
        return False
    return quote in _normalise(submission)


def score_grade(
    rubric: Rubric,
    submission: str,
    judge_output: dict,
    *,
    flags: tuple[str, ...] = (),
    meta: dict | None = None,
) -> Grade:
    by_id = {c.id: c for c in rubric.criteria}
    returned = {c["id"]: c for c in judge_output.get("criteria", [])}

    results: list[CriterionResult] = []
    flipped = 0

    for criterion in rubric.criteria:
        raw = returned.get(criterion.id)
        if raw is None:
            # The judge dropped a criterion. Treat as unmet rather than skipping it,
            # so a malformed verdict can never inflate a score.
            results.append(
                CriterionResult(
                    id=criterion.id,
                    met=False,
                    evidence="judge did not return this criterion",
                    evidence_verified=False,
                    flipped=False,
                    weight=criterion.weight,
                    polarity=criterion.polarity,
                )
            )
            continue

        met = bool(raw.get("met"))
        evidence = raw.get("evidence", "")
        verified = verify_evidence(evidence, submission) if met else True

        was_flipped = False
        if met and not verified:
            # The evidence rule, enforced. An unquotable claim is not a claim.
            met = False
            was_flipped = True
            flipped += 1

        results.append(
            CriterionResult(
                id=criterion.id,
                met=met,
                evidence=evidence,
                evidence_verified=verified,
                flipped=was_flipped,
                weight=criterion.weight,
                polarity=criterion.polarity,
            )
        )

    earned = sum(r.weight for r in results if r.met and r.polarity != "negative")
    penalty = sum(r.weight for r in results if r.met and r.polarity == "negative")
    total = rubric.positive_weight or 1.0
    score = max(0.0, min(1.0, (earned - penalty) / total))

    weakest_id = _pick_weakest(rubric, results, judge_output.get("weakest", ""))
    feedback = _feedback_for(by_id, weakest_id, results)

    return Grade(
        rubric_id=rubric.id,
        rubric_version=rubric.version,
        score=round(score, 4),
        passed=score >= rubric.pass_threshold,
        criteria=results,
        feedback=feedback,
        weakest_id=weakest_id,
        strongest_id=judge_output.get("strongest", ""),
        flags=flags,
        flipped_count=flipped,
        meta=meta or {},
    )


def _pick_weakest(rubric: Rubric, results: list[CriterionResult], judge_choice: str) -> str:
    """Trust the judge's pick only if it is actually a problem; otherwise take the
    heaviest unmet positive criterion."""
    by_id = {r.id: r for r in results}
    chosen = by_id.get(judge_choice)
    if chosen and (
        (chosen.polarity != "negative" and not chosen.met)
        or (chosen.polarity == "negative" and chosen.met)
    ):
        return judge_choice

    problems = [r for r in results if r.polarity != "negative" and not r.met]
    if problems:
        return max(problems, key=lambda r: r.weight).id
    negatives = [r for r in results if r.polarity == "negative" and r.met]
    return negatives[0].id if negatives else ""


def _feedback_for(
    by_id: dict[str, Criterion], weakest_id: str, results: list[CriterionResult]
) -> str:
    if not weakest_id:
        met = sum(1 for r in results if r.met and r.polarity != "negative")
        return f"Saare {met} criteria clear. Yeh submission reference ke barabar hai."
    criterion = by_id.get(weakest_id)
    if criterion and criterion.feedback_if_missed:
        return criterion.feedback_if_missed
    return f"Criterion {weakest_id} miss hua."
