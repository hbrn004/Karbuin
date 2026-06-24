"""Regression test: 2-tak/4-tak motor-type filtering.

This test guards against a bug where 4-tak-specific causes (like
seal_klep_bocor) were incorrectly returned as candidates for 2-tak
motors (RX-King, Ninja 150) that don't have such components.

Fix: added `motor_type_filter` to relasi (engine change in
karbuin/inference.py: matches_filter + rank). 4-tak-specific relasi
now carry `motor_type_filter="4_stroke"`, so the engine skips them
when the target motor is `2_stroke`.

Cases tested:
  1. RX-King (2-tak) + asap_biru → NO seal_klep_bocor candidate
  2. Ninja 150 (2-tak) + asap_biru → NO seal_klep_bocor candidate
  3. Supra X125 (4-tak) + asap_biru → seal_klep_bocor CAN still appear
  4. Tiger 2000 (4-tak) + klep_renggang → klep_renggang CAN still appear
  5. Supra X125 (4-tak) + klep_bunyi → klep_renggang CAN still appear

Run: uv run --quiet python3 tests/test_regression_2tak_4tak.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from karbuin.kb import KnowledgeBase
from karbuin.diagnose import Diagnoser

SEED = ROOT / "data" / "seed"

# (motor_id, motor_type, user_input, must_have_cause, must_NOT_have_cause, description)
CASES = [
    # --- 2-tak motors: 4-tak causes MUST NOT appear ---
    (
        "yamaha_rx_king_karbu",
        "2_stroke",
        "asap biru",
        None,                # any cause OK
        "seal_klep_bocor",   # but NOT seal_klep_bocor
        "RX-King (2-tak) + asap_biru: seal_klep_bocor MUST NOT appear",
    ),
    (
        "yamaha_rx_king_karbu",
        "2_stroke",
        "asap biru",
        None,
        "klep_renggang",     # but NOT klep_renggang either
        "RX-King (2-tak) + asap_biru: klep_renggang MUST NOT appear",
    ),
    (
        "kawasaki_ninja_150",
        "2_stroke",
        "asap biru",
        None,
        "seal_klep_bocor",
        "Ninja 150 (2-tak) + asap_biru: seal_klep_bocor MUST NOT appear",
    ),
    (
        "kawasaki_ninja_150",
        "2_stroke",
        "asap biru",
        None,
        "klep_renggang",
        "Ninja 150 (2-tak) + asap_biru: klep_renggang MUST NOT appear",
    ),

    # --- 4-tak motors: 4-tak causes CAN appear (positive regression) ---
    (
        "honda_supra_x125_karbu",
        "4_stroke",
        "asap biru",
        "seal_klep_bocor",   # SHOULD still appear for 4-tak motor
        None,
        "Supra X125 (4-tak) + asap_biru: seal_klep_bocor MUST appear (positive regression)",
    ),
    (
        "honda_tiger_2000",
        "4_stroke",
        "asap biru",
        "seal_klep_bocor",
        None,
        "Tiger 2000 (4-tak) + asap_biru: seal_klep_bocor MUST appear (positive regression)",
    ),
    (
        "honda_supra_x125_karbu",
        "4_stroke",
        "klep bunyi",
        "klep_renggang",
        None,
        "Supra X125 (4-tak) + klep bunyi: klep_renggang MUST appear (positive regression)",
    ),
    (
        "honda_tiger_2000",
        "4_stroke",
        "klep bunyi",
        "klep_renggang",
        None,
        "Tiger 2000 (4-tak) + klep bunyi: klep_renggang MUST appear (positive regression)",
    ),
]


def main():
    kb = KnowledgeBase(SEED)
    diag = Diagnoser(kb)
    passed = 0
    failed = 0
    for motor_id, expected_type, user_input, must_have, must_not, desc in CASES:
        # Verify motor is correctly classified
        motor = kb.get_motor(motor_id)
        actual_type = motor.get("engine_type", "MISSING")
        if actual_type != expected_type:
            print(f"  ❌ SETUP: motor {motor_id} engine_type={actual_type}, expected {expected_type}")
            failed += 1
            continue

        # Run diagnosis
        r = diag.diagnose(user_input=user_input, motor_id=motor_id)
        all_causes = [c["cause"]["id"] for c in r.get("results", [])]
        top_two_causes = [c["cause_id"] for c in r.get("top_two", [])]
        all_cause_ids = set(all_causes) | set(top_two_causes)

        ok = True
        if must_have and must_have not in all_cause_ids:
            ok = False
            print(f"  ❌ {desc}")
            print(f"     Expected '{must_have}' in results, but got: {sorted(all_cause_ids)}")
        if must_not and must_not in all_cause_ids:
            ok = False
            print(f"  ❌ {desc}")
            print(f"     '{must_not}' INCORRECTLY in results: {sorted(all_cause_ids)}")
        if ok:
            print(f"  ✅ {desc}")
            print(f"     status={r.get('status')} top_cause={all_cause_ids and list(all_cause_ids)[0]}")
            passed += 1
        else:
            failed += 1

    print()
    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed (out of {len(CASES)} cases)")
    print("=" * 70)
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
