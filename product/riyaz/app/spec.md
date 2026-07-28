# Riyaz v0 — Specification

**Status:** draft, awaiting review
**Owner:** Vivek
**Blueprint sections this implements:** [§6 the core loop](../BLUEPRINT.md#6-the-core-loop--anatomy-of-a-10-minute-lesson),
[§8 exercise types](../BLUEPRINT.md#8-exercise-types), [§9 grading](../BLUEPRINT.md#9-the-hard-problem-grading-a-free-form-prompt),
[§10 gamification](../BLUEPRINT.md#10-gamification-economy), [§12 data model](../BLUEPRINT.md#12-data-model)

---

## 1. What v0 is

**One sentence:** a web app where a learner opens a URL, completes today's 10-minute Riyaz session
end-to-end, and watches their XP and streak advance.

v0 exists to make the loop real. Until a person can actually sit down and *do a session*, every
claim in the blueprint about retention, session length, and feedback quality is a guess. This is
the smallest thing that turns those guesses into observations.

## 2. What v0 is not

Explicitly out of scope. Each of these is in the blueprint; none of them changes whether the loop
works.

| Not in v0 | Why deferred |
|---|---|
| Accounts, login, multi-user | v0 is single-learner on localhost. Auth adds a week and tests nothing about the loop. |
| Leagues, leaderboards, battles | Need a population. With one learner they are empty screens. |
| RAG missions, connector labs, SDD quests | Each is a subsystem. Blueprint §18 cuts them from the MVP for the same reason. |
| Payments, tiers, the free-tier cap | Nothing to pay for yet. The cap is enforced in v1 when there are two tiers. |
| Mobile app | Blueprint §18 puts web first for iteration speed. |
| Content beyond the 3 authored lessons | Content velocity is a separate problem (§13). Three lessons is enough to test the loop. |
| Push notifications | Requires a device and a schedule. |

## 3. Users

One persona for v0: **the learner**. No instructor view, no admin, no author tooling — lessons are
authored by editing JSON, which is already how `schema/samples/` works.

## 4. User stories and acceptance criteria

Acceptance criteria are written so that each one is either true or false when you look at the
running app. "Feels good" is not a criterion.

### S1 — Start today's session

> As a learner, I open Riyaz and immediately see what today's practice is, without choosing
> anything.

- **A1.1** `GET /` returns the day's lesson open screen with: current streak, the lesson title, and
  the one-line brief from the lesson JSON.
- **A1.2** The open screen shows the streak *before* asking for any work. (Blueprint §6: reward
  before effort.)
- **A1.3** A single visible control starts the session. No lesson picker, no menu.
- **A1.4** Which lesson is "today's" is determined by the learner's progress: the lowest
  `day_index` among published lessons they have not completed. When all are complete, the app says
  so rather than erroring.

### S2 — Warm-ups grade instantly and for free

> As a learner, I answer 3–4 quick questions and know immediately whether I was right.

- **A2.1** Exercise types `spot_the_flaw`, `predict_the_output`, `budget_call` render their stem,
  optional context block, and options; selecting one submits.
- **A2.2** `order_the_steps` renders a reorderable list and accepts a submitted order.
- **A2.3** `fill_the_contract` renders an editable text area seeded with `starter` and validates the
  submission against `target_schema`.
- **A2.4** Every warm-up is graded **server-side with zero LLM calls**. Verified by: with
  `ANTHROPIC_API_KEY` unset, all warm-ups still grade correctly.
- **A2.5** After answering, the learner sees correct/incorrect **and** the `explanation` from the
  lesson JSON — on both right and wrong answers.
- **A2.6** The correct answer is never present in any response sent to the browser before the
  learner submits. Verified by a test that asserts `correct_index` is absent from the pre-submit
  payload.

### S3 — The rep is graded against a rubric

> As a learner, I write a real prompt and get a specific verdict on it, not a vibe.

- **A3.1** The rep exercise renders scenario, task, and the stated constraints from the lesson JSON.
- **A3.2** Submitting calls `grader.grade(rubric, submission)` and nothing deeper. No prompt
  construction or model IDs exist in app code.
- **A3.3** The result shows the score, and a per-criterion breakdown of which criteria were met.
- **A3.4** For any unmet criterion, the learner sees that criterion's `feedback_if_missed` verbatim.
- **A3.5** Guard rejections (too short, empty) return the guard's feedback and **do not** spend a
  grading call.
- **A3.6** With no API key configured, the rep submits, is stored, and shows an explicit
  "grading unavailable" state. The app does not crash, and the session can still be completed.
- **A3.7** The reference answer is shown only after the learner has submitted.
- **A3.8** The grade record stores `rubric_version`, `grader_model`, and `cost_usd`.

### S4 — The twist

> As a learner, the scenario changes after I have answered, and I have to adapt.

- **A4.1** A `twist`-slot exercise renders after the rep, showing what changed
  (`payload.twist_change`) and the learner's own prior submission for reference.
- **A4.2** The twist is graded by its own rubric, on the same path as the rep.
- **A4.3** If the lesson has no twist, the session proceeds to the close screen without one.

### S5 — The session closes on a win

> As a learner, I finish knowing what I earned and what I learned.

- **A5.1** The close screen shows XP earned this session, broken down per exercise.
- **A5.2** It shows the new streak count and states whether the streak advanced today.
- **A5.3** It leads with something the learner got right, even when the rep scored below the pass
  threshold. (Blueprint §6: the session ends on a win.)
- **A5.4** It names tomorrow's lesson title.
- **A5.5** Completing a session is idempotent: reloading the close screen does not award XP twice.

### S6 — Progress persists

> As a learner, my streak and XP survive a restart.

- **A6.1** XP is an append-only ledger. No row is ever updated or deleted.
- **A6.2** Total XP is always recomputable by summing the ledger; the app never stores a
  denormalised balance it could disagree with.
- **A6.3** The streak advances on **one completed session per day**, not on XP.
- **A6.4** The streak is forgiving (blueprint §10, decision D3), displayed as an unbroken count:
  it survives up to **2 missed days in a row** and ends on the third. Three consecutive misses is
  also the point at which a trailing 7-day window can no longer hold 5 completed days, so this is
  the checkable form of the "5-of-7" rule rather than a different rule.
- **A6.5** Restarting the server preserves streak, XP, and which lessons are complete.
- **A6.6** Per-skill mastery is recorded on completion with a decay timestamp, so the spaced-
  repetition engine in v1 has data to work with.

### S7 — It runs

- **A7.1** `pip install -r app/requirements.txt && uvicorn app.main:app` starts a working app with
  no other setup — no database server, no node, no build step.
- **A7.2** The database is created on first run if absent.
- **A7.3** All tests pass with no API key set.
- **A7.4** A lesson JSON that fails schema validation is rejected at load with a message naming the
  file — it never half-loads.

## 5. Non-functional requirements

- **N1** Warm-up grading responds in under 100ms locally (no network involved).
- **N2** Rep grading streams or shows progress; the learner is never looking at an unexplained
  blank screen. Blueprint §6 targets under 8 seconds.
- **N3** A learner submission is never placed in a system prompt. Enforced by A3.2 — app code cannot
  build prompts.
- **N4** No secret is ever rendered into a page or logged.
- **N5** The app is usable at 375px wide (phone), because that is where the blueprint says the
  session happens.

## 6. Open questions

| # | Question | Blocking? | Default if unanswered |
|---|---|---|---|
| Q1 | Hinglish or English UI chrome? | No | Follow the lesson content: Hinglish, matching blueprint D2 |
| Q2 | Should the twist be skippable? | No | No — it is where transfer happens |
| Q3 | Show cost per grade to the learner? | No | No. Useful in dev; noise for a learner. Keep it in the DB and the dev log. |

## 7. Definition of done

Every acceptance criterion above is either demonstrated by an automated test or checkable by
opening the app. `tasks.md` maps each task to the criteria it satisfies, and no task is complete
until its criteria pass.
