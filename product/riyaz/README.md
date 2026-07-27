# Riyaz

> *10 minutes a day. Get fluent in AI.*
> **"Duolingo for AI"** — a product blueprint for a daily-practice app, built on the Prompt Vidya curriculum.

This directory holds the **pre-build product blueprint**. There is no code here yet — this is the
spec you'd hand to an engineer, a designer, or a co-founder before writing any.

## Files

| File | What's in it |
|---|---|
| **[`BLUEPRINT.md`](BLUEPRINT.md)** | The main document. Naming, personas, positioning, the 10-minute loop, the 6-track curriculum, exercise types, the grading architecture, gamification economy, data model, tech stack, unit economics, monetization, metrics, a 12-week MVP plan, GTM, risks, and open decisions. |
| [`schema/lesson.schema.json`](schema/lesson.schema.json) | The authoring contract. Lessons are JSON, live in git, validated in CI, shipped by merge. |
| [`schema/samples/t1-l03-context-window.json`](schema/samples/t1-l03-context-window.json) | A **zero-LLM-cost** Foundations lesson — the shape the free tier is built from. |
| [`schema/samples/t2-l07-output-contract.json`](schema/samples/t2-l07-output-contract.json) | A Promptcraft lesson with a full rubric-graded rep and a twist. |
| [`schema/samples/t3-l04-agent-debug.json`](schema/samples/t3-l04-agent-debug.json) | A hybrid-graded agent-debugging lesson (deterministic diagnosis + free-form fix). |
| **[`grader/`](grader/README.md)** | Working spike of the grading pipeline + eval harness — the riskiest assumption in the concept, tested in ~700 lines instead of a 12-week app build. Not yet run against the live API. |

## The four things worth reading first

If you only read four sections of the blueprint, read these — they're where the real decisions are:

1. **[§9 The hard problem: grading a free-form prompt](BLUEPRINT.md#9-the-hard-problem-grading-a-free-form-prompt)**
   The grader *is* the product. Binary criteria, mandatory evidence quotes, score computed in code
   (never by the model), golden-set regression gates — plus the prompt-caching floor that decides
   whether the whole thing is affordable.
2. **[§15 Unit economics](BLUEPRINT.md#15-unit-economics--the-make-or-break-section)**
   At 10k DAU and 4% conversion the contribution margin is ~9%. That single number reshapes the
   free tier, the pricing, and the exercise mix. This is the section most likely to change your mind.
3. **[§18 MVP scope and 12-week build plan](BLUEPRINT.md#18-mvp-scope-and-12-week-build-plan)**
   30 lessons, 6 exercise types, one league. Agent debugging, RAG missions, MCP labs and SDD quests
   are all *deliberately* cut from v0 — none of them changes whether D7 retention is 25% or 8%.
4. **[§21 Open decisions](BLUEPRINT.md#21-open-decisions)**
   Eight calls only you can make: the name check, Hinglish vs English, the streak rule, price,
   the free-tier cap, platform order, team size, and whether this is a separate company.

## Status

Pre-build. Nothing validated with users. Every number in §15 is a stated assumption, not a
measurement — the point is to find the shape of the business, not to predict it.

Next concrete steps:

1. **Run the grader eval with an API key** — `python grader/evals/run_eval.py`. Costs a few cents
   and produces the two numbers that decide whether the concept works at all.
2. **Name/trademark/domain check (D1)** and **the price test (D4)** — both block work that starts
   in week 1 of the build plan.
