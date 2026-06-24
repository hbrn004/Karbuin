#!/usr/bin/env python3
"""Karbuin Benchmark Suite — runs the permanent 200-query benchmark.

Usage:
    python tests/run_benchmark.py              # Run and compare to baseline
    python tests/run_benchmark.py --save       # Run and save as baseline
    python tests/run_benchmark.py --no-baseline  # Run without comparison
    python tests/run_benchmark.py --filter honda  # Run only Honda queries

Metrics:
    - parser_hit_rate: % queries where parser identified >=1 symptom
    - diagnosis_success: % queries with status ok OR ambiguous_top_results
    - no_parse: count of no_symptom_match results
    - regression_detection: compare to saved baseline

Outputs:
    - Console summary
    - tests/benchmark_results.json (per-query detail)
    - tests/benchmark_baseline.json (if --save)
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from karbuin.kb import KnowledgeBase
from karbuin.diagnose import Diagnoser


def load_benchmark(path: Path) -> dict:
    return json.loads(path.read_text())


def run_benchmark(benchmark: dict, kb_path: str = "data/seed",
                  filter_category: str | None = None,
                  filter_motor: str | None = None) -> list[dict]:
    """Run all benchmark queries and return per-query results."""
    kb = KnowledgeBase(kb_path)
    diag = Diagnoser(kb)

    queries = benchmark["queries"]
    if filter_category:
        queries = [q for q in queries if q["category"] == filter_category]
    if filter_motor:
        queries = [q for q in queries if q["motor_id"] == filter_motor]

    results = []
    for q in queries:
        try:
            r = diag.diagnose(user_input=q["input"], motor_id=q["motor_id"])
            parsed = r.get("parsed_symptoms", [])
            parsed_ids = [p["symptom_id"] for p in parsed]
            results_r = r.get("results", [])
            partial = r.get("partial_results", [])

            # Classify outcome
            status = r.get("status", "unknown")
            parse_hit = len(parsed_ids) > 0
            if status == "ok" and results_r:
                outcome = "ok"
            elif status == "ambiguous_top_results":
                outcome = "ambiguous"
            elif status == "confidence_too_low":
                outcome = "low_confidence"
            elif status == "no_symptom_match":
                outcome = "no_parse"
            else:
                outcome = "other"

            results.append({
                "id": q["id"],
                "input": q["input"],
                "motor_id": q["motor_id"],
                "category": q["category"],
                "status": status,
                "outcome": outcome,
                "parse_hit": parse_hit,
                "parsed_ids": parsed_ids,
                "n_results": len(results_r),
                "n_partial": len(partial),
                "top_confidence": results_r[0]["confidence"] if results_r else (
                    partial[0]["confidence"] if partial else 0.0
                ),
                "top_cause": results_r[0]["cause"]["id"] if results_r else (
                    partial[0]["cause"]["id"] if partial else None
                ),
            })
        except Exception as e:
            results.append({
                "id": q["id"],
                "input": q["input"],
                "motor_id": q["motor_id"],
                "category": q["category"],
                "status": "error",
                "outcome": "error",
                "error": str(e),
                "parse_hit": False,
                "parsed_ids": [],
            })

    return results


def compute_metrics(results: list[dict]) -> dict:
    """Compute aggregate metrics from results."""
    total = len(results)
    if total == 0:
        return {"total": 0}

    parse_hit = sum(1 for r in results if r["parse_hit"])
    ok = sum(1 for r in results if r["outcome"] == "ok")
    ambig = sum(1 for r in results if r["outcome"] == "ambiguous")
    low_conf = sum(1 for r in results if r["outcome"] == "low_confidence")
    no_parse = sum(1 for r in results if r["outcome"] == "no_parse")
    diag_success = ok + ambig

    by_category = defaultdict(lambda: {"total": 0, "parse_hit": 0, "ok": 0,
                                        "ambig": 0, "low_conf": 0, "no_parse": 0})
    for r in results:
        c = r["category"]
        by_category[c]["total"] += 1
        if r["parse_hit"]:
            by_category[c]["parse_hit"] += 1
        if r["outcome"] == "ok":
            by_category[c]["ok"] += 1
        elif r["outcome"] == "ambiguous":
            by_category[c]["ambig"] += 1
        elif r["outcome"] == "low_confidence":
            by_category[c]["low_conf"] += 1
        elif r["outcome"] == "no_parse":
            by_category[c]["no_parse"] += 1

    by_motor = defaultdict(lambda: {"total": 0, "parse_hit": 0})
    for r in results:
        m = r["motor_id"]
        by_motor[m]["total"] += 1
        if r["parse_hit"]:
            by_motor[m]["parse_hit"] += 1

    return {
        "total": total,
        "parse_hit": parse_hit,
        "parse_hit_rate": parse_hit / total * 100,
        "diagnosis_success": diag_success,
        "diagnosis_success_rate": diag_success / total * 100,
        "ok": ok,
        "ok_rate": ok / total * 100,
        "ambiguous": ambig,
        "low_confidence": low_conf,
        "no_parse": no_parse,
        "by_category": dict(by_category),
        "by_motor": dict(by_motor),
    }


def detect_regressions(current: list[dict], baseline: list[dict]) -> dict:
    """Compare current results to baseline, detect regressions."""
    baseline_map = {r["id"]: r for r in baseline}
    current_map = {r["id"]: r for r in current}

    regressions = []  # Was ok/ambiguous, now no_parse/low_confidence
    improvements = []  # Was no_parse/low_confidence, now ok/ambiguous

    OUTCOME_RANK = {
        "ok": 4,
        "ambiguous": 3,
        "low_confidence": 2,
        "no_parse": 1,
        "error": 0,
        "other": 0,
    }

    for qid, cur in current_map.items():
        if qid not in baseline_map:
            continue
        base = baseline_map[qid]
        base_rank = OUTCOME_RANK.get(base["outcome"], 0)
        cur_rank = OUTCOME_RANK.get(cur["outcome"], 0)
        if cur_rank < base_rank:
            regressions.append({
                "id": qid,
                "input": cur["input"],
                "baseline_outcome": base["outcome"],
                "current_outcome": cur["outcome"],
            })
        elif cur_rank > base_rank:
            improvements.append({
                "id": qid,
                "input": cur["input"],
                "baseline_outcome": base["outcome"],
                "current_outcome": cur["outcome"],
            })

    return {"regressions": regressions, "improvements": improvements}


def print_summary(metrics: dict, regression: dict | None = None):
    """Print formatted benchmark summary."""
    print("=" * 78)
    print("KARBUIN BENCHMARK SUITE — RESULTS")
    print("=" * 78)
    print(f"  Total queries:          {metrics['total']}")
    print(f"  Parser hit rate:        {metrics['parse_hit']:3d}/{metrics['total']} ({metrics['parse_hit_rate']:.1f}%)")
    print(f"  Diagnosis success:      {metrics['diagnosis_success']:3d}/{metrics['total']} ({metrics['diagnosis_success_rate']:.1f}%)")
    print(f"    ok (clear):           {metrics['ok']:3d} ({metrics['ok_rate']:.1f}%)")
    print(f"    ambiguous:            {metrics['ambiguous']:3d}")
    print(f"    low_confidence:       {metrics['low_confidence']:3d}")
    print(f"    no_parse:             {metrics['no_parse']:3d}")
    print()

    print("BY CATEGORY:")
    print(f"  {'Category':12s} | {'Total':>5s} | {'Parse':>10s} | {'OK':>3s} | {'Ambig':>5s} | {'LC':>3s} | {'NP':>3s} | Diag%")
    print("  " + "-" * 76)
    for cat in ["honda", "yamaha", "suzuki", "kawasaki", "multi", "typo", "casual"]:
        if cat not in metrics["by_category"]:
            continue
        c = metrics["by_category"][cat]
        diag = c["ok"] + c["ambig"]
        diag_pct = diag / c["total"] * 100 if c["total"] else 0
        parse_pct = c["parse_hit"] / c["total"] * 100 if c["total"] else 0
        print(f"  {cat:12s} | {c['total']:>5d} | {c['parse_hit']:>3d}/{c['total']:<3d} ({parse_pct:5.1f}%) | {c['ok']:>3d} | {c['ambig']:>5d} | {c['low_conf']:>3d} | {c['no_parse']:>3d} | {diag_pct:.1f}%")

    if regression is not None:
        print()
        print("REGRESSION DETECTION:")
        print(f"  Regressions:  {len(regression['regressions'])}")
        print(f"  Improvements: {len(regression['improvements'])}")
        if regression["regressions"]:
            print("  ⚠️  Regressions detail:")
            for reg in regression["regressions"][:10]:
                print(f"    [{reg['id']}] '{reg['input']}': {reg['baseline_outcome']} → {reg['current_outcome']}")
        if regression["improvements"]:
            print("  ✅ Improvements detail:")
            for imp in regression["improvements"][:10]:
                print(f"    [{imp['id']}] '{imp['input']}': {imp['baseline_outcome']} → {imp['current_outcome']}")

    print("=" * 78)


def main():
    parser = argparse.ArgumentParser(description="Karbuin Benchmark Suite")
    parser.add_argument("--benchmark", type=Path,
                        default=ROOT / "tests" / "benchmark_v1.json",
                        help="Path to benchmark JSON")
    parser.add_argument("--baseline", type=Path,
                        default=ROOT / "tests" / "benchmark_baseline.json",
                        help="Path to baseline for regression comparison")
    parser.add_argument("--save", action="store_true",
                        help="Save current results as new baseline")
    parser.add_argument("--no-baseline", action="store_true",
                        help="Skip baseline comparison")
    parser.add_argument("--filter", type=str,
                        help="Run only specified category")
    parser.add_argument("--output", type=Path,
                        help="Path to save detailed results JSON")
    args = parser.parse_args()

    if not args.benchmark.exists():
        print(f"❌ Benchmark file not found: {args.benchmark}")
        return 1

    benchmark = load_benchmark(args.benchmark)
    print(f"Loaded benchmark: {benchmark['version']} ({len(benchmark['queries'])} queries)")
    print()

    # Run
    results = run_benchmark(benchmark, filter_category=args.filter)

    # Compute metrics
    metrics = compute_metrics(results)

    # Compare to baseline
    regression = None
    if not args.no_baseline and args.baseline.exists():
        baseline = json.loads(args.baseline.read_text())
        baseline_results = baseline.get("results", baseline)
        regression = detect_regressions(results, baseline_results)

    # Print summary
    print_summary(metrics, regression)

    # Save
    timestamp = datetime.now().isoformat()
    output_data = {
        "version": benchmark["version"],
        "run_at": timestamp,
        "filter": args.filter,
        "metrics": metrics,
        "results": results,
    }
    if args.save:
        baseline_save = {
            "version": benchmark["version"],
            "saved_at": timestamp,
            "metrics": metrics,
            "results": results,
        }
        args.baseline.write_text(json.dumps(baseline_save, indent=2, ensure_ascii=False))
        print(f"✅ Saved baseline to {args.baseline}")
    if args.output:
        args.output.write_text(json.dumps(output_data, indent=2, ensure_ascii=False))
        print(f"✅ Saved detailed results to {args.output}")

    return 0 if not regression or not regression["regressions"] else 2


if __name__ == "__main__":
    sys.exit(main())
