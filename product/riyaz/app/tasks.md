# Riyaz v0 — Tasks

Decomposed from [`plan.md`](plan.md) §7. Each task names the [`spec.md`](spec.md) acceptance
criteria it satisfies and how it is verified. **A task is done when its criteria pass, not when the
code is written.**

Order matters — each layer is testable before anything depends on it.

---

## Phase 1 — Foundations (nothing renders yet)

### T1 — Package skeleton and dependencies
- [x] `app/__init__.py`, `app/requirements.txt`, `app/main.py` stub
- [x] `fastapi`, `uvicorn`, `jinja2`, `jsonschema`, `pytest`, `httpx` (for `TestClient`)
- **Satisfies:** A7.1 (partly)
- **Verify:** `pip install -r app/requirements.txt` succeeds; `uvicorn app.main:app` starts

### T2 — Content loader
- [x] `content.py`: load `../schema/samples/*.json`, validate against `lesson.schema.json`
- [x] Typed accessors: `Lesson`, `Exercise`; `exercises_in_order()`, `rep_exercise()`
- [x] Fatal, file-named error on validation failure
- [x] `next_lesson_for(completed_ids)` → lowest unfinished `day_index`, `None` when all done
- **Satisfies:** A1.4, A7.4
- **Verify:** `test_content.py` — 3 lessons load; a deliberately broken lesson raises naming the file

### T3 — Store
- [x] `store.py`: schema DDL from plan §3, created on first run
- [x] `add_xp()` idempotent on `(source_type, source_id)`; `total_xp()` sums the ledger
- [x] `record_session_day()`, `completed_lesson_ids()`, attempt/grade writes
- [x] No UPDATE or DELETE against `xp_ledger` anywhere
- **Satisfies:** A6.1, A6.2, A6.5, A7.2
- **Verify:** `test_store.py` — double award is a no-op; totals recompute; reopening the DB preserves state

### T4 — Progression
- [x] `progression.py`: `xp_for(slot, score, first_try, streak)` per plan §5
- [x] `streak_from_days(days, today)` — 5-of-7 rolling
- [x] `record_mastery()`
- **Satisfies:** A6.3, A6.4, A6.6
- **Verify:** `test_progression.py` — XP table cases; streak at the 5-of-7 boundary, a 2-day gap
  (holds) and a 3-day gap (breaks)

## Phase 2 — Grading

### T5 — Deterministic graders
- [x] `grading.py`: `choice`, `order` (with partial credit), `contract` (JSON Schema validate)
- [x] Returns `ExerciseResult(status, score, passed, feedback, explanation)`
- [x] Zero LLM calls on this path
- **Satisfies:** A2.4, A2.5
- **Verify:** `test_grading.py` — each type, right and wrong; passes with `ANTHROPIC_API_KEY` unset

### T6 — Answer withholding
- [x] `Exercise.for_browser()` strips `correct_index`, `correct_order`, `target_schema`,
      `explanation`, `reference_answer`
- **Satisfies:** A2.6, A3.7
- **Verify:** `test_grading.py` asserts the stripped keys are absent from the payload

### T7 — Free-form grading via `grader/`
- [x] `grade_freeform()` → `grader.grade(rubric, submission)`, nothing deeper
- [x] Guard rejection returns feedback and spends no grading call
- [x] Missing key → `status="grading_unavailable"`, session continues
- [x] Persist `rubric_version`, `grader_model`, `cost_micro_usd`, `flipped_count`
- **Satisfies:** A3.2, A3.5, A3.6, A3.8
- **Verify:** `test_grading.py` with a stubbed `grade()`; `test_boundaries.py` scans `app/**/*.py`
  for `anthropic` and fails if found

## Phase 3 — The app runs

### T8 — Routes
- [x] The six endpoints in plan §4
- [x] `POST /session/start` creates a session and redirects
- [x] Submit returns a rendered result fragment
- **Satisfies:** A1.1, A1.3, A3.1
- **Verify:** `test_routes.py` walks a full session end-to-end

### T9 — Templates
- [x] `base.html`, `open.html`, `exercise.html`, `_result.html`, `complete.html`, `styles.css`
- [x] Streak visible on the open screen before any work is asked for
- [x] Readable at 375px
- **Satisfies:** A1.1, A1.2, A2.1–A2.3, N5
- **Verify:** by eye at 375px; `test_routes.py` asserts streak and title appear in `GET /`

### T10 — Rep and twist screens
- [x] Rep renders scenario, task, constraints; textarea with min/max
- [x] Result shows score, per-criterion breakdown, `feedback_if_missed` verbatim
- [x] Twist shows `twist_change` and the learner's prior submission
- [x] Lesson with no twist proceeds straight to the close screen
- **Satisfies:** A3.1, A3.3, A3.4, A4.1–A4.3
- **Verify:** `test_routes.py`; visually for the t2-l07 lesson

### T11 — Close screen
- [x] Per-exercise XP breakdown, new streak, whether it advanced, tomorrow's title
- [x] Leads with something the learner got right, even on a failed rep
- [x] Idempotent — reload awards nothing further
- **Satisfies:** A5.1–A5.5
- **Verify:** `test_routes.py` completes a session twice and asserts XP is unchanged

## Phase 4 — Close out

### T12 — Pending state for slow grading
- [x] Submit shows a designed pending state immediately, not a blank screen
- **Satisfies:** N2
- **Verify:** by eye with the grader stubbed to sleep

### T13 — Docs and CI
- [x] `app/README.md`: run it, test it, what works without a key
- [x] App tests added to the CI job
- [x] `pylint --rcfile=.pylintrc` clean across `app/`
- **Satisfies:** A7.1, A7.3
- **Verify:** the CI `check` job

---

## Out of scope — do not build

Auth, leagues, battles, missions, payments, push, mobile, content authoring UI, retry-a-rep.
All are in `spec.md` §2 with reasons. If one of these starts to feel necessary, that is a spec
change to discuss — not a task to quietly add.

## Progress

| Phase | Tasks | Done |
|---|---|---|
| 1 Foundations | T1–T4 | 4/4 |
| 2 Grading | T5–T7 | 3/3 |
| 3 The app runs | T8–T11 | 4/4 |
| 4 Close out | T12–T13 | 2/2 |
