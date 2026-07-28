"""Loading rubrics out of the lesson JSON files."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

LESSON_DIR = Path(__file__).resolve().parent.parent / "schema" / "samples"


@dataclass(frozen=True)
class Criterion:
    """One binary check the judge answers, with its weight and its miss feedback."""

    id: str
    check: str
    weight: float
    polarity: str = "positive"
    feedback_if_missed: str = ""

    @property
    def is_negative(self) -> bool:
        return self.polarity == "negative"


@dataclass(frozen=True)
class Rubric:
    """A versioned set of criteria plus the exercise context the judge needs."""

    id: str
    version: int
    grader_tier: str
    pass_threshold: float
    criteria: tuple[Criterion, ...]
    reference_answer: str
    golden_set_id: str
    # Carried for the prompt so the judge knows what the learner was asked to do.
    scenario: str = ""
    task: str = ""
    constraints: tuple[str, ...] = ()

    @property
    def positive_weight(self) -> float:
        return sum(c.weight for c in self.criteria if not c.is_negative)


def _payload_context(payload: dict) -> tuple[str, str, tuple[str, ...]]:
    kind = payload.get("kind")
    if kind == "freeform":
        return (
            payload.get("scenario", ""),
            payload.get("task", ""),
            tuple(payload.get("constraints", ())),
        )
    if kind == "trace":
        return payload.get("scenario", ""), payload.get("task", ""), ()
    return "", "", ()


def load_rubrics(lesson_dir: Path = LESSON_DIR) -> dict[str, Rubric]:
    """Every rubric across every lesson file, keyed by rubric id."""
    rubrics: dict[str, Rubric] = {}
    for path in sorted(Path(lesson_dir).glob("*.json")):
        lesson = json.loads(path.read_text())
        for exercise in lesson.get("exercises", []):
            raw = exercise.get("rubric")
            if not raw:
                continue
            scenario, task, constraints = _payload_context(exercise.get("payload", {}))
            rubric = Rubric(
                id=raw["id"],
                version=raw["version"],
                grader_tier=raw.get("grader_tier", "standard"),
                pass_threshold=raw.get("pass_threshold", 0.6),
                criteria=tuple(
                    Criterion(
                        id=c["id"],
                        check=c["check"],
                        weight=c["weight"],
                        polarity=c.get("polarity", "positive"),
                        feedback_if_missed=c.get("feedback_if_missed", ""),
                    )
                    for c in raw["criteria"]
                ),
                reference_answer=raw["reference_answer"],
                golden_set_id=raw["golden_set_id"],
                scenario=scenario,
                task=task,
                constraints=constraints,
            )
            if rubric.id in rubrics:
                raise ValueError(f"duplicate rubric id {rubric.id!r} in {path}")
            rubrics[rubric.id] = rubric
    return rubrics


def load_rubric(rubric_id: str, lesson_dir: Path = LESSON_DIR) -> Rubric:
    rubrics = load_rubrics(lesson_dir)
    if rubric_id not in rubrics:
        raise KeyError(f"no rubric {rubric_id!r}; found {sorted(rubrics)}")
    return rubrics[rubric_id]
