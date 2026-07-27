# Riyaz — Product Blueprint

> **Riyaz** (रियाज़) — the daily practice a musician does. Not a performance, not a course. A habit.
>
> **Tagline:** *10 minutes a day. Get fluent in AI.*
>
> **Positioning line:** *Duolingo for AI — by Prompt Vidya.*

Status: **v0 blueprint / pre-build.** Everything here is a proposal with stated assumptions.
Nothing has been validated with users yet. Sections marked **⚠️ Decision needed** require a call
from you before engineering starts.

---

## Table of contents

1. [The name](#1-the-name)
2. [One-paragraph pitch](#2-one-paragraph-pitch)
3. [Why this, why now](#3-why-this-why-now)
4. [Who it's for](#4-who-its-for)
5. [Competitive positioning](#5-competitive-positioning)
6. [The core loop — anatomy of a 10-minute lesson](#6-the-core-loop--anatomy-of-a-10-minute-lesson)
7. [The skill tree — 6 tracks, 90 days](#7-the-skill-tree--6-tracks-90-days)
8. [Exercise types](#8-exercise-types)
9. [The hard problem: grading a free-form prompt](#9-the-hard-problem-grading-a-free-form-prompt)
10. [Gamification economy](#10-gamification-economy)
11. [Flagship modes](#11-flagship-modes)
12. [Data model](#12-data-model)
13. [Content pipeline — how to author 400 lessons without dying](#13-content-pipeline--how-to-author-400-lessons-without-dying)
14. [Technical architecture](#14-technical-architecture)
15. [Unit economics — the make-or-break section](#15-unit-economics--the-make-or-break-section)
16. [Monetization](#16-monetization)
17. [Metrics](#17-metrics)
18. [MVP scope and 12-week build plan](#18-mvp-scope-and-12-week-build-plan)
19. [Go-to-market via Prompt Vidya](#19-go-to-market-via-prompt-vidya)
20. [Risks and kill criteria](#20-risks-and-kill-criteria)
21. [Open decisions](#21-open-decisions)

---

## 1. The name

**Primary recommendation: Riyaz.**

Why it works:

- **It means the thing.** Riyaz is the daily, unglamorous, repeated practice a musician does before
  sunrise. That is exactly the product: not a course you finish, a practice you keep. No other
  ed-tech brand in this space owns "daily practice" as a *word*.
- **It pairs with the channel.** Prompt Vidya = *vidya* (knowledge, the teaching). Riyaz = *practice*.
  "Vidya sikhata hai, Riyaz banata hai." That is a genuinely good brand story and it makes the
  channel→product handoff feel inevitable rather than bolted on.
- **It travels.** Two syllables, phonetic in English, no hard consonant clusters, and it carries a
  hint of discipline even to someone who doesn't know the word. Compare with the alternative of a
  generic English name (PromptGym, AI Dojo) which is forgettable and probably unclaimable.
- **It's not literal about "AI".** Every AI product is named `<something>AI`. In two years that will
  read like naming a company `<something>.com` in 2001. Riyaz survives the category moving from
  "prompting" to "agents" to whatever's next — which matters a lot here, because your curriculum
  will move.

Product naming inside the app follows the metaphor: a lesson is a **riyaz**, a streak is a **sur**
(staying in tune), a lost streak *breaks* your sur, and levels are **taal** stages. Use this lightly
— flavour, not a foreign-language quiz.

**Alternates**, ranked, if Riyaz doesn't survive a trademark/domain check:

| Name | Read | Trade-off |
|---|---|---|
| **Abhyas** | Practice/exercise (Sanskrit) | Same concept, slightly heavier and less musical; more "study" than "craft" |
| **Sur** | In tune | Beautiful and short, but too abstract on its own; works better as a sub-noun |
| **Kata** | Martial-arts form | Instantly legible to developers (coding katas), but crowded and Japanese-borrowed |
| **Manthan** | Churning (of the ocean, for nectar) | Strong story, harder to pronounce for non-Indian users |
| **Prompt Vidya Labs** | Channel extension | Zero brand risk, zero brand asset. Use only if you want the product subordinate to the channel |

**⚠️ Decision needed:** before anything gets printed on a landing page, run a
trademark search (Indian TM class 41/42, plus USPTO if you want a US presence) and check
domain + handle availability across `.ai`, `.com`, `.app`, X, YouTube, Instagram, LinkedIn.
I have not checked availability and you should not assume it.

---

## 2. One-paragraph pitch

Riyaz is a mobile-first daily practice app for the AI era. Every day you get one 10-minute session:
a few fast reps to keep the fundamentals warm, then one real scenario where you write an actual
prompt, debug an actual agent trace, or fix an actual RAG pipeline — and get graded on it in
seconds against a rubric, not a multiple-choice key. You keep a streak, you earn XP, you climb a
league, you fight prompt battles against other learners. In 90 days you go from "I use ChatGPT
sometimes" to "I can specify, build, debug, and evaluate an AI system." The content is authored on
top of the Prompt Vidya curriculum, so the channel is the top of the funnel and the app is the habit.

---

## 3. Why this, why now

**The gap is real and specific.** There is a large and growing population of people who need
practical AI fluency for their job and who are served today by exactly two bad options:

1. **Long video courses.** High intent required, ~5–15% completion rates industry-wide, and they
   teach *recognition* ("I've seen a RAG diagram") not *production* ("I can fix a RAG pipeline that
   is returning garbage").
2. **Just using ChatGPT and hoping.** No feedback loop. You never find out that your prompt was
   mediocre, because the model is agreeable and produces *something*.

Nobody has built the third option: **spaced, gamified, feedback-rich daily reps.** That option is
what took Duolingo from "language app" to a habit product with hundreds of millions of installs, and
what LeetCode did for interview algorithms.

**Why the timing works:**

- Prompting/agent skills are now *job-relevant* to non-engineers (PMs, marketers, analysts,
  support, ops), which is a ~50× larger market than "developers learning LangChain."
- LLM inference is finally cheap enough to grade free-form text at consumer scale — this was
  economically impossible in 2023. (See [§15](#15-unit-economics--the-make-or-break-section);
  it's cheap, not free, and the design has to respect that.)
- The skill surface is unstable (MCP, agents, SDD didn't exist as consumer-teachable concepts two
  years ago), which *favours* a subscription with continuously shipped content over a static course.

**Why this is hard, honestly:** the thing that made Duolingo work is that language has an
objectively gradeable, infinitely generatable exercise surface and a clear "I want to speak Spanish"
motivation. AI skill has neither by default. Both have to be manufactured — the grader
([§9](#9-the-hard-problem-grading-a-free-form-prompt)) and the outcome narrative
([§19](#19-go-to-market-via-prompt-vidya)). Those two are the actual product risk. Everything else
is execution.

---

## 4. Who it's for

Four personas, in priority order for v1.

### P1 — "Priya, the ambitious PM" *(primary — build for her)*
28, product manager at a mid-size SaaS company. Uses ChatGPT daily, feels she's using 10% of it.
Her company just announced an "AI-first" mandate and she is quietly worried. Doesn't code, won't
install Python, will absolutely not watch a 6-hour video. Has 10 minutes on the metro.
**Wants:** to walk into a meeting and be the person who actually knows how this works.
**Will pay for:** a credible, visible signal of progress and a habit she doesn't have to maintain
with willpower.

### P2 — "Rahul, the CS student"
21, final year, everyone in his batch says "AI" in interviews and nobody can explain retrieval.
Broke, competitive, on his phone constantly.
**Wants:** placement edge, leaderboard bragging rights.
**Will pay for:** almost nothing — but he is your growth engine. Prompt battles and leagues exist
largely for him. Monetize him via referral loops, not rupees.

### P3 — "Anita, the working engineer"
32, backend dev, needs to ship an agent at work next quarter, has real gaps in RAG evaluation and
MCP. Impatient with basics.
**Wants:** to skip to the hard tracks, get real debugging reps, not be condescended to.
**Will pay for:** yes, readily, if the advanced content is genuinely non-trivial. This is the
persona most likely to churn out if the content is shallow.

### P4 — "Vikram, the L&D buyer"
41, head of learning at a 2,000-person company, has budget and a mandate to "upskill everyone on
AI," currently buying a generic LMS course nobody finishes.
**Wants:** completion dashboards, seat management, a certificate.
**Will pay for:** a lot, per seat. **But do not build for him in year one** — B2B requirements
(SSO, admin panels, procurement, custom content) will consume the whole roadmap and kill the
consumer product. Note him, defer him.

---

## 5. Competitive positioning

| Product | What it does well | The gap Riyaz fills |
|---|---|---|
| **Duolingo** | The habit mechanics, perfected | Different subject; nothing to copy but the *shape* |
| **DeepLearning.AI / Coursera** | Depth, credibility, instructor brand | Passive, long-form, low completion, no reps |
| **LeetCode / HackerRank** | Deterministic grading, competitive pressure | Only serves developers; no free-form judgment |
| **Brilliant** | Beautiful interactive lessons, daily habit | Math/science; interactivity is scripted, not open-ended |
| **Exercism** | Human mentorship on submitted work | Doesn't scale; slow feedback (hours/days, not seconds) |
| **Prompt-engineering courses (Udemy etc.)** | Cheap, plentiful | Static, stale within 6 months, no practice loop |
| **ChatGPT itself as a tutor** | Free, infinitely patient | **The real competitor.** No curriculum, no streak, no assessment, no proof of progress |

**The defensible wedge is not content.** Content gets copied and models can generate it. The wedge is:

1. **The grading rubric library.** A tuned, evaluated, adversarially-tested set of rubrics per
   exercise is genuinely hard to reproduce and gets better with every learner submission you grade.
   This is the moat. Treat it as the crown jewel asset, not as "prompts in a folder."
2. **The habit + social graph.** Streaks, leagues, and battles are switching costs.
3. **Prompt Vidya distribution.** A warm audience that already trusts the teaching voice.

**Explicitly not competing on:** being the deepest AI course. You will lose that to DeepLearning.AI
and you don't need to win it.

---

## 6. The core loop — anatomy of a 10-minute lesson

The single most important design constraint: **the session must be finishable in 10 minutes on a
phone, one-handed, with interruptions.** Everything else negotiates around that.

```
  ┌─────────────────────────────────────────────────────────────────┐
  │  OPEN  →  WARM UP  →  THE REP  →  THE TWIST  →  CLOSE            │
  │  0:00     0:15         3:00        7:00         9:00      10:00  │
  └─────────────────────────────────────────────────────────────────┘
```

| Beat | Time | What happens | Why it's there |
|---|---|---|---|
| **Open** | 0:00–0:15 | Streak flame, today's skill, one-line "why this matters today" | Reward before effort. Never make the first screen a question. |
| **Warm up** | 0:15–3:00 | 3–4 fast **deterministic** reps: spot-the-bug, order-the-steps, pick-the-better-prompt, fill-the-gap. Instant right/wrong, no LLM call. | Builds momentum, costs nothing, gives spaced repetition a surface to work on. |
| **The rep** | 3:00–7:00 | **One** open-ended task. Write the prompt. Fix the agent. Design the retrieval. Graded by rubric in <8 seconds. | This is the product. Everything else is scaffolding around this moment. |
| **The twist** | 7:00–9:00 | The scenario changes under you. "The model now returns JSON with a trailing comma." "Your context window just halved." Adapt your answer. | Transfer, not memorization. Also the most shareable moment. |
| **Close** | 9:00–10:00 | XP tally, streak advanced, one-sentence "what you learned," tomorrow's teaser, optional share card | Closes the loop, sets the return hook. |

**Hard rules for the loop:**

- **One open-ended rep per lesson.** Not three. Two free-form gradings in a session doubles cost and
  halves completion. The warm-ups carry the volume.
- **Feedback in under 8 seconds, or fake it well.** Stream the grader's output token-by-token so
  perceived latency is ~1.5s. Never show a blank spinner on the rep.
- **Never fail a learner silently.** Every rubric miss must name the specific thing and show a
  worked better answer. "Score: 6/10" with no diagnosis is the #1 way to kill retention.
- **The session ends on a win.** If a learner bombs the rep, the close screen leads with what they
  got right and books the concept for tomorrow's warm-up. Duolingo's cruelty is a bug, not a feature.

---

## 7. The skill tree — 6 tracks, 90 days

Six tracks. Each track is 12–20 lessons. A learner does one lesson per day and finishes the core
path in roughly 90 days, which is the length you should market ("90 days to AI fluency") because it
is a horizon people can hold in their head.

```
                        ┌──────────────────┐
                        │  T1  FOUNDATIONS │  (12 lessons — required)
                        └────────┬─────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
   ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
   │ T2  PROMPTCRAFT │  │  T3  AGENTS     │  │  T4  GROUNDING  │
   │   (18 lessons)  │  │  (20 lessons)   │  │  (RAG, 16)      │
   └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                  ┌──────────────┴──────────────┐
                  │                             │
         ┌────────▼────────┐          ┌─────────▼────────┐
         │ T5  CONNECTORS  │          │  T6  SPEC-DRIVEN │
         │  (MCP/tools,14) │          │  (SDD, 14)       │
         └─────────────────┘          └──────────────────┘
```

### T1 — Foundations (12 lessons, required, no prerequisites)
What a token is and why it costs money. Context windows as a physical constraint. Why the model
agrees with you. Temperature and determinism. Hallucination as a *predictable failure shape*, not a
mystery. Reading an API response. What "the model can't do X" actually means.
**Exit criterion:** learner can predict *why* a given output went wrong before being told.

### T2 — Promptcraft (18 lessons)
Role and task separation. Constraint stacking. Output contracts (schemas, formats). Few-shot design
and when it backfires. Decomposition. Self-critique loops. Adversarial prompting and prompt
injection defence. Prompt versioning and regression.
**Exit criterion:** given a fuzzy business ask, learner writes a prompt that passes a hidden rubric
on first try 70% of the time.

### T3 — Agents (20 lessons)
Tools as an interface, not magic. The agent loop (perceive → decide → act → observe). Reading a
trace. The five canonical agent failures: infinite loop, tool-arg hallucination, premature stop,
context poisoning, silent no-op. Multi-agent handoff. Cost/latency budgets. Human-in-the-loop gates.
**Exit criterion:** learner can look at a broken 30-step trace and name the failure in under 60s.

### T4 — Grounding / RAG (16 lessons)
Why retrieval exists. Chunking as a lossy decision. Embeddings intuition without linear algebra.
Hybrid search. Reranking. The evaluation problem (recall vs. precision vs. faithfulness). Citation
integrity. When RAG is the wrong answer.
**Exit criterion:** learner can diagnose a RAG system returning confident wrong answers and
correctly attribute it to chunking / retrieval / synthesis.

### T5 — Connectors (MCP & tool integration, 14 lessons)
What a connector protocol is for. Tool schema design. Auth and secrets boundaries. Idempotency and
retries. Rate limits and backoff. Permission models and confirmation gates. The blast-radius
question: what's the worst thing this tool can do?
**Exit criterion:** learner designs a safe tool schema for a destructive operation.

### T6 — Spec-driven development (14 lessons)
Writing a spec an agent can execute. Acceptance criteria that are actually checkable. Decomposition
into verifiable units. Review loops. Knowing when the spec, not the model, is the bug.
**Exit criterion:** learner turns a two-line feature request into a spec that a coding agent
completes correctly without follow-up.

**Beyond day 90:** daily "Riyaz Continues" — freshly generated scenario reps drawn from the same
skill graph plus a weekly "what shipped this week in AI" applied lesson. This is what a subscription
is actually paying for, and it's why the curriculum being a *graph* (with skill-level mastery
scores) rather than a *list* matters.

---

## 8. Exercise types

Twelve types. The column that matters most is **Grading** — anything marked `deterministic` costs
₹0 to run and can be served infinitely to free users.

| # | Type | What the learner does | Grading | Tracks |
|---|---|---|---|---|
| 1 | **Spot the flaw** | Pick which of 4 prompts/traces/configs is broken | deterministic | all |
| 2 | **Order the steps** | Drag agent-loop / RAG-pipeline steps into order | deterministic | T3, T4 |
| 3 | **Fill the contract** | Complete a JSON schema / tool definition from a spec | deterministic (schema validate) | T2, T5, T6 |
| 4 | **Predict the output** | Given prompt + config, choose what the model returns | deterministic | T1, T2 |
| 5 | **Budget call** | Given a task, choose model/context/effort under a cost or latency cap | deterministic (rule check) | T1, T3 |
| 6 | **Write the prompt** ⭐ | Free-form: write a prompt satisfying a hidden rubric | **rubric grader** | T2 |
| 7 | **Debug the agent** ⭐ | Read a real trace, identify failure, propose a fix | hybrid (MCQ diagnosis + free-form fix) | T3 |
| 8 | **Fix the retrieval** ⭐ | Given a failing RAG case, adjust chunking/query/rerank | hybrid (config diff + free-form rationale) | T4 |
| 9 | **Design the tool** ⭐ | Write an MCP-style tool schema for a scenario | hybrid (schema validate + rubric on safety) | T5 |
| 10 | **Write the spec** ⭐ | Turn a vague ask into executable acceptance criteria | **rubric grader** | T6 |
| 11 | **The twist** | Adapt a just-submitted answer to a changed constraint | rubric grader (delta only) | all |
| 12 | **Prompt battle** | Head-to-head, same brief, better output wins | rubric grader + pairwise judge | T2, T6 |

⭐ = the reps that actually teach. Every lesson has exactly one.

**Design note on hybrid grading:** types 7, 8, and 9 deliberately split into a cheap deterministic
half (which failure is it? which config value changed?) and an expensive free-form half (why? fix
it). The deterministic half alone is a valid, satisfying, zero-cost exercise for free users. This
is not a compromise — it's the main lever that makes the free tier viable
([§15](#15-unit-economics--the-make-or-break-section)).

---

## 9. The hard problem: grading a free-form prompt

**This section is the product.** If the grader is bad, nothing else matters: learners will feel
judged arbitrarily, lose trust in the score, and churn. If it's good, everything else is
straightforward engineering.

### The three failure modes to design against

1. **Agreeableness.** An LLM asked "is this a good prompt?" says yes to almost anything.
   Mitigation: never ask for a holistic judgment. Ask for **independent binary checks against
   named criteria**, then compute the score in code from the checks.
2. **Score drift.** The same submission graded twice gets 6/10 and 8/10.
   Mitigation: binary criteria (not 1–10 sliders), low effort setting, and a golden-set regression
   suite run on every rubric change.
3. **Gaming.** Learner discovers that stuffing keywords passes.
   Mitigation: adversarial criteria in the rubric ("does the answer contain unjustified boilerplate?"
   is a *negative* criterion), plus periodic manual review of top scorers.

### The grading architecture

```
   learner submission
          │
          ▼
   ┌──────────────────┐   fail
   │ 1. GUARDS        ├────────►  instant reject, no LLM cost
   │  length, empty,  │           ("that's 4 words — try again")
   │  language, PII,  │
   │  injection scan  │
   └────────┬─────────┘
            │ pass
            ▼
   ┌──────────────────┐   fail
   │ 2. HARD CHECKS   ├────────►  instant specific feedback
   │  regex/schema/   │           ("your JSON is missing `required`")
   │  AST/JSON parse  │
   └────────┬─────────┘
            │ pass
            ▼
   ┌──────────────────────────────────────────────────┐
   │ 3. RUBRIC JUDGE  (the only LLM call)              │
   │                                                   │
   │  system: GRADING CONSTITUTION  ~5k tok  [CACHED]  │
   │  ────────────────────────────────────────────     │
   │  user:   lesson rubric (6–10 binary criteria)     │
   │          reference answer                         │
   │          learner submission                       │
   │                                                   │
   │  → structured output: {criteria:[{id,met,evidence}]│
   │                        , strongest, weakest }     │
   └────────┬─────────────────────────────────────────┘
            │
            ▼
   ┌──────────────────┐
   │ 4. SCORE IN CODE │   score = Σ weight(criterion) where met
   │  + FEEDBACK GEN  │   feedback = template(weakest criterion)
   └──────────────────┘
```

**Key design decisions in that diagram:**

- **The judge never emits a number.** It emits per-criterion booleans plus a one-line evidence quote
  from the submission. The score is arithmetic in your code. This kills drift and makes the score
  explainable ("you missed criterion 4: no output format specified").
- **`evidence` is mandatory and must be a verbatim quote.** If the judge can't quote the submission
  to justify `met: true`, you post-validate and flip it to false. Cheapest hallucination guard there is.
- **The grading constitution is one shared ~5k-token system prompt** across every lesson, holding
  the general grading philosophy, the evidence rule, the anti-agreeableness instructions, and the
  output contract. Per-lesson rubrics go *after* the cache breakpoint. This is not a stylistic
  choice — see the caching note below.
- **Structured outputs, always.** Use `output_config.format` with a JSON schema so the judge
  physically cannot return prose. No parsing, no retry-on-malformed.
- **Low effort, small output.** Grading is a classification task, not a reasoning marathon. Run it
  at `effort: "low"`, cap `max_tokens` around 600.

### ⚠️ The prompt-caching gotcha that determines your cost model

Prompt caching has a **minimum cacheable prefix**, and it is *not* the same across models:

| Model | Min cacheable prefix |
|---|---:|
| Claude Opus 5 | 512 tokens |
| Claude Sonnet 5 | 1,024 tokens |
| Claude Haiku 4.5 | **4,096 tokens** |

If you write a lean 1,500-token grading system prompt and run it on Haiku 4.5 — the obvious
cost-optimal choice — **it silently will not cache.** No error, no warning, just
`cache_creation_input_tokens: 0` and a 3× higher bill than your spreadsheet said.

So: the grading constitution is *deliberately* written to ~5,000 tokens. Not padding — that's real
budget for worked examples of good and bad grading, the evidence rule, and the anti-gaming
criteria — but it is sized with the 4,096 floor in mind, because the constitution is identical
across every grade you ever run and therefore caches at ~0.1× read cost across your entire user base.

Cache reads cost roughly 0.1× base input; cache writes cost 1.25× (5-minute TTL). With continuous
traffic the entry stays warm and every grade after the first pays read price. At any real scale this
is the difference between a viable and a non-viable free tier.

### Model routing

| Grading job | Model | Why |
|---|---|---|
| Warm-up exercises (types 1–5) | **none** | Deterministic. Zero cost. |
| Standard rubric grade (types 6–11) | **Claude Haiku 4.5** | Binary criteria checking is well within Haiku's range at $1/$5 per MTok |
| Hard rubric grade (T5/T6, safety-critical, ambiguous) | **Claude Sonnet 5** | Nuance on safety and spec-quality criteria; $3/$15 per MTok |
| Prompt battle pairwise judge | **Claude Sonnet 5** | Head-to-head comparison is genuinely harder than criterion checking; a wrong call here is publicly visible |
| Nightly content generation, weekly report cards, battle post-mortems | **Batch API** (50% off) | Not latency-sensitive |

**Route by rubric difficulty, not by user tier.** Giving paid users a "better grader" means free and
paid users get different scores for the same answer, which is indefensible the moment someone
notices. Tier on *volume and features*, never on grading quality.

### Building the rubric library

1. **Author the rubric before the lesson.** If you can't write 8 binary criteria for the exercise,
   the exercise isn't well-specified and won't be gradeable. This constraint is a feature — it will
   kill your worst lesson ideas early.
2. **Build a golden set per rubric**: ~20 submissions spanning excellent → terrible, hand-labelled
   by you. This is boring and it is the highest-leverage work in the project.
3. **Regression-gate every rubric change** against its golden set. Target ≥90% agreement with human
   labels and ≥95% self-consistency across two runs of the same submission.
4. **Mine real submissions.** Every week, sample submissions where the grader was least confident
   or where learners hit "this grade seems wrong," label them, add to the golden set. This is the
   flywheel — the rubric library is the asset that compounds and it compounds only if you feed it.

---

## 10. Gamification economy

### What transfers from Duolingo, and what doesn't

**Transfers:**
- Streaks. The single strongest retention mechanic ever built in consumer ed-tech.
- Leagues. Weekly, relative, resettable competition — motivating without being permanent.
- Short sessions with a fixed, visible end.
- The "one more lesson" close screen.

**Does NOT transfer — do not copy these:**
- **Hearts / lives.** Language learners make dozens of small errors per session and hearts create
  urgency. AI-skill learners make *one* substantial attempt per session; taking a life for a
  mediocre prompt is punishing exactly the exploratory behaviour you want to encourage. **No hearts.**
- **Aggressive push guilt** ("the owl is disappointed"). Your users are professionals. That tone
  reads as juvenile and will get the app deleted, not opened.
- **Infinite generated drilling.** Duolingo can generate 10,000 valid Spanish sentences. You
  cannot generate 10,000 valid agent-debugging scenarios that are *actually different*. Respect the
  content ceiling; don't design mechanics that assume infinite supply.

### XP

```
XP  =  BASE(exercise_type)
     × QUALITY(score)
     × FIRST_TRY(1.25 if no retry, else 1.0)
     + STREAK_BONUS(min(streak_days, 30) × 0.5)
```

| Exercise type | BASE |
|---|---:|
| Warm-up (types 1–5) | 5 |
| The rep (types 6–10) | 30 |
| The twist (type 11) | 20 |
| Prompt battle | 40 (win) / 15 (loss) |

`QUALITY(score)` = `0.5` below 60%, `1.0` at 60–84%, `1.3` at 85%+. Note that **a bad attempt still
earns XP.** Showing up is the behaviour you're reinforcing; quality is the multiplier, not the gate.

A typical good session ≈ 20 (warm-ups) + 39 (rep at 85%+, first try) + 20 (twist) + streak bonus
≈ **85–95 XP**. Round numbers by design — learners should be able to predict roughly what a session
is worth.

### Streaks

- **Advances on one completed session per day.** Not on XP thresholds.
- **Streak Freeze:** auto-consumed, earn one every 7 days, hold max 2. Free for everyone. This is
  not a monetization lever — a broken streak is a churn event and you should be actively preventing
  churn, not selling insurance against it.
- **Weekend Amnesty:** ⚠️ **Decision needed.** Duolingo-style unbroken daily streaks punish people
  with families and jobs (i.e. your paying persona). Strong recommendation: streaks require **5 days
  out of any rolling 7**, displayed as an unbroken flame. Slightly less addictive, dramatically less
  churn-on-guilt, and it fits how adults actually live. Test both.
- **Streak repair:** one per month, costs a completed "make-up" session (do two lessons in a day),
  never money.

### Leagues

Weekly. Groups of 30, matched on the previous week's XP. Top 7 promote, bottom 7 demote. Six tiers,
named on the taal metaphor (Vilambit → Madhya → Drut → …). Reset every Monday 00:00 in the user's
local timezone.

**Rate-limit the XP that counts toward league standing** (e.g. first 150 XP per day) so leagues
reward consistency rather than one Saturday binge. Otherwise the top of every league is people with
a free afternoon, not people building a habit.

### Badges

Keep them few and meaningful. Twelve, not eighty.
Examples: *Trace Reader* (debug 25 agent traces), *Rubric Slayer* (10 perfect scores),
*Undefeated* (5 battle wins in a row), *Ninety* (complete the 90-day path),
*Nightingale* (30 sessions before 7am), *Sur* (100-day streak).

### Leaderboards

Three scopes, in priority order: **your league** (30 people, weekly — the one that matters),
**your friends** (invited, all-time), **global** (top 100, weekly — motivational for P2, irrelevant
to P1). Do not put a global all-time leaderboard in the app; it is permanently demoralizing to new
users.

---

## 11. Flagship modes

These are the five things that make Riyaz *not* a quiz app. Each gets a named section because each
needs distinct engineering.

### 11.1 Scenario reps
The default "rep." A short, concrete, workplace-real brief. Not "write a prompt about summarizing."
Instead: *"Your support team gets 400 tickets/day. Write the prompt that routes each ticket to one
of six teams and flags the angry ones. The tickets are in Hinglish. You get one shot per ticket —
no retries, no human review."*
Every constraint in that brief maps to a rubric criterion. Scenario quality is the difference
between a toy and a product.

### 11.2 Agent debugging
A rendered agent trace — 15 to 40 steps, real-looking tool calls, real-looking outputs, one seeded
failure. Learner scrubs the trace, taps the step where it went wrong, classifies the failure from a
fixed taxonomy (the cheap deterministic half), then writes the fix (the graded half).

Build a **trace fixture library** of ~60 hand-built traces covering the five canonical failures ×
several domains, each parameterizable (swap the domain, the tool names, the specific values) so one
fixture yields ~10 distinct-feeling exercises. Rendering the trace nicely on mobile is a real design
problem — budget for it.

### 11.3 Prompt battles
Two learners, same brief, 3-minute timer, both submissions run against the same rubric plus a
**pairwise judge** that picks a winner on the criteria they tied on.

Engineering notes:
- **Asynchronous by default.** Real-time matchmaking at low DAU means empty queues. Match against a
  submission from the last 24h — the opponent gets a notification with the result. Show "live" only
  once concurrency supports it.
- **Ghost opponents** for cold start: pre-graded submissions from the golden set, clearly labelled
  as practice (never fake a human opponent — if that's ever discovered, trust is gone).
- **Anti-abuse:** rate-limit, detect copy-paste of the reference answer, and make submissions
  reviewable by the loser ("see the winning answer") — which doubles as a teaching moment and is
  the reason battles are educational rather than just competitive.

### 11.4 RAG missions
Multi-step (3–4 lessons chained across days). A fictional corpus, a set of test queries, and a
retrieval config the learner tunes: chunk size, overlap, query rewriting, reranking on/off.

**Run this for real.** A small local embedding index over a fixed 200-document corpus, evaluated
against a fixed query set with precomputed ground truth. The learner changes a config, you rerun
retrieval (milliseconds, no LLM), and show the recall/precision delta immediately. The free-form
part is only the *rationale* ("why did increasing overlap help here?"). This makes RAG viscerally
learnable and costs almost nothing to grade.

### 11.5 Connector labs (MCP)
A sandboxed mock server exposing a handful of fake tools (a calendar, a CRM, a file store, a
payments API). The learner writes a tool schema or a permission policy; you execute their schema
against scripted scenarios including adversarial ones ("the model tries to call `delete_all` — does
your policy stop it?"). Pass/fail is deterministic from the scenario outcomes; the rubric grade
covers the design rationale and the blast-radius reasoning.

### 11.6 SDD quests
Longest form: a week-long arc. Day 1 a vague feature request, day 2 acceptance criteria, day 3
decomposition, day 4 the spec, day 5 the spec goes to a real coding agent and the learner sees what
actually got built. The gap between what they specified and what they got *is* the lesson — and it's
the single most memorable moment in the whole curriculum. Cost note: day 5 is a real agent run;
gate it to paid, run it on the Batch API overnight, deliver as a morning notification.

---

## 12. Data model

Core entities. (Illustrative field lists, not a migration.)

```
User            id, handle, email, tz, locale, created_at, tier, cohort
Profile         user_id, display_name, avatar, headline, public_visibility

Skill           id, track, name, description, prerequisites[]
Lesson          id, skill_id, day_index, title, brief, est_seconds, status
Exercise        id, lesson_id, ordinal, type, payload(jsonb), rubric_id?
Rubric          id, version, criteria[], weights[], reference_answer, golden_set_id

Attempt         id, user_id, exercise_id, submission, started_at, submitted_at,
                latency_ms, grader_model, grader_version
Grade           attempt_id, criteria_results[], score, xp_awarded,
                feedback_md, confidence, cost_micro_usd
Mastery         user_id, skill_id, score(0-1), last_seen_at, next_due_at, decay_rate

Streak          user_id, current, longest, freezes_held, last_active_date, repairs_used
XPLedger        id, user_id, source_type, source_id, amount, occurred_at   -- append-only
LeagueMember    league_id, user_id, week, xp_counted, rank_final
Badge / UserBadge

Battle          id, brief_id, rubric_id, state, created_at
BattleEntry     battle_id, user_id, submission, grade_id, is_ghost
BattleVerdict   battle_id, winner_user_id, judge_model, rationale

Mission         id, kind(rag|mcp|sdd), config_schema, corpus_id, eval_set_id
MissionRun      id, user_id, mission_id, config(jsonb), metrics(jsonb), created_at
```

**Three modelling decisions worth flagging:**

1. **XPLedger is append-only.** Never mutate a balance. You will need to recompute leagues, correct
   grading bugs, and answer "why did my XP change" — all trivially possible with a ledger and
   miserable without one.
2. **`Rubric` is versioned and `Grade` records `grader_version`.** When you improve a rubric, old
   grades must remain explainable. Also lets you A/B rubric changes.
3. **`Mastery` with `decay_rate` and `next_due_at`** is what turns the app from a linear course into
   a practice system. Warm-up exercises are drawn from skills whose mastery has decayed past
   threshold — that's your spaced-repetition engine, and it's what keeps day 200 interesting.
   Half-life-based decay (FSRS-style) rather than fixed Leitner boxes.

---

## 13. Content pipeline — how to author 400 lessons without dying

400+ lessons is the single biggest non-obvious cost in this project. Plan it like an assembly line.

### Roles
- **Curriculum owner (you).** Owns the skill graph, exit criteria, and the voice. Non-delegable.
- **Scenario writer.** Turns a skill + exit criterion into a concrete workplace brief.
- **Rubric author.** Writes 8 binary criteria + reference answer + 20-item golden set.
- **Reviewer.** Runs the rubric against the golden set, signs off.

One person can wear several hats; the *stages* still have to exist separately.

### Pipeline

```
skill spec → scenario draft → rubric draft → golden set → regression run → review → ship
                    │              │              │             │
              (LLM-assisted) (LLM-assisted)  (human-labelled) (automated gate)
```

**What to LLM-assist:** first drafts of scenarios, distractor options for MCQs, trace fixture
variations, paraphrases of briefs.
**What to never LLM-assist:** the rubric criteria, the golden-set labels, the exit criteria.
Those are the asset. Generating them with a model means grading a model's opinion with a model's
opinion, and the whole thing becomes circular and un-debuggable.

### Content as code
Lessons live in this repo as JSON validated against
[`schema/lesson.schema.json`](schema/lesson.schema.json), reviewed in PRs, tested in CI (schema
validation + rubric regression against golden sets), shipped by merge. Content bugs are then
bisectable and rollback-able like any other bug — which you will need on day 3 of production.

### Throughput target
A trained pair should ship **8–12 lessons/week** at quality. That's ~40 weeks for the full 400 —
which is why the MVP ships **T1 + T2 only (30 lessons)** and the rest lands progressively. See
[§18](#18-mvp-scope-and-12-week-build-plan).

---

## 14. Technical architecture

Deliberately boring. Novelty budget goes entirely into the grader and the content, not the stack.

```
   ┌──────────────────────────────────────────────────────────┐
   │  CLIENTS   React Native (iOS/Android)  ·  Next.js (web)   │
   └───────────────────────────┬──────────────────────────────┘
                               │ REST + SSE (streamed grading)
   ┌───────────────────────────▼──────────────────────────────┐
   │  API              FastAPI (Python)                        │
   │  ┌──────────┬───────────┬────────────┬────────────────┐  │
   │  │ Lessons  │ Attempts  │ Progression│ Social         │  │
   │  │ & content│ & grading │ XP/streak/ │ battles/leagues│  │
   │  │          │           │ mastery    │ /leaderboards  │  │
   │  └──────────┴─────┬─────┴────────────┴────────────────┘  │
   └───────────────────┼──────────────────────────────────────┘
                       │
        ┌──────────────┼───────────────┬─────────────────┐
        ▼              ▼               ▼                 ▼
   ┌─────────┐   ┌───────────┐   ┌──────────┐    ┌──────────────┐
   │ Postgres│   │  Redis    │   │ Grading  │    │ Batch worker │
   │ +pgvector│  │ cache/    │   │ service  │    │ (nightly:    │
   │         │   │ rate-limit│   │ (Claude) │    │  reports,    │
   └─────────┘   └───────────┘   └──────────┘    │  SDD runs)   │
                                                  └──────────────┘
```

**Choices and why:**

| Layer | Choice | Rationale |
|---|---|---|
| Mobile | React Native (Expo) | One team, two platforms; nothing here needs native performance |
| Web | Next.js | SEO landing pages + web player from the same codebase |
| API | **FastAPI / Python** | Same language as the grading logic and the eval harness; matches this repo's ecosystem |
| DB | Postgres + pgvector | Relational for everything; pgvector serves RAG-mission corpora without a second datastore |
| Cache/queue | Redis | Sessions, rate limits, league standings, battle matchmaking |
| LLM | Anthropic SDK (`anthropic`) | Structured outputs + prompt caching + Batch API are all first-class |
| Analytics | PostHog (self-hosted or cloud) | Funnels + feature flags + session replay in one, and you own the data |
| Payments | Razorpay (India) + Stripe (rest) | UPI is non-negotiable for the Indian market |
| Push | FCM / APNs via Expo | |

**The grading service is a separate module with a hard interface** (`grade(submission, rubric) →
GradeResult`) even if it starts in-process. You will swap models, add a self-hosted classifier for
cheap pre-filtering, and run offline evals against it. Keep that seam clean from day one.

**Eval harness is not optional infrastructure.** `pytest`-driven, runs every rubric against its
golden set, reports agreement + self-consistency, blocks merge below threshold. Build it in week 2,
before you have 300 rubrics and no way to know if a change broke 40 of them.

---

## 15. Unit economics — the make-or-break section

Every number below is a **stated assumption**, not a measurement. The purpose is to find the shape
of the business, not to predict it. Model prices are Anthropic first-party API rates as of
2026-07-27; Sonnet 5 has introductory pricing ($2/$10) through 2026-08-31, after which it is $3/$15
— the calculations below use **standard** rates so nothing breaks on 1 September.

### Cost per graded rep

Assumptions: grading constitution 5,000 tokens (cached), per-lesson rubric + reference + submission
1,100 tokens (fresh), judge output 400 tokens.

Effective input with a warm cache = `5,000 × 0.1 + 1,100 = 1,600` tokens.

| Model | Input $/MTok | Output $/MTok | Input cost | Output cost | **Per grade** |
|---|---:|---:|---:|---:|---:|
| Haiku 4.5 | 1.00 | 5.00 | $0.0016 | $0.0020 | **$0.0036** |
| Haiku 4.5, *cache missed* | 1.00 | 5.00 | $0.0061 | $0.0020 | $0.0081 |
| Sonnet 5 | 3.00 | 15.00 | $0.0048 | $0.0060 | **$0.0108** |

Note the middle row: **getting the cache wrong costs you 2.25×.** That is the entire reason
[§9](#9-the-hard-problem-grading-a-free-form-prompt) obsesses over the 4,096-token floor.

### Cost per active user per month

Assume a mix of 80% Haiku / 20% Sonnet → blended **$0.0050** per graded rep.

| Tier | Graded reps/day | Days/mo active | LLM cost/user/mo |
|---|---:|---:|---:|
| Free (1 graded rep/day cap; warm-ups free) | 1 | 20 | **$0.10** |
| Paid (rep + twist + 1 battle) | 3 | 26 | **$0.39** |

Warm-up exercises (types 1–5) are deterministic and cost **$0.00** regardless of volume. This is
why the free tier is mostly warm-ups. It is not stinginess — it's what makes a free tier possible
at all.

### The scenario that decides the business

10,000 DAU, 30 days:

| Line | Value |
|---|---:|
| Free users (96%) — 9,600 × $0.10 | −$960 |
| Paid users (4%) — 400 × $0.39 | −$156 |
| **LLM cost** | **−$1,116** |
| Infra (Postgres, Redis, hosting, push, analytics) | −$600 |
| **Total variable cost** | **−$1,716** |
| Revenue: 400 paid × ₹399 (~$4.70) | **+$1,880** |
| **Contribution margin** | **+$164 (9%)** |

**That is far too thin, and it is the central finding of this blueprint.** Three observations:

1. **A 4% conversion rate does not work.** At 7% conversion the same model yields ~$1,500/mo
   contribution (44% margin). Conversion, not cost, is the lever that matters most. Everything in
   [§16](#16-monetization) is designed around getting from 4% to 7%+.
2. **An uncapped free tier with LLM grading is fatal.** If free users got 3 graded reps/day instead
   of 1, LLM cost triples to ~$3,000/mo and the business is underwater at any plausible conversion.
   The 1-graded-rep-per-day free cap is a load-bearing product decision, not a growth tax.
3. **Price is probably too low.** ₹399/mo is anchored to Indian consumer app pricing, but the
   persona (P1: a PM whose company has an AI mandate) is not price-sensitive at ₹599–799. Test it.
   A ₹699 price point at 5% conversion produces ~$2,300/mo contribution at the same cost base.

### Cost controls to build in from day one

- **Per-user daily grading budget**, enforced in code, with a friendly ceiling message. Not a rate
  limiter bolted on later.
- **Cache-hit monitoring as a first-class alert.** Track `cache_read_input_tokens` on every call; if
  the hit rate drops below ~90%, page someone. A stray timestamp in the constitution can silently
  triple your bill overnight.
- **Batch API for everything non-interactive** — weekly report cards, battle post-mortems, SDD
  agent runs, nightly content generation. 50% discount, results within an hour.
- **Track `cost_micro_usd` per grade** in the `Grade` row. You cannot manage what you don't
  attribute per-lesson; some rubrics will turn out to be 5× more expensive than others.
- **Deterministic-first review.** Every quarter, audit which rubric-graded exercises could be
  converted to hybrid or deterministic without losing pedagogical value. This number should go up
  over time.

---

## 16. Monetization

**Free forever:**
All warm-up exercises, unlimited. 1 rubric-graded rep per day. Streaks, XP, leagues, leaderboards.
Track 1 (Foundations) complete. Practice battles vs ghosts.

**Riyaz Pro — ₹399/mo or ₹2,999/yr** *(⚠️ price to be tested; see §15)*
Unlimited graded reps. All six tracks. The twist on every lesson. Live prompt battles. RAG missions
and connector labs. SDD quests. Weekly personalised report card (Batch API — cheap). Full mistake
history and re-practice. Streak repair without a make-up session.

**Riyaz Teams — ₹299/seat/mo, 10-seat minimum** *(defer to year 2)*
Everything in Pro plus a cohort dashboard, assigned tracks, and completion export. Do not build the
admin panel until you have inbound demand you're turning away.

**Deliberately not monetized:**
- **Streak freezes.** Selling anxiety relief to the persona you want to retain is short-term revenue
  and long-term churn.
- **Better grading.** See [§9](#9-the-hard-problem-grading-a-free-form-prompt).
- **Ad-supported free tier.** Ads on a 10-minute focus session destroy the exact thing the product
  is selling.

**Conversion strategy — where the 4% → 7% comes from:**
1. **Convert on the cap, not on a paywall.** The moment a free learner finishes their one graded rep
   and wants another *right now* is the highest-intent moment in the product. That's the upgrade
   prompt. Nothing else converts as well as "you're on a roll and you want to keep going."
2. **Convert on day 7, not day 1.** Habit first. Nobody pays for a product they haven't proven they'll
   use. Free trial of Pro from day 7–14, no card up front.
3. **Convert on the report card.** A weekly "here's what you learned and here's your gap" is a
   genuinely valuable artifact and a natural place for "Pro shows you the full picture."
4. **Annual by default at checkout.** ₹2,999/yr = ₹250/mo effective; the discount pays for itself in
   reduced churn processing.

---

## 17. Metrics

**North star: Weekly Practicing Learners (WPL)** — users who complete ≥3 sessions in a rolling 7
days. Not DAU (rewards notification spam), not lessons completed (rewards making lessons shorter),
not XP (inflatable). WPL captures habit, which is the actual product.

| Layer | Metric | Target (6 mo post-launch) |
|---|---|---:|
| Acquisition | Install → first session complete | ≥60% |
| Activation | D1 return | ≥45% |
| | **D7 return** *(the number that predicts everything)* | ≥25% |
| | D30 return | ≥15% |
| Habit | WPL / MAU | ≥35% |
| | Median streak length | ≥9 days |
| Learning | Rep completion rate (started → submitted) | ≥80% |
| | Mean first-try rubric score, by week-in-app | trending up |
| | Skill mastery retention at 30 days | ≥70% |
| Quality | Grader–human agreement on golden sets | ≥90% |
| | Grader self-consistency | ≥95% |
| | "This grade seems wrong" reports / 1,000 grades | ≤5 |
| Business | Free → Pro conversion | ≥7% |
| | Pro monthly churn | ≤6% |
| | LLM cost per WPL | ≤$0.35 |
| | Contribution margin | ≥40% |

**The two leading indicators to watch weekly from day one:** D7 return and grader–human agreement.
If D7 is below 20%, the loop isn't working and no amount of content will fix it. If agreement is
below 85%, learners are being graded arbitrarily and D7 will follow it down within a month.

---

## 18. MVP scope and 12-week build plan

**MVP thesis:** prove that (a) people come back on day 7 and (b) the grader is trusted. Nothing else.
Everything cut below is cut because it does not test one of those two things.

### In scope for v0

- Web + iOS (Android in week 11 — RN makes it cheap, but pick one store to debug first)
- **T1 Foundations (12 lessons) + T2 Promptcraft (18 lessons)** = 30 lessons ≈ 30 days of content
- Exercise types 1, 2, 3, 4, 6, 11 (the deterministic core + write-the-prompt + the twist)
- The full grading pipeline with rubric library + golden sets + eval harness
- Streaks, XP, one league tier, friends leaderboard
- Email/Google auth, Razorpay + Stripe, Pro tier
- Async prompt battles vs ghosts only

### Explicitly out of v0

Agent debugging (needs the trace fixture library and a mobile trace renderer — 3+ weeks on its own),
RAG missions, connector labs, SDD quests, live battles, badges beyond three, Teams, Android launch,
content beyond day 30.

Each of those is a headline feature and each is *correctly* cut: none of them changes whether D7 is
25% or 8%.

### 12 weeks

| Wk | Engineering | Content | Milestone |
|---|---|---|---|
| 1 | Repo, schema, CI, auth | T1 skill specs + exit criteria | Skeleton deploys |
| 2 | **Eval harness + grading service** | First 3 rubrics + golden sets | **Grader measurable** |
| 3 | Lesson player (web), exercise types 1–4 | T1 lessons 1–6 | First playable lesson |
| 4 | Free-form rep UI, SSE streaming grade | T1 lessons 7–12 + rubrics | **T1 complete end-to-end** |
| 5 | XP ledger, streaks, mastery/decay | T2 lessons 1–6 | Progression works |
| 6 | RN app shell, lesson player parity | T2 lessons 7–12 | Runs on a phone |
| 7 | Leagues, friends leaderboard, push | T2 lessons 13–18 | **All 30 lessons live** |
| 8 | Payments, Pro gating, upgrade moments | Golden-set expansion pass | Can take money |
| 9 | Async battles + ghosts, share cards | Battle brief library (20) | Social loop closed |
| 10 | **Closed beta — 100 users from the channel** | Fix what beta breaks | **Real D7 data** |
| 11 | Android, perf, onboarding rework | Rubric tuning from real submissions | Both platforms |
| 12 | Public launch | Launch-week content | **Ship** |

**Week 10 is the real milestone.** If closed-beta D7 is under 20%, stop and fix the loop before
public launch. Shipping a leaky bucket to your channel audience burns your best distribution once,
and you don't get it back.

---

## 19. Go-to-market via Prompt Vidya

The channel is the unfair advantage. Use it structurally, not just as an announcement.

**1. Make every video end in a rep.** Each Prompt Vidya video ships with a companion Riyaz lesson —
"you just watched me do it, now you do it, 10 minutes, link in description." This is the single
highest-converting mechanic available to you and it requires the content pipeline to be *coupled*
to the video calendar. Design for that from week 1.

**2. Launch to a waitlist, not to the public.** 4–6 weeks of "90 days to AI fluency, starting
<date>" builds a cohort that starts together — which makes leagues populated and battles matched on
day one instead of empty. Cohort launches also give you clean retention curves.

**3. Public streak accountability.** Shareable streak/report cards designed for LinkedIn, where P1
lives and where "I'm 47 days into learning AI" is genuinely good personal-brand content. The share
card is a growth feature; give it real design attention, not a screenshot with a logo.

**4. The 90-day challenge as a recurring event.** Run it quarterly with a cohort leaderboard and a
completion certificate. Recurring events give you a reason to re-market to lapsed users, which is
otherwise very hard.

**5. Seed the difficulty upward, not downward.** The instinct is to make lesson 1 trivially easy.
Resist it slightly — your channel audience is not a general consumer audience, and an insultingly
easy first lesson signals "this is not for me" to P3/P4. Aim for "I got that right but it made me
think."

**Cross-promotion sequencing:** waitlist (week 6) → beta invite to top 100 commenters (week 10) →
launch video (week 12) → companion lessons on every video thereafter (ongoing) → first 90-day
challenge cohort (week 16).

---

## 20. Risks and kill criteria

| # | Risk | Likelihood | Impact | Mitigation | Kill criterion |
|---|---|---|---|---|---|
| R1 | **Grader isn't trusted.** Learners feel scores are arbitrary. | Medium | Fatal | Binary criteria, evidence quotes, golden sets, visible per-criterion breakdown | Agreement <85% after two tuning cycles → rebuild grading approach before launch |
| R2 | **10 minutes isn't enough to teach anything real.** Users feel it's shallow. | Medium | High | The twist mechanic; multi-day missions; exit criteria that demand transfer | Beta users say "fun but I didn't learn anything" → restructure toward 15-min sessions with fewer, deeper reps |
| R3 | **Content velocity can't keep up.** Users finish everything in 6 weeks. | **High** | High | Mastery-decay-driven infinite warm-ups; scenario parameterization; weekly current-events lesson | Median engaged user exhausts content before day 60 |
| R4 | **Unit economics don't close.** | Medium | Fatal | Free-tier cap, caching discipline, deterministic-first, Batch API, price testing | Contribution margin <20% at 10k DAU after price tests |
| R5 | **The category moves under you.** Prompting becomes obsolete. | Medium | Medium | Curriculum is a graph, not a list; T3–T6 already skate toward agents/specs | — (this is a reason to build the *graph*, not to not build) |
| R6 | **A big player ships this.** OpenAI/Google add a learn tab. | Low–Med | High | Rubric library + habit + community are the moat, not content | — (compete on depth and trust, not on being first) |
| R7 | **Gamification feels juvenile to professionals.** | Medium | Medium | Restrained visual language, no guilt-tripping, professional tone, LinkedIn-worthy share cards | P1 interviews consistently cite "feels like a kids' app" |
| R8 | **Prompt-injection through submissions.** Learner jailbreaks the grader for a perfect score. | **High** | Medium | Submissions are always in a user-content block, never in the system prompt; injection scan in the guard stage; anomaly detection on perfect scores | — (assume this happens; design for it now, not after) |
| R9 | Channel audience ≠ paying audience. Great engagement, no revenue. | Medium | High | Test price early with the waitlist; interview P1 before building payments | Waitlist → paid intent below 5% at any tested price |

**R3 deserves emphasis.** Content exhaustion is the most likely way this dies quietly — the app
works, people love it, they finish it, they leave. The mastery-decay engine
([§12](#12-data-model)) and scenario parameterization ([§13](#13-content-pipeline--how-to-author-400-lessons-without-dying))
are the answers, and both need to exist in v0 even though neither shows up in a demo.

---

## 21. Open decisions

Things I could not decide for you. Each blocks something.

| # | Decision | Options | Blocks | My recommendation |
|---|---|---|---|---|
| D1 | **Name + trademark** | Riyaz / Abhyas / other | All branding, domains, app store | Riyaz, pending TM + domain check |
| D2 | **Language of the app** | English-only / Hinglish / both | Content pipeline, rubrics ×2 | English UI, **Hinglish scenario briefs and feedback**. Matches the channel voice; halves rubric work vs full localization |
| D3 | **Streak rule** | Strict daily / 5-of-7 | Streak engine, entire retention model | 5-of-7, displayed as unbroken. A/B it in beta |
| D4 | **Price** | ₹399 / ₹599 / ₹699 | Whether the business closes | Test ₹399 vs ₹699 on the waitlist before writing payment code |
| D5 | **Free-tier graded-rep cap** | 1/day / 3/day / 3/week | Unit economics, conversion | 1/day. It is both the cost control and the best conversion moment |
| D6 | **Platform first** | iOS / Android / web | Week 6–11 sequencing | Web for beta (fastest iteration), then Android first at launch — India install base |
| D7 | **Do you build alone or hire?** | Solo / +1 eng / +1 content | The 12-week plan assumes ~2 FTE | The plan is not achievable solo. If solo, cut to T1 only and 16 weeks |
| D8 | **Company or channel product?** | Separate entity / channel extension | Fundraising, branding, exit | Separate entity, channel as the distribution partner |

---

## Appendix — related files

- [`schema/lesson.schema.json`](schema/lesson.schema.json) — the lesson + exercise + rubric contract
- [`schema/samples/t2-l07-output-contract.json`](schema/samples/t2-l07-output-contract.json) — a full
  Promptcraft lesson with a rubric-graded rep
- [`schema/samples/t3-l04-agent-debug.json`](schema/samples/t3-l04-agent-debug.json) — a hybrid-graded
  agent-debugging lesson
- [`schema/samples/t1-l03-context-window.json`](schema/samples/t1-l03-context-window.json) — a
  fully deterministic (zero-LLM-cost) Foundations lesson
