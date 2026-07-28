# Riyaz v0 — Technical Plan

Implements [`spec.md`](spec.md). Read that first — this file answers *how*, and every decision
below traces to an acceptance criterion there.

---

## 1. Shape

```
browser
  │  HTML (Jinja2) + fetch() for submissions
  ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI  (app/main.py)                                  │
│                                                          │
│  routes.py     HTTP surface, session flow                │
│  content.py    loads + validates lessons from JSON        │
│  grading.py    deterministic graders (types 1–5)          │
│                → delegates free-form to grader/           │
│  progression.py XP formula, streak rule, mastery          │
│  store.py      SQLite, append-only ledger                 │
└────────────┬───────────────────────────┬─────────────────┘
             │                           │
             ▼                           ▼
     riyaz.db (SQLite)          ../grader/  (existing package)
                                          │
                                          ▼
                                  Anthropic API (optional)
```

Five modules, each with one job. `grading.py` is the only one that talks to `grader/`, and it does
so through the single `grade()` entry point — that boundary is what makes A3.2 checkable.

## 2. Decisions

### D1 — Server-rendered HTML, not a SPA

**Chosen:** Jinja2 templates, one page per session step, `fetch()` only for submitting an answer
and swapping in the result.

**Rejected:** React/Vue SPA. It needs a bundler, which turns "clone and run" into "clone, install
node, build, run" and breaks A7.1. v0 has five screens and no client-side state worth a framework.

**Cost of being wrong:** if v1 needs richer interaction, the templates are throwaway. That is
acceptable — they are ~300 lines, and the API surface underneath them is what has real value.

### D2 — SQLite, schema written for Postgres

**Chosen:** SQLite via the stdlib `sqlite3`, no ORM.

**Rejected:** Postgres (needs a server — breaks A7.1); SQLAlchemy (an ORM earns its keep at more
than seven tables).

**Mitigation:** no SQLite-only syntax. Timestamps stored as ISO-8601 UTC text, IDs as explicit
integers, no `AUTOINCREMENT` quirks relied on. Moving to Postgres should be a driver swap.

### D3 — Content is loaded and validated at startup

Lessons are read from `../schema/samples/*.json`, validated against `lesson.schema.json`, and held
in memory. They are small (three files) and immutable at runtime.

A validation failure is **fatal at startup**, naming the file (A7.4). A half-loaded lesson that
breaks on exercise four is far worse than a server that refuses to start.

### D4 — The grader boundary

`grading.py` exposes:

```python
def grade_deterministic(exercise: Exercise, submission) -> ExerciseResult   # no LLM, no cost
def grade_freeform(exercise: Exercise, submission: str) -> ExerciseResult   # delegates to grader/
```

`grade_freeform` imports exactly `from grader import grade, load_rubric`. No model IDs, no prompt
text, no Anthropic import anywhere in `app/`. A test asserts this by scanning `app/**/*.py` for
`anthropic` — which is how A3.2 stops being a promise and becomes a check.

### D5 — Missing API key is a first-class state, not an error

`grade_freeform` catches the missing-credential case and returns
`ExerciseResult(status="grading_unavailable", ...)`. The session continues, the submission is
stored, XP is awarded for completion but not for quality.

This is the *normal* state for someone who just cloned the repo, so it gets a designed screen
rather than a stack trace (A3.6).

### D6 — The XP ledger is append-only

`xp_ledger(id, occurred_at, source_type, source_id, amount, note)`. Inserts only. Totals are always
`SELECT SUM(amount)`. No balance column exists to disagree with the ledger (A6.1, A6.2).

Idempotency for A5.5: `(source_type, source_id)` carries a unique index, so re-completing a session
is a no-op rather than a double award.

### D7 — Streak is 5-of-7, computed not stored

Per blueprint §10 and decision D3 there. `session_days` holds one row per day a session was
completed. The streak is derived by walking backwards from today and allowing up to two missed days
in any rolling seven.

**Why computed rather than stored:** a stored counter has to be repaired when the rule changes, and
the rule is explicitly still under test (blueprint D3 says A/B it). Derived means changing the rule
is a one-function change with no migration.

### D8 — Grading a warm-up never trusts the client

The pre-submit payload for an exercise omits `correct_index`, `correct_order`, and `target_schema`
(A2.6). Grading happens server-side against the in-memory lesson. The browser is shown only what it
needs to render.

## 3. Data model

```sql
CREATE TABLE learner (            -- exactly one row in v0
  id            INTEGER PRIMARY KEY,
  handle        TEXT NOT NULL,
  tz            TEXT NOT NULL DEFAULT 'Asia/Kolkata',
  created_at    TEXT NOT NULL
);

CREATE TABLE session (
  id            INTEGER PRIMARY KEY,
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  lesson_id     TEXT    NOT NULL,
  started_at    TEXT    NOT NULL,
  completed_at  TEXT,                        -- NULL until the close screen
  UNIQUE (learner_id, lesson_id, started_at)
);

CREATE TABLE attempt (
  id            INTEGER PRIMARY KEY,
  session_id    INTEGER NOT NULL REFERENCES session(id),
  exercise_id   TEXT    NOT NULL,
  submission    TEXT    NOT NULL,            -- JSON for structured, raw text for free-form
  submitted_at  TEXT    NOT NULL,
  latency_ms    INTEGER,
  UNIQUE (session_id, exercise_id)           -- one attempt per exercise per session
);

CREATE TABLE grade (
  attempt_id      INTEGER PRIMARY KEY REFERENCES attempt(id),
  status          TEXT    NOT NULL,          -- graded | rejected | grading_unavailable
  score           REAL    NOT NULL,          -- 0.0–1.0
  passed          INTEGER NOT NULL,
  feedback        TEXT    NOT NULL,
  criteria_json   TEXT,                      -- per-criterion trace, free-form only
  rubric_id       TEXT,
  rubric_version  INTEGER,
  grader_model    TEXT,
  cost_micro_usd  INTEGER NOT NULL DEFAULT 0,
  flipped_count   INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE xp_ledger (
  id            INTEGER PRIMARY KEY,
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  occurred_at   TEXT    NOT NULL,
  source_type   TEXT    NOT NULL,            -- exercise | session_bonus | streak_bonus
  source_id     TEXT    NOT NULL,
  amount        INTEGER NOT NULL,
  note          TEXT
);
CREATE UNIQUE INDEX xp_ledger_source ON xp_ledger (learner_id, source_type, source_id);

CREATE TABLE session_day (
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  day           TEXT    NOT NULL,            -- YYYY-MM-DD, learner's timezone
  PRIMARY KEY (learner_id, day)
);

CREATE TABLE mastery (
  learner_id    INTEGER NOT NULL REFERENCES learner(id),
  skill_id      TEXT    NOT NULL,
  score         REAL    NOT NULL,
  last_seen_at  TEXT    NOT NULL,
  PRIMARY KEY (learner_id, skill_id)
);
```

`grade` is keyed by `attempt_id` rather than carrying its own id — one grade per attempt, always.

## 4. HTTP surface

| Method | Path | Purpose | Criteria |
|---|---|---|---|
| GET | `/` | Open screen: streak, today's lesson, start control | A1.1–A1.4 |
| POST | `/session/start` | Create a session, redirect to the first exercise | A1.3 |
| GET | `/session/{id}/exercise/{ordinal}` | Render one exercise (answer withheld) | A2.1–A2.3, A3.1, A4.1, D8 |
| POST | `/session/{id}/exercise/{ordinal}` | Submit, grade, return the result fragment | A2.4–A2.6, A3.2–A3.8, A4.2 |
| GET | `/session/{id}/complete` | Close screen: XP breakdown, streak, tomorrow | A5.1–A5.5 |
| GET | `/healthz` | Liveness + whether grading is configured | — |

Submissions POST as JSON and get back a rendered HTML fragment, which the page swaps in. Enough
interactivity for a result reveal, no client-side router.

## 5. XP

Straight from blueprint §10, in `progression.py`:

```
xp = BASE[slot] × QUALITY(score) × FIRST_TRY + STREAK_BONUS
```

| | |
|---|---|
| `BASE` | warmup 5, rep 30, twist 20 |
| `QUALITY` | <0.60 → 0.5; 0.60–0.84 → 1.0; ≥0.85 → 1.3 |
| `FIRST_TRY` | 1.25 (v0 has no retry, so always 1.25 — kept explicit so v1 does not have to rediscover it) |
| `STREAK_BONUS` | `min(streak, 30) × 0.5`, once per session |

A poor attempt still earns XP. Showing up is the reinforced behaviour; quality is the multiplier,
not the gate.

## 6. Testing

| Layer | What | Needs a key? |
|---|---|---|
| `test_content.py` | lessons load, validate, bad lesson rejected by name | no |
| `test_grading.py` | every deterministic type; answers withheld pre-submit | no |
| `test_progression.py` | XP arithmetic, 5-of-7 streak incl. boundaries, idempotency | no |
| `test_store.py` | ledger append-only, totals recompute, restart survives | no |
| `test_routes.py` | full session end-to-end via `TestClient`, key absent | no |
| `test_boundaries.py` | no `anthropic` import under `app/`; no secret in any response | no |

Every test runs without credentials (A7.3). The free-form path is exercised through a stub
`grade()` — the real one already has its own 32 tests and an eval harness.

## 7. Sequencing

Build order is chosen so something is runnable early and each layer is testable before the next
depends on it:

1. store + content (nothing renders, but tests pass)
2. progression (pure functions, fully testable alone)
3. deterministic grading
4. routes + templates — **first point where the app runs**
5. free-form rep via `grader/`
6. twist, close screen, polish

## 8. Risks

| Risk | Mitigation |
|---|---|
| Free-form grading is slow enough to feel broken | Show a designed pending state immediately; blueprint §6 targets <8s (N2) |
| Three lessons is too little to feel like a habit | Accepted for v0 — the loop is what is being tested, not retention |
| SQLite concurrency | Single learner, single process. Revisit at multi-user, not before. |
| Templates thrown away in v1 | Accepted and cheap (D1) |
