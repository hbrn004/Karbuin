"""Validate real_cases.jsonl against schema and KB.

Usage:
  python3 scripts/validate_real_cases.py
  python3 scripts/validate_real_cases.py --file data/real_cases.jsonl
  python3 scripts/validate_real_cases.py --score  # also run engine + accuracy

Engine FROZEN: this script READS engine KB but does not modify it.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Add parent to path so we can import karbuin
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from karbuin import KnowledgeBase  # noqa: E402

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data" / "seed"
KB = KnowledgeBase(DATA_DIR)


VALID_SOURCE_PREFIXES = (
    "bengkel_", "forum_", "survey",
    "user_submitted", "synthetic_",
)

MOTOR_IDS = {m["id"] for m in KB.motor}
PENYEBAB_IDS = {p["id"] for p in KB.penyebab}
GEJALA_IDS = {g["id"] for g in KB.gejala}
KOMPONEN_IDS = {k["id"] for k in KB.komponen}


def validate_record(rec: dict, line_no: int) -> list[str]:
    """Return list of error messages (empty if valid)."""
    errors = []
    required_top = ["case_id", "ts", "schema_version", "motor", "user_input", "expected"]
    for k in required_top:
        if k not in rec:
            errors.append(f"L{line_no}: missing required field '{k}'")

    # case_id format
    cid = rec.get("case_id", "")
    if cid and not (cid.startswith("RC") and len(cid) >= 4):
        errors.append(f"L{line_no}: case_id '{cid}' must match /^RC[0-9]+$/")

    # schema_version
    sv = rec.get("schema_version")
    if sv is not None and sv != 1:
        errors.append(f"L{line_no}: schema_version={sv} unsupported (only 1)")

    # motor
    motor = rec.get("motor", {})
    if motor:
        mid = motor.get("id")
        if mid and mid not in MOTOR_IDS:
            errors.append(f"L{line_no}: motor.id '{mid}' not in KB. Valid: {sorted(MOTOR_IDS)}")
        year = motor.get("year")
        if year is not None and not (1990 <= year <= 2025):
            errors.append(f"L{line_no}: motor.year {year} out of range [1990, 2025]")

    # user_input
    ui = rec.get("user_input", {})
    if ui:
        raw = ui.get("raw", "")
        if not (5 <= len(raw) <= 1000):
            errors.append(f"L{line_no}: user_input.raw length {len(raw)} not in [5, 1000]")
        for sid in ui.get("explicit_symptoms", []):
            if sid not in GEJALA_IDS:
                errors.append(f"L{line_no}: symptom '{sid}' not in KB")

    # expected
    exp = rec.get("expected", {})
    if exp:
        cause_id = exp.get("cause_id")
        if cause_id and cause_id not in PENYEBAB_IDS:
            errors.append(f"L{line_no}: cause_id '{cause_id}' not in KB")
        cost = exp.get("cost_idr")
        if cost is not None and not (0 <= cost <= 5_000_000):
            errors.append(f"L{line_no}: cost_idr {cost} out of range [0, 5000000]")
        conf = exp.get("confidence")
        if conf is not None and not (1 <= conf <= 5):
            errors.append(f"L{line_no}: expected.confidence {conf} not in [1, 5]")

    # meta
    meta = rec.get("meta", {})
    if meta:
        src = meta.get("source", "")
        if src and not any(src.startswith(p) for p in VALID_SOURCE_PREFIXES):
            errors.append(f"L{line_no}: source '{src}' invalid (must start with one of {VALID_SOURCE_PREFIXES})")

    return errors


def validate_file(path: Path) -> tuple[int, int, list[str], list[dict]]:
    """Validate file. Returns (total, valid, errors, records)."""
    if not path.exists():
        return 0, 0, [f"{path} not found"], []

    total = 0
    valid = 0
    all_errors = []
    seen_ids = set()
    records = []

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"L{line_no}: invalid JSON: {e}")
                continue

            cid = rec.get("case_id")
            if cid in seen_ids:
                all_errors.append(f"L{line_no}: duplicate case_id '{cid}'")
            seen_ids.add(cid)

            errors = validate_record(rec, line_no)
            if not errors:
                valid += 1
            else:
                all_errors.extend(errors)
            records.append(rec)

    return total, valid, all_errors, records


def score_against_engine(records: list[dict]) -> dict:
    """Run engine on each case and compute accuracy metrics."""
    from karbuin import Diagnoser
    from pathlib import Path as _P

    diagnoser = Diagnoser(KB)
    total = 0
    correct_top1 = 0
    correct_top3 = 0
    rejected = 0
    conf_correct_sum = 0.0
    conf_correct_n = 0
    conf_wrong_sum = 0.0
    conf_wrong_n = 0
    by_motor = {}
    by_cause = {}
    failures = []

    for rec in records:
        if rec.get("schema_version") != 1:
            continue
        total += 1
        motor_id = rec.get("motor", {}).get("id")
        raw = rec.get("user_input", {}).get("raw", "")
        explicit = rec.get("user_input", {}).get("explicit_symptoms")
        expected = rec.get("expected", {}).get("cause_id")

        if not expected:
            continue

        result = diagnoser.diagnose(
            user_input=raw,
            motor_id=motor_id,
            explicit_symptoms=explicit,
        )

        results = result.get("results", [])
        top_id = results[0]["cause"]["id"] if results else ""
        top3_ids = [r["cause"]["id"] for r in results[:3]]
        top_conf = results[0].get("confidence", 0) if results else 0

        is_correct = (top_id == expected)
        is_top3 = (expected in top3_ids)
        is_rejected = (result.get("status") == "no_match" or not results)

        if is_correct:
            correct_top1 += 1
            conf_correct_sum += top_conf
            conf_correct_n += 1
        else:
            conf_wrong_sum += top_conf
            conf_wrong_n += 1
            failures.append({
                "case_id": rec.get("case_id"),
                "motor_id": motor_id,
                "user_input": raw[:100],
                "expected": expected,
                "predicted_top": top_id,
                "predicted_conf": round(top_conf, 3),
                "in_top3": is_top3,
            })

        if is_top3:
            correct_top3 += 1

        if is_rejected:
            rejected += 1

        # Per-motor stats
        by_motor.setdefault(motor_id, {"total": 0, "correct": 0})
        by_motor[motor_id]["total"] += 1
        if is_correct:
            by_motor[motor_id]["correct"] += 1

        # Per-cause stats
        by_cause.setdefault(expected, {"total": 0, "correct": 0})
        by_cause[expected]["total"] += 1
        if is_correct:
            by_cause[expected]["correct"] += 1

    avg_conf_correct = conf_correct_sum / conf_correct_n if conf_correct_n else 0
    avg_conf_wrong = conf_wrong_sum / conf_wrong_n if conf_wrong_n else 0

    return {
        "total_scored": total,
        "top1_accuracy": round(correct_top1 / total, 4) if total else 0,
        "top3_accuracy": round(correct_top3 / total, 4) if total else 0,
        "rejected_rate": round(rejected / total, 4) if total else 0,
        "avg_confidence_correct": round(avg_conf_correct, 4),
        "avg_confidence_wrong": round(avg_conf_wrong, 4),
        "confidence_calibration_gap": round(avg_conf_correct - avg_conf_wrong, 4),
        "by_motor": {
            k: {**v, "accuracy": round(v["correct"] / v["total"], 4)}
            for k, v in by_motor.items()
        },
        "by_cause": {
            k: {**v, "accuracy": round(v["correct"] / v["total"], 4)}
            for k, v in by_cause.items()
        },
        "failures": failures[:20],  # top 20 failures
    }


def main():
    parser = argparse.ArgumentParser(description="Validate real_cases.jsonl")
    parser.add_argument("--file", type=Path, default=ROOT / "data" / "real_cases.jsonl",
                        help="Path to JSONL file")
    parser.add_argument("--score", action="store_true",
                        help="Also run engine and compute accuracy")
    args = parser.parse_args()

    print(f"📋 Validating {args.file}...")
    total, valid, errors, records = validate_file(args.file)

    print(f"\n📊 Schema Validation Report")
    print(f"   Total records: {total}")
    print(f"   Valid: {valid}")
    print(f"   Invalid: {total - valid}")

    if errors:
        print(f"\n❌ Errors (showing first 20):")
        for e in errors[:20]:
            print(f"   {e}")
        if len(errors) > 20:
            print(f"   ... {len(errors) - 20} more")
        if total == 0:
            sys.exit(1)

    if valid == 0:
        print("\n❌ No valid records. Aborting.")
        sys.exit(1)

    if args.score and records:
        print(f"\n🎯 Scoring against engine...")
        score = score_against_engine(records)
        print(f"\n📈 Engine Accuracy Report")
        print(f"   Total scored: {score['total_scored']}")
        print(f"   Top-1 Accuracy: {score['top1_accuracy']*100:.1f}%")
        print(f"   Top-3 Accuracy: {score['top3_accuracy']*100:.1f}%")
        print(f"   Rejected rate: {score['rejected_rate']*100:.1f}%")
        print(f"   Avg conf (correct): {score['avg_confidence_correct']:.3f}")
        print(f"   Avg conf (wrong):   {score['avg_confidence_wrong']:.3f}")
        print(f"   Calibration gap:    {score['confidence_calibration_gap']:.3f}")

        if score["by_motor"]:
            print(f"\n🏍 By Motor:")
            for mid, m in sorted(score["by_motor"].items(), key=lambda x: -x[1]["total"]):
                print(f"   {mid:30} {m['correct']:3}/{m['total']:3}  ({m['accuracy']*100:5.1f}%)")

        if score["by_cause"]:
            print(f"\n🎯 By Expected Cause:")
            for cid, c in sorted(score["by_cause"].items(), key=lambda x: -x[1]["total"]):
                print(f"   {cid:30} {c['correct']:3}/{c['total']:3}  ({c['accuracy']*100:5.1f}%)")

        if score["failures"]:
            print(f"\n❌ Top Failures (first 5):")
            for f in score["failures"][:5]:
                print(f"   {f['case_id']}: '{f['user_input'][:60]}'")
                print(f"      expected: {f['expected']}")
                print(f"      predicted: {f['predicted_top']} (conf={f['predicted_conf']}, in_top3={f['in_top3']})")


if __name__ == "__main__":
    main()