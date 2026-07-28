#!/usr/bin/env python3
"""Riyaz grader eval harness.

Measures the two numbers that decide whether this product is viable at all
(BLUEPRINT.md sections 9, 17, 20-R1):

    agreement       — do the grader's per-criterion verdicts match human labels?   target >= 90%
    self-consistency— does the same submission get the same verdicts twice?        target >= 95%

Below those thresholds, learners are being graded arbitrarily, and no amount of
content or gamification will hold retention. This script exits non-zero when either
threshold is missed so it can gate a merge.

Usage:
    python run_eval.py --offline          # no API key needed: validate sets, sanity checks
    python run_eval.py                    # full run, 2 passes per submission
    python run_eval.py --runs 3 --rubric rubric.t2-l07.classifier-contract
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# pylint: disable=wrong-import-position  # the path shim above must run first
from grader import for_tier, judge, load_rubrics, score_grade  # noqa: E402
from grader.judge import constitution  # noqa: E402
from grader.rubric import Rubric  # noqa: E402

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"

AGREEMENT_TARGET = 0.90
CONSISTENCY_TARGET = 0.95


def load_golden(rubric: Rubric) -> list[dict] | None:
    """Labelled submissions for a rubric, or None if none have been authored yet.

    A rubric without a golden set is *ungated* — it can be silently broken by any
    prompt or criterion edit and nothing will catch it. That is a real gap, so it is
    reported loudly rather than raised: the harness's job is to make coverage visible,
    not to refuse to run until coverage is complete.
    """
    path = GOLDEN_DIR / Path(rubric.golden_set_id).name
    if not path.exists():
        return None
    items = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ids = {c.id for c in rubric.criteria}
    for item in items:
        labelled = set(item["labels"])
        if labelled != ids:
            missing, extra = ids - labelled, labelled - ids
            raise ValueError(
                f"{path.name}:{item['id']} label mismatch — missing {sorted(missing)}, "
                f"unexpected {sorted(extra)}"
            )
    return items


def human_score(rubric: Rubric, labels: dict[str, bool]) -> float:
    earned = sum(c.weight for c in rubric.criteria if labels[c.id] and not c.is_negative)
    penalty = sum(c.weight for c in rubric.criteria if labels[c.id] and c.is_negative)
    total = rubric.positive_weight or 1.0
    return max(0.0, min(1.0, (earned - penalty) / total))


def offline_checks(rubrics: dict[str, Rubric]) -> int:
    """Everything verifiable without an API key."""
    problems = 0
    text = constitution()
    approx_tokens = int(len(text) / 3.6)  # rough; confirm with count_tokens when a key is available
    print(f"constitution: {len(text):,} chars, ~{approx_tokens:,} tokens (heuristic)")

    for tier_name in ("standard", "hard"):
        model = for_tier(tier_name)
        floor = model.min_cacheable_tokens
        margin = (approx_tokens - floor) / floor
        if approx_tokens < floor:
            status, problems = "TOO SHORT — will not cache", problems + 1
        elif margin < 0.15:
            # The heuristic is +/- ~15%, so a thin margin is indistinguishable from
            # being under the floor. Caching fails silently, so treat this as a problem.
            status, problems = f"THIN (+{margin:.0%}) — confirm with count_tokens", problems + 1
        else:
            status = f"OK (+{margin:.0%})"
        print(f"  cacheable on {model.model_id:<20} (min {floor:>5,}): {status}")

    print()
    ungated = []
    for rubric in rubrics.values():
        items = load_golden(rubric)
        if items is None:
            ungated.append(rubric.id)
            continue
        pos = sum(1 for c in rubric.criteria if not c.is_negative)
        neg = len(rubric.criteria) - pos
        weight_sum = rubric.positive_weight
        scores = [human_score(rubric, i["labels"]) for i in items]
        spread = f"{min(scores):.2f}–{max(scores):.2f}"
        warn = ""
        if abs(weight_sum - 1.0) > 0.001:
            warn += f"  [!] positive weights sum to {weight_sum:.2f}, not 1.00"
            problems += 1
        if len(items) < 10:
            warn += f"  [!] only {len(items)} golden items (want ~20)"
        print(
            f"{rubric.id}\n"
            f"  tier={rubric.grader_tier} criteria={pos}+{neg}neg golden={len(items)} "
            f"human score spread {spread}{warn}"
        )
        # Constraints stated in the exercise must each map to a criterion.
        if rubric.constraints and len(rubric.constraints) > pos:
            print(
                f"  [!] {len(rubric.constraints)} stated constraints but only {pos} positive "
                "criteria — every constraint needs one"
            )
            problems += 1

    if ungated:
        print(f"\nCOVERAGE GAP — {len(ungated)} rubric(s) have no golden set and are ungated:")
        for rid in ungated:
            print(f"  {rid}")
        print("  These can be broken by any edit without the harness noticing.")
    return problems


def evaluate(rubric: Rubric, items: list[dict], runs: int, workers: int) -> dict:
    client = None  # default client; created lazily inside judge()

    def one(item: dict, run_idx: int) -> tuple[str, int, dict]:
        verdict = judge(rubric, item["submission"], client=client)
        grade = score_grade(rubric, item["submission"], verdict.raw)
        return item["id"], run_idx, {"grade": grade, "verdict": verdict}

    # Warm the cache with a single request first. Concurrent requests with an identical
    # prefix all pay full price — none can read what the others are still writing.
    print(f"  warming cache ({rubric.grader_tier} tier)...", flush=True)
    warm_id, _, warm = one(items[0], 0)
    print(
        f"  warm-up: {warm['verdict'].cache_write_tokens:,} tokens written, "
        f"{warm['verdict'].latency_ms}ms"
    )

    jobs = [(item, r) for item in items for r in range(runs)]
    jobs = [(i, r) for (i, r) in jobs if not (i["id"] == warm_id and r == 0)]

    results: dict[str, dict[int, dict]] = defaultdict(dict)
    results[warm_id][0] = warm

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for item_id, run_idx, payload in pool.map(lambda a: one(*a), jobs):
            results[item_id][run_idx] = payload

    return results


def report(rubric: Rubric, items: list[dict], results: dict, runs: int) -> dict:
    by_id = {i["id"]: i for i in items}
    per_criterion = defaultdict(lambda: {"hits": 0, "total": 0, "fp": 0, "fn": 0})
    consistency_hits = consistency_total = 0
    score_errors: list[float] = []
    pass_agree = 0
    costs: list[float] = []
    latencies: list[int] = []
    cache_hits = cache_total = 0
    flips = 0
    disagreements: list[str] = []

    for item_id, runs_map in results.items():
        labels = by_id[item_id]["labels"]

        # Agreement is measured on run 0; later runs feed self-consistency only.
        grade = runs_map[0]["grade"]
        actual = {c.id: c.met for c in grade.criteria}

        for cid, expected in labels.items():
            bucket = per_criterion[cid]
            bucket["total"] += 1
            if actual[cid] == expected:
                bucket["hits"] += 1
            else:
                if actual[cid] and not expected:
                    bucket["fp"] += 1
                else:
                    bucket["fn"] += 1
                disagreements.append(
                    f"    {item_id}/{cid}: human={expected} grader={actual[cid]} "
                    f"| {next(c.evidence for c in grade.criteria if c.id == cid)[:90]}"
                )

        expected_score = human_score(rubric, labels)
        score_errors.append(abs(grade.score - expected_score))
        if (expected_score >= rubric.pass_threshold) == grade.passed:
            pass_agree += 1

        for run_idx, payload in runs_map.items():
            v = payload["verdict"]
            costs.append(v.cost_usd)
            latencies.append(v.latency_ms)
            cache_total += 1
            cache_hits += 1 if v.cache_hit else 0
            flips += payload["grade"].flipped_count

        if runs > 1:
            baseline = {c.id: c.met for c in runs_map[0]["grade"].criteria}
            for run_idx in range(1, runs):
                other = {c.id: c.met for c in runs_map[run_idx]["grade"].criteria}
                for cid in baseline:
                    consistency_total += 1
                    consistency_hits += 1 if baseline[cid] == other[cid] else 0

    agreement = sum(b["hits"] for b in per_criterion.values()) / max(
        1, sum(b["total"] for b in per_criterion.values())
    )
    consistency = consistency_hits / consistency_total if consistency_total else float("nan")

    print(f"\n{'=' * 78}\n{rubric.id}  (v{rubric.version}, tier={rubric.grader_tier})\n{'=' * 78}")
    print(f"{'criterion':<34} {'agree':>7} {'FP':>4} {'FN':>4}")
    for cid, b in per_criterion.items():
        rate = b["hits"] / b["total"]
        mark = " " if rate >= AGREEMENT_TARGET else "<"
        print(f"{cid:<34} {rate:>6.0%}{mark} {b['fp']:>4} {b['fn']:>4}")

    print(f"\n  agreement (criterion-level)  {agreement:>7.1%}   target >= {AGREEMENT_TARGET:.0%}")
    if runs > 1:
        print(
            f"  self-consistency             {consistency:>7.1%}"
            f"   target >= {CONSISTENCY_TARGET:.0%}"
        )
    print(f"  pass/fail agreement          {pass_agree / len(items):>7.1%}")
    print(f"  mean score error             {statistics.mean(score_errors):>7.3f}")
    print(f"  evidence flips (unquotable)  {flips:>7}")
    print(
        f"\n  cost/grade  ${statistics.mean(costs):.5f}   total ${sum(costs):.4f}"
        f"   cache hit {cache_hits}/{cache_total}"
    )
    print(
        f"  latency     p50 {int(statistics.median(latencies))}ms   "
        f"p95 {int(sorted(latencies)[int(len(latencies) * 0.95) - 1])}ms"
    )

    if disagreements:
        print(f"\n  disagreements ({len(disagreements)}):")
        for line in disagreements[:20]:
            print(line)

    return {
        "rubric": rubric.id,
        "agreement": agreement,
        "consistency": consistency,
        "cost_per_grade": statistics.mean(costs),
        "cache_hit_rate": cache_hits / max(1, cache_total),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="no API calls; validate sets only")
    ap.add_argument(
        "--runs", type=int, default=2, help="passes per submission (>=2 for consistency)"
    )
    ap.add_argument("--rubric", help="run a single rubric by id")
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()

    rubrics = load_rubrics()
    if args.rubric:
        rubrics = {args.rubric: rubrics[args.rubric]}

    if args.offline:
        print("OFFLINE — structural checks only, no grading performed\n")
        problems = offline_checks(rubrics)
        print(f"\n{'FAIL' if problems else 'OK'}: {problems} problem(s)")
        return 1 if problems else 0

    summaries = []
    for rubric in rubrics.values():
        items = load_golden(rubric)
        if items is None:
            print(f"\nSKIP {rubric.id} — no golden set authored yet (ungated)")
            continue
        print(f"\ngrading {len(items)} submissions x {args.runs} runs -> {rubric.id}")
        results = evaluate(rubric, items, args.runs, args.workers)
        summaries.append(report(rubric, items, results, args.runs))

    print(f"\n{'=' * 78}\nSUMMARY\n{'=' * 78}")
    failed = False
    for s in summaries:
        ok = s["agreement"] >= AGREEMENT_TARGET and (
            s["consistency"] != s["consistency"] or s["consistency"] >= CONSISTENCY_TARGET
        )
        failed |= not ok
        print(
            f"{'PASS' if ok else 'FAIL'}  {s['rubric']:<40} "
            f"agree {s['agreement']:.1%}  consist {s['consistency']:.1%}  "
            f"${s['cost_per_grade']:.5f}/grade  cache {s['cache_hit_rate']:.0%}"
        )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
