"""T4 — XP, streaks, mastery.

Pure functions over plain data, so the rules are testable without a database or a
request. Every formula here comes from BLUEPRINT.md section 10.
"""

from __future__ import annotations

from datetime import date, timedelta

# Blueprint section 10. A bad attempt still earns XP: showing up is the behaviour being
# reinforced, and quality is the multiplier rather than the gate.
BASE_XP = {"warmup": 5, "rep": 30, "twist": 20}

QUALITY_FLOOR = 0.5  # below 60%
QUALITY_MID = 1.0  # 60-84%
QUALITY_HIGH = 1.3  # 85%+
FIRST_TRY_MULTIPLIER = 1.25
STREAK_BONUS_CAP_DAYS = 30

# Blueprint decision D3: a forgiving streak, shown as an unbroken count. Strict daily
# streaks punish people with families and jobs — which is the paying persona.
#
# Operationally that is "at most 2 missed days in a row". Three consecutive misses is
# also exactly the point at which a trailing 7-day window can no longer hold 5 completed
# days, so this is the simple, checkable form of the 5-of-7 rule rather than a different
# one. Derived rather than stored, so changing it needs no migration (plan D7).
MAX_CONSECUTIVE_MISSES = 2


def quality_multiplier(score: float) -> float:
    if score < 0.60:
        return QUALITY_FLOOR
    if score < 0.85:
        return QUALITY_MID
    return QUALITY_HIGH


def xp_for(slot: str, score: float, first_try: bool = True) -> int:
    """XP for one exercise, before the once-per-session streak bonus."""
    base = BASE_XP.get(slot, BASE_XP["warmup"])
    multiplier = quality_multiplier(score) * (FIRST_TRY_MULTIPLIER if first_try else 1.0)
    return round(base * multiplier)


def streak_bonus(streak_days: int) -> int:
    return round(min(streak_days, STREAK_BONUS_CAP_DAYS) * 0.5)


def streak_from_days(days: set[str] | list[str], today: date) -> int:
    """Current streak: completed days walking back from today, ending at 3 misses in a row.

    Returns the number of completed days in the surviving run — that is the flame the
    learner sees. A gap of one or two days keeps the streak; a third consecutive silent
    day ends it.
    """
    completed = {d if isinstance(d, str) else d.isoformat() for d in days}
    if not completed:
        return 0

    counted = 0
    consecutive_misses = 0
    cursor = today
    oldest = min(completed)

    while cursor.isoformat() >= oldest:
        if cursor.isoformat() in completed:
            counted += 1
            consecutive_misses = 0
        else:
            consecutive_misses += 1
            if consecutive_misses > MAX_CONSECUTIVE_MISSES:
                break
        cursor -= timedelta(days=1)

    return counted


def mastery_after(previous: float | None, score: float) -> float:
    """Blend a new result into a skill's mastery.

    Weighted toward the new observation but not fully replacing it, so one bad session on
    a known skill does not erase the record. Feeds the spaced-repetition engine in v1
    (spec A6.6).
    """
    if previous is None:
        return round(score, 4)
    return round(previous * 0.6 + score * 0.4, 4)
