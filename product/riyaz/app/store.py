"""T3 — persistence.

SQLite, no ORM, schema written so a move to Postgres is a driver swap (plan D2).

The one rule that matters here: the XP ledger is append-only. There is no balance column
to disagree with the ledger, and re-awarding the same source is a no-op rather than a
double credit (plan D6, spec A6.1/A6.2/A5.5).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "riyaz.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS learner (
  id            INTEGER PRIMARY KEY,
  handle        TEXT NOT NULL,
  tz            TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  created_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS session (
  id            INTEGER PRIMARY KEY,
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  lesson_id     TEXT    NOT NULL,
  started_at    TEXT    NOT NULL,
  completed_at  TEXT
);

CREATE TABLE IF NOT EXISTS attempt (
  id            INTEGER PRIMARY KEY,
  session_id    INTEGER NOT NULL REFERENCES session(id),
  exercise_id   TEXT    NOT NULL,
  submission    TEXT    NOT NULL,
  submitted_at  TEXT    NOT NULL,
  latency_ms    INTEGER,
  UNIQUE (session_id, exercise_id)
);

CREATE TABLE IF NOT EXISTS grade (
  attempt_id      INTEGER PRIMARY KEY REFERENCES attempt(id),
  status          TEXT    NOT NULL,
  score           REAL    NOT NULL,
  passed          INTEGER NOT NULL,
  feedback        TEXT    NOT NULL,
  criteria_json   TEXT,
  rubric_id       TEXT,
  rubric_version  INTEGER,
  grader_model    TEXT,
  cost_micro_usd  INTEGER NOT NULL DEFAULT 0,
  flipped_count   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS xp_ledger (
  id            INTEGER PRIMARY KEY,
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  occurred_at   TEXT    NOT NULL,
  source_type   TEXT    NOT NULL,
  source_id     TEXT    NOT NULL,
  amount        INTEGER NOT NULL,
  note          TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS xp_ledger_source
  ON xp_ledger (learner_id, source_type, source_id);

CREATE TABLE IF NOT EXISTS session_day (
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  day           TEXT    NOT NULL,
  PRIMARY KEY (learner_id, day)
);

CREATE TABLE IF NOT EXISTS mastery (
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  skill_id      TEXT    NOT NULL,
  score         REAL    NOT NULL,
  last_seen_at  TEXT    NOT NULL,
  PRIMARY KEY (learner_id, skill_id)
);
"""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Store:
    """All database access. Every timestamp is ISO-8601 UTC text; no SQLite-only syntax."""

    def __init__(self, path: Path | str = DB_PATH):
        self.path = str(path)
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ------------------------------------------------------------------ learner

    def learner(self, handle: str = "you") -> sqlite3.Row:
        """The single v0 learner, created on first call."""
        row = self.conn.execute("SELECT * FROM learner ORDER BY id LIMIT 1").fetchone()
        if row is None:
            self.conn.execute(
                "INSERT INTO learner (handle, created_at) VALUES (?, ?)", (handle, now_iso())
            )
            self.conn.commit()
            row = self.conn.execute("SELECT * FROM learner ORDER BY id LIMIT 1").fetchone()
        return row

    # ------------------------------------------------------------------ sessions

    def start_session(self, learner_id: int, lesson_id: str) -> int:
        """Resume the open session for this lesson if there is one, else create it.

        Resuming rather than always inserting is what lets a learner close the tab
        mid-session and pick up where they left off.
        """
        row = self.conn.execute(
            "SELECT id FROM session WHERE learner_id = ? AND lesson_id = ? AND completed_at IS NULL"
            " ORDER BY id DESC LIMIT 1",
            (learner_id, lesson_id),
        ).fetchone()
        if row:
            return int(row["id"])
        cursor = self.conn.execute(
            "INSERT INTO session (learner_id, lesson_id, started_at) VALUES (?, ?, ?)",
            (learner_id, lesson_id, now_iso()),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def session(self, session_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM session WHERE id = ?", (session_id,)).fetchone()

    def complete_session(self, session_id: int) -> bool:
        """Mark complete. Returns False if it already was — the caller uses this for A5.5."""
        row = self.session(session_id)
        if row is None or row["completed_at"] is not None:
            return False
        self.conn.execute(
            "UPDATE session SET completed_at = ? WHERE id = ?", (now_iso(), session_id)
        )
        self.conn.commit()
        return True

    def completed_lesson_ids(self, learner_id: int) -> set[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT lesson_id FROM session"
            " WHERE learner_id = ? AND completed_at IS NOT NULL",
            (learner_id,),
        ).fetchall()
        return {r["lesson_id"] for r in rows}

    # ------------------------------------------------------- attempts and grades

    def record_attempt(
        self, session_id: int, exercise_id: str, submission, latency_ms: int | None = None
    ) -> int:
        payload = submission if isinstance(submission, str) else json.dumps(submission)
        self.conn.execute(
            "INSERT OR REPLACE INTO attempt"
            " (id, session_id, exercise_id, submission, submitted_at, latency_ms)"
            " VALUES ((SELECT id FROM attempt WHERE session_id = ? AND exercise_id = ?),"
            "         ?, ?, ?, ?, ?)",
            (session_id, exercise_id, session_id, exercise_id, payload, now_iso(), latency_ms),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT id FROM attempt WHERE session_id = ? AND exercise_id = ?",
            (session_id, exercise_id),
        ).fetchone()
        return int(row["id"])

    def record_grade(self, attempt_id: int, result) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO grade (attempt_id, status, score, passed, feedback,"
            " criteria_json, rubric_id, rubric_version, grader_model, cost_micro_usd,"
            " flipped_count) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                attempt_id,
                result.status,
                result.score,
                int(result.passed),
                result.feedback,
                json.dumps(result.criteria) if result.criteria else None,
                result.rubric_id,
                result.rubric_version,
                result.grader_model,
                result.cost_micro_usd,
                result.flipped_count,
            ),
        )
        self.conn.commit()

    def attempt_for(self, session_id: int, exercise_id: str) -> sqlite3.Row | None:
        return self.conn.execute(
            "SELECT a.*, g.status, g.score, g.passed, g.feedback, g.criteria_json"
            " FROM attempt a LEFT JOIN grade g ON g.attempt_id = a.id"
            " WHERE a.session_id = ? AND a.exercise_id = ?",
            (session_id, exercise_id),
        ).fetchone()

    def session_attempts(self, session_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT a.*, g.status, g.score, g.passed, g.feedback"
            " FROM attempt a LEFT JOIN grade g ON g.attempt_id = a.id"
            " WHERE a.session_id = ? ORDER BY a.id",
            (session_id,),
        ).fetchall()

    # ------------------------------------------------------------------ XP

    def add_xp(
        self, learner_id: int, source_type: str, source_id: str, amount: int, note: str = ""
    ) -> bool:
        """Append to the ledger. Returns False when this source was already awarded.

        The unique index on (learner_id, source_type, source_id) is what makes a reloaded
        close screen a no-op instead of a second award.
        """
        try:
            self.conn.execute(
                "INSERT INTO xp_ledger"
                " (learner_id, occurred_at, source_type, source_id, amount, note)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (learner_id, now_iso(), source_type, source_id, amount, note),
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def total_xp(self, learner_id: int) -> int:
        row = self.conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total FROM xp_ledger WHERE learner_id = ?",
            (learner_id,),
        ).fetchone()
        return int(row["total"])

    def xp_entries_for_session(self, learner_id: int, session_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM xp_ledger WHERE learner_id = ? AND source_id LIKE ?"
            " ORDER BY id",
            (learner_id, f"{session_id}:%"),
        ).fetchall()

    # ------------------------------------------------------- streak and mastery

    def record_session_day(self, learner_id: int, day: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO session_day (learner_id, day) VALUES (?, ?)", (learner_id, day)
        )
        self.conn.commit()

    def session_days(self, learner_id: int) -> list[str]:
        rows = self.conn.execute(
            "SELECT day FROM session_day WHERE learner_id = ? ORDER BY day", (learner_id,)
        ).fetchall()
        return [r["day"] for r in rows]

    def record_mastery(self, learner_id: int, skill_id: str, score: float) -> None:
        self.conn.execute(
            "INSERT INTO mastery (learner_id, skill_id, score, last_seen_at) VALUES (?, ?, ?, ?)"
            " ON CONFLICT (learner_id, skill_id) DO UPDATE SET score = ?, last_seen_at = ?",
            (learner_id, skill_id, score, now_iso(), score, now_iso()),
        )
        self.conn.commit()

    def mastery(self, learner_id: int) -> dict[str, float]:
        rows = self.conn.execute(
            "SELECT skill_id, score FROM mastery WHERE learner_id = ?", (learner_id,)
        ).fetchall()
        return {r["skill_id"]: r["score"] for r in rows}
