# Riyaz grader — spike

The riskiest assumption in the whole Riyaz concept is that a free-form prompt can be graded
consistently enough that learners trust the score. [`BLUEPRINT.md` §20-R1](../BLUEPRINT.md#20-risks-and-kill-criteria)
calls it fatal if it fails: below ~85% grader–human agreement, learners are being judged
arbitrarily, they stop trusting the number, and no amount of content or streak mechanics holds
retention.

This directory tests that assumption with ~700 lines of Python instead of a 12-week app build.

**Not yet run against the live API.** The environment this was written in has no Anthropic
credentials, so the numbers that matter — agreement, self-consistency, real cost, real cache-hit
rate — are still unmeasured. Everything up to the API boundary is built and tested. See
[Running it](#running-it).

---

## The pipeline

```
submission
   │
   ├─ 1. guards ........... empty / too short / too long / injection scan     no LLM, no cost
   ├─ 2. hard checks ...... regex + schema validation                         no LLM, no cost
   ├─ 3. rubric judge ..... ONE call, structured output, cached constitution  the only cost
   └─ 4. score ............ evidence verified, score computed in code         no LLM, no cost
```

| Stage | Module | Notes |
|---|---|---|
| 1 | [`guards.py`](guards.py) | Rejects before spending anything, with feedback more specific than a rubric could give |
| 2 | [`guards.py`](guards.py) | Per-exercise regex/schema checks |
| 3 | [`judge.py`](judge.py) | Builds the prompt, makes the call, returns raw verdict + usage |
| 4 | [`score.py`](score.py) | Verifies evidence, flips unquotable claims, computes the score |
| — | [`models.py`](models.py) | Tier routing, per-model request quirks, cost accounting |
| — | [`rubric.py`](rubric.py) | Loads rubrics out of the lesson JSON |
| — | [`constitution.md`](constitution.md) | The cached system prompt — grading policy + 7 worked examples |

## Three design decisions worth knowing

**The judge never emits a number.** It answers each criterion `met: true/false` and the score is
arithmetic in [`score.py`](score.py). This is what kills score drift: identical booleans always
produce an identical score, and every point traces to a named criterion, which is what makes
feedback specific instead of a bare "6/10".

**Every `met: true` needs a verbatim quote, or it is discarded.** [`verify_evidence`](score.py)
searches the submission for the judge's quote (whitespace-normalised, otherwise strict). No match →
the criterion is flipped to unmet before scoring. It is the only mechanical check available on a
model's judgment, and it costs nothing. `flipped_count` on every grade tells you how often the
judge is reaching.

**The constitution is deliberately ~5,000 tokens.** Haiku 4.5 will not cache a prefix below **4,096
tokens**, and it fails *silently* — no error, `cache_creation_input_tokens: 0`, and a ~2.25× bill.
A lean 1,500-token grading prompt would be the obvious choice and would quietly break the economics
in [`BLUEPRINT.md` §15](../BLUEPRINT.md#15-unit-economics--the-make-or-break-section). The
constitution is real content sized against that floor, and `run_eval.py --offline` fails the build
if it drifts within 15% of it.

## Running it

```bash
cd product/riyaz
pip install anthropic jsonschema pytest

# No API key needed — structural checks + the whole scoring path
python grader/evals/run_eval.py --offline
python -m pytest grader/tests/ -q

# Needs ANTHROPIC_API_KEY (or `ant auth login`)
python grader/evals/run_eval.py                 # 2 passes per submission
python grader/evals/run_eval.py --runs 3 --rubric rubric.t2-l07.classifier-contract
```

`run_eval.py` exits non-zero when agreement < 90% or self-consistency < 95%, so it can gate a
merge. It warms the cache with a single request before fanning out — concurrent requests with the
same prefix all pay full price, since none can read what the others are still writing.

### What the output means

| Number | Target | What it tells you |
|---|---|---|
| **agreement** | ≥ 90% | Per-criterion match against human labels. The one that decides the product. |
| **self-consistency** | ≥ 95% | Same submission, two runs, same verdicts. Below this, scores are a coin flip. |
| FP / FN per criterion | — | Which criteria the judge is too generous or too harsh on. Fix the criterion wording, not the constitution. |
| evidence flips | low | How often the judge claimed something it could not quote. |
| cost/grade | ≈ $0.0036 | Compare against §15. A large gap means the cache is not hitting. |
| cache hit | ~all but the first | Anything less and the economics in §15 do not hold. |

## Current state

| | |
|---|---|
| Pipeline stages 1, 2, 4 | built, 32 tests passing |
| Stage 3 (the API call) | built, **never executed** — no credentials in this environment |
| Constitution | 17.5k chars, ~4,900 tokens (heuristic), +19% over the Haiku floor |
| Golden sets | 26 hand-labelled submissions across 2 rubrics |
| Ungated rubrics | 2 (both twists) — flagged by `--offline`, not yet authored |

The golden sets deliberately include the awkward cases: a Devanagari submission, informal Hinglish,
two prompt-injection attempts, a padded-but-confident answer, a long-but-entirely-substantive answer
(the control for length bias), and several near-misses where one criterion is satisfied and the rest
are not (the control for holistic grading bleeding across criteria).

## What to do with this

1. **Run it with a key.** One command, a few cents. That produces the two numbers that decide
   whether the concept is viable.
2. **If agreement < 90%,** read the per-criterion FP/FN table. Almost always the fix is rewording
   one criterion to be narrower, not editing the constitution.
3. **If self-consistency < 95%,** the criteria are too subjective — split the ambiguous one into
   two sharper binary checks.
4. **Confirm the token count.** `judge.count_constitution_tokens()` gives the real number; the
   offline heuristic is ±15% and the caching floor fails silently.
5. **Grow the golden sets** to ~20 per rubric, and author the two missing ones. Then feed them from
   real learner submissions — this library is the moat described in
   [§5](../BLUEPRINT.md#5-competitive-positioning), and it only compounds if it is fed.
