"""T2 — lesson loading and validation.

Lessons are content, not code: they live in ../schema/samples/ as JSON and are validated
against the authoring schema at startup. A lesson that fails validation is fatal and names
its file — a half-loaded lesson that breaks on exercise four is far worse than a server
that refuses to start (spec A7.4).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator

RIYAZ_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = RIYAZ_ROOT / "schema" / "lesson.schema.json"
LESSON_DIR = RIYAZ_ROOT / "schema" / "samples"

# Keys the browser must never see before the learner submits (spec A2.6, A3.7).
WITHHELD_PAYLOAD_KEYS = frozenset(
    {"correct_index", "correct_order", "target_schema", "explanation", "forbidden_patterns"}
)


class ContentError(RuntimeError):
    """A lesson file is missing, malformed, or fails schema validation."""


@dataclass(frozen=True)
class Exercise:
    """One exercise, with its lesson context and its answer key kept server-side."""

    id: str
    ordinal: int
    slot: str
    type: str
    payload: dict
    rubric: dict | None
    xp_base: int
    lesson_id: str

    @property
    def kind(self) -> str:
        """The payload shape: choice | order | contract | freeform | trace."""
        return self.payload.get("kind", "")

    @property
    def is_freeform(self) -> bool:
        """Whether grading this needs the rubric judge rather than a deterministic check."""
        return self.rubric is not None

    def for_browser(self) -> dict:
        """The payload minus everything that would give the answer away (T6)."""
        return {k: v for k, v in self.payload.items() if k not in WITHHELD_PAYLOAD_KEYS}


@dataclass(frozen=True)
class Lesson:
    """One authored lesson: a day's session."""

    id: str
    track: str
    skill_id: str
    day_index: int
    title: str
    brief: str
    est_seconds: int
    exercises: tuple[Exercise, ...]

    def exercise(self, ordinal: int) -> Exercise | None:
        return next((e for e in self.exercises if e.ordinal == ordinal), None)

    @property
    def last_ordinal(self) -> int:
        return max(e.ordinal for e in self.exercises)


def _validator() -> Draft202012Validator:
    with open(SCHEMA_PATH, encoding="utf-8") as handle:
        schema = json.load(handle)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _parse(path: Path, validator: Draft202012Validator) -> Lesson:
    try:
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
    except json.JSONDecodeError as exc:
        raise ContentError(f"{path.name}: not valid JSON — {exc}") from exc

    errors = sorted(validator.iter_errors(raw), key=lambda e: list(e.path))
    if errors:
        first = errors[0]
        where = " -> ".join(str(p) for p in first.path) or "(root)"
        raise ContentError(
            f"{path.name}: {len(errors)} schema error(s); first at {where}: {first.message}"
        )

    exercises = tuple(
        Exercise(
            id=item["id"],
            ordinal=item["ordinal"],
            slot=item["slot"],
            type=item["type"],
            payload=item["payload"],
            rubric=item.get("rubric"),
            xp_base=item.get("xp_base", 5),
            lesson_id=raw["id"],
        )
        for item in sorted(raw["exercises"], key=lambda e: e["ordinal"])
    )
    return Lesson(
        id=raw["id"],
        track=raw["track"],
        skill_id=raw["skill_id"],
        day_index=raw["day_index"],
        title=raw["title"],
        brief=raw["brief"],
        est_seconds=raw["est_seconds"],
        exercises=exercises,
    )


@lru_cache(maxsize=1)
def all_lessons(lesson_dir: Path = LESSON_DIR) -> tuple[Lesson, ...]:
    """Every lesson, ordered by day_index. Cached — lessons are immutable at runtime."""
    validator = _validator()
    paths = sorted(Path(lesson_dir).glob("*.json"))
    if not paths:
        raise ContentError(f"no lessons found in {lesson_dir}")
    lessons = tuple(sorted((_parse(p, validator) for p in paths), key=lambda le: le.day_index))
    seen: set[str] = set()
    for lesson in lessons:
        if lesson.id in seen:
            raise ContentError(f"duplicate lesson id {lesson.id!r}")
        seen.add(lesson.id)
    return lessons


def lesson_by_id(lesson_id: str) -> Lesson | None:
    return next((le for le in all_lessons() if le.id == lesson_id), None)


def next_lesson_for(completed_ids: set[str]) -> Lesson | None:
    """Today's lesson: the lowest day_index not yet completed, or None when all are done."""
    return next((le for le in all_lessons() if le.id not in completed_ids), None)
