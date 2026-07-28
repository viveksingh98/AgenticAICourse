# CLAUDE.md — Riyaz

Context for anyone (human or agent) working in `product/riyaz/`.

## What this is

Riyaz is a daily-practice web app for AI skills — "Duolingo for AI", built on the Prompt Vidya
curriculum. One 10-minute session a day: fast warm-ups, one real graded rep, a twist, a close.

`BLUEPRINT.md` is the product spec and the source of truth for *why*. When code and blueprint
disagree, the blueprint is right and the code is a bug — or the blueprint needs an explicit,
committed update. Do not quietly diverge.

## Layout

```
product/riyaz/
├── BLUEPRINT.md              product spec — 21 sections, read §6 §9 §10 §15 before building
├── CLAUDE.md                 this file
├── .pylintrc                 lint config for everything under product/riyaz/
├── schema/
│   ├── lesson.schema.json    lesson authoring contract (JSON Schema, Draft 2020-12)
│   └── samples/*.json        3 authored lessons — the content the app serves
├── grader/                   free-form grading pipeline + eval harness (built, PR #2)
│   ├── constitution.md       the cached ~4.9k-token grading system prompt
│   ├── guards.py judge.py score.py models.py rubric.py
│   ├── evals/                run_eval.py + golden sets
│   └── tests/                32 offline tests
└── app/                      the web application
    ├── spec.md               WHAT v0 is, with acceptance criteria
    ├── plan.md               HOW — architecture, data model, API surface
    └── tasks.md              decomposed, checkable tasks
```

## Working method: spec first

This project follows spec-driven development. The order is **spec → plan → tasks → code**, and it
is not optional:

1. `spec.md` states what is being built and how you will know it works. Acceptance criteria are
   checkable statements, not vibes.
2. `plan.md` states how, including the decisions that were considered and rejected.
3. `tasks.md` decomposes the plan into units small enough to verify individually.
4. Only then, code — against the tasks, ticking them off as their acceptance criteria pass.

If you find yourself writing code for something not in `tasks.md`, stop: either it is scope creep,
or the task list is wrong and should be updated first. Both are worth a moment's thought.

The grader spike (`grader/`) was built code-first, before this discipline was adopted. That is the
one exception in this tree, and its README says so.

## Stack

| | | Why |
|---|---|---|
| Python 3.11+ | | Same language as the grader and the eval harness |
| FastAPI | web framework | Async, typed, tiny |
| SQLite | database | Zero setup; the schema is written to survive a move to Postgres |
| Jinja2 + vanilla JS | frontend | No build step. `uvicorn` and it runs. |
| pytest | tests | |
| Anthropic SDK | grading | Via `grader/` — never called directly from app code |

**No frontend build step in v0.** The moment a bundler appears, "clone and run" becomes "clone,
install node, build, and run", and this stops being something you can hand to someone.

## Commands

```bash
cd product/riyaz
pip install -r app/requirements.txt

uvicorn app.main:app --reload          # http://127.0.0.1:8000
pytest app/tests/ grader/tests/ -q     # all tests, no API key needed
pylint --rcfile=.pylintrc $(git ls-files 'product/riyaz/**/*.py')
python grader/evals/run_eval.py --offline
```

## Conventions

- **The grader is a module boundary.** App code calls `grader.grade(rubric, submission)` and nothing
  deeper. No prompt construction, no model IDs, no Anthropic imports outside `grader/`.
- **No API key must never crash the app.** Free-form grading degrades to a clearly-labelled
  unavailable state; every other exercise type keeps working. This is the normal case for a new
  contributor, not an edge case.
- **XP is an append-only ledger.** Never mutate a balance. Recomputing must always be possible.
- **Lessons are content, not code.** They live in `schema/samples/` and are validated against the
  schema at load time. Adding a lesson must never require touching Python.
- **Money is visible.** Anything that spends tokens records what it cost (`Grade.meta.cost_usd`).
- Line length 100. Type hints on public functions. `from __future__ import annotations` at the top
  of every module.

## Guardrails

- Do not add a JS framework, a bundler, or Postgres to v0. All three are in the blueprint's later
  phases; none of them makes v0 truer.
- Do not widen the free tier's LLM grading. `BLUEPRINT.md` §15 shows the margin is ~9% at 4%
  conversion; the one-graded-rep-per-day cap is load-bearing, not a growth tax.
- Do not put learner submissions into a system prompt. They are untrusted data, always in a user
  turn, always fenced — see `grader/constitution.md` §5.
- Do not change a rubric without re-running `run_eval.py`. The golden sets exist to catch exactly
  that.
