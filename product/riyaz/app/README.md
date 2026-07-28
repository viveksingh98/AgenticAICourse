# Riyaz v0 — the app

A daily-practice web app for AI skills. One 10-minute session: warm-ups, one graded rep, a
twist, a close screen.

Built spec-first: [`spec.md`](spec.md) (what + acceptance criteria) → [`plan.md`](plan.md)
(how + decisions) → [`tasks.md`](tasks.md) (decomposed work) → code.

## Run it

```bash
cd product/riyaz
pip install -r app/requirements.txt
uvicorn app.main:app --reload      # http://127.0.0.1:8000
```

No database server, no node, no build step. The SQLite file is created on first run.

## Test it

```bash
pytest app/tests/ grader/tests/ -q
```

Every test runs **without an API key**.

## What works without `ANTHROPIC_API_KEY`

| | Without a key | With a key |
|---|---|---|
| Warm-ups (choice, order, contract) | fully graded | same |
| The rep and the twist | saved, shown as "grading unavailable" | graded against the rubric, per-criterion |
| XP, streak, mastery, close screen | yes | yes |

Free-form grading is the only thing that needs credentials. Set the key and the same
submission grades against the rubric library in [`../grader/`](../grader/README.md).

## Layout

```
app/
├── spec.md plan.md tasks.md   the SDD artifacts this was built from
├── main.py          the six routes
├── content.py       loads + validates lessons from ../schema/samples/
├── grading.py       deterministic graders; the only door to ../grader/
├── progression.py   XP, streak, mastery — pure functions
├── store.py         SQLite; the XP ledger is append-only
├── templates/       Jinja2, no build step
├── static/          one stylesheet, mobile-first
└── tests/           35 tests, no API key needed
```

## Two things worth knowing

**The grader is a hard boundary.** App code calls `grader.grade(rubric, submission)` and
nothing deeper — no prompt text, no model IDs, no Anthropic import anywhere under `app/`.
Two tests enforce that by scanning the tree, so it cannot rot into a convention.

**XP is an append-only ledger.** Totals are always `SUM(amount)`; there is no balance column
that could disagree. Re-awarding the same source is a no-op, which is what makes reloading
the close screen safe.
