"""DiagnosisEngine — weighted inference over relasi_gejala_penyebab.

Confidence formula (v2 — saturating, no symptom-count dilution):
    confidence = 1 - exp(-score / SATURATION_K)
- score = sum of matched relasi weights
- SATURATION_K = 6 (constant) — chosen via benchmark vs K=4 (too aggressive) and K=8 (too conservative)
- Monotonically increasing in score.
- More matched symptoms → higher confidence (no penalty).
- Confidence range for typical cases: 78-97%.
- Follow-up bonus: +5 weight → +3-7pp confidence boost on average.

Reference: /tmp/benchmark_K.py on 5 UAT cases (2026-06-24).
Benchmark results:
    K=4: 5/5 pass · avg conf=97.9% · avg fup boost=+1.5pp (too high, no headroom)
    K=6: 5/5 pass · avg conf=92.9% · avg fup boost=+4.0pp (✓ selected)
    K=8: 5/5 pass · avg conf=86.6% · avg fup boost=+6.2pp (too conservative)

Supports follow-up refinement:
- confirmed_causes: list of cause_id that user confirmed via follow-up questions
  Each confirmed cause gets +bonus weight to push confidence up.
- answer adjustments: dict {cause_id: weight_delta} for fine-tuning.
"""
from __future__ import annotations
import math


class DiagnosisEngine:
    CONFIRM_BONUS = 5  # weight bonus per confirmed cause
    SATURATION_K = 6   # confidence curve constant — see module docstring

    def __init__(self, kb):
        self.kb = kb

    def matches_filter(self, motor_id, motor_filter, motor_type=None, motor_type_filter=None):
        """Check whether a relasi applies to a given motor.

        Filter layers (all must pass):
        1. motor_filter (list): explicit allowlist of motor IDs / wildcards.
           None or empty = matches all motors.
        2. motor_type_filter (str): engine type compatibility.
           Set on relasi when the cause is specific to a stroke count
           (e.g. "4_stroke" for klep-related causes that don't apply to
           2-tak engines). None = matches all engine types.

        Args:
            motor_id: target motor ID (or None for global).
            motor_filter: list from relasi.motor_filter (or None).
            motor_type: target motor's engine_type ("2_stroke"/"4_stroke"/None).
            motor_type_filter: str from relasi.motor_type_filter (or None).

        Returns True only if every active filter is satisfied.
        """
        # Backward compat: if no filters at all, global relasi
        if not motor_filter and not motor_type_filter:
            return True
        # motor_filter check
        if motor_filter:
            if not motor_id:
                return False
            matched = False
            for pattern in motor_filter:
                if pattern == motor_id:
                    matched = True
                    break
                if pattern.endswith("*") and motor_id.startswith(pattern[:-1]):
                    matched = True
                    break
                if pattern.startswith("*") and motor_id.endswith(pattern[1:]):
                    matched = True
                    break
            if not matched:
                return False
        # motor_type_filter check
        if motor_type_filter:
            if motor_type != motor_type_filter:
                return False
        return True

    def calc_confidence(self, score):
        """Saturating confidence: 1 - exp(-score / K).

        Properties:
        - score=0 → 0
        - score=4 → 1 - e^-1 ≈ 0.632
        - score=8 → 1 - e^-2 ≈ 0.865
        - score=12 → 1 - e^-3 ≈ 0.950
        - score=18 → 1 - e^-4.5 ≈ 0.989
        - score=24 → 1 - e^-6 ≈ 0.998
        """
        if score <= 0:
            return 0.0
        return 1.0 - math.exp(-score / self.SATURATION_K)

    def rank(
        self,
        symptom_ids,
        motor_id=None,
        confirmed_causes=None,
        answer_adjustments=None,
    ):
        """Aggregate relasi weights per cause, return ranked list.

        Args:
            symptom_ids: gejala IDs from parser + explicit
            motor_id: motor ID for filter + location
            confirmed_causes: cause IDs that user said 'Ya' to follow-up question
            answer_adjustments: {cause_id: weight_delta} for both yes/no effects
        """
        confirmed = set(confirmed_causes or [])
        adjustments = answer_adjustments or {}

        # Resolve target motor's engine_type for motor_type_filter checks
        motor_type = None
        if motor_id:
            motor_obj = self.kb.get_motor(motor_id)
            if motor_obj:
                motor_type = motor_obj.get("engine_type")

        cause_data = {}
        for sid in symptom_ids:
            for rel in self.kb.relasi:
                if rel["symptom_id"] != sid:
                    continue
                if not self.matches_filter(
                    motor_id,
                    rel.get("motor_filter"),
                    motor_type=motor_type,
                    motor_type_filter=rel.get("motor_type_filter"),
                ):
                    continue
                cid = rel["cause_id"]
                if cid not in cause_data:
                    cause_data[cid] = {
                        "score": 0,
                        "matched_symptoms": [],
                        "matched_relasi": [],
                        "confirmed": cid in confirmed,
                    }
                cause_data[cid]["score"] += rel["weight"]
                cause_data[cid]["matched_symptoms"].append(sid)
                cause_data[cid]["matched_relasi"].append(rel["id"])
                if "matched_relations_list" not in cause_data[cid]:
                    cause_data[cid]["matched_relations_list"] = []
                # Strip non-essential fields but keep verification metadata
                rel_clean = {
                    "id": rel["id"],
                    "symptom_id": rel["symptom_id"],
                    "cause_id": rel["cause_id"],
                    "weight": rel["weight"],
                    "verified": rel.get("verified", False),
                    "populated": rel.get("populated", False),
                    "source_type": rel.get("source_type", "unknown"),
                    "confidence": rel.get("confidence", "low"),
                }
                cause_data[cid]["matched_relations_list"].append(rel_clean)

        # Apply follow-up bonuses
        for cid in confirmed:
            if cid in cause_data:
                cause_data[cid]["score"] += self.CONFIRM_BONUS
            else:
                cause_data[cid] = {
                    "score": self.CONFIRM_BONUS,
                    "matched_symptoms": [],
                    "matched_relasi": [],
                    "confirmed": True,
                }

        # Apply per-cause adjustments (yes/no weight deltas)
        for cid, delta in adjustments.items():
            if cid in cause_data:
                cause_data[cid]["score"] += delta
            elif delta > 0:
                cause_data[cid] = {
                    "score": delta,
                    "matched_symptoms": [],
                    "matched_relasi": [],
                    "confirmed": False,
                }

        # Confidence uses the new saturating formula — no symptom-count dilution.
        ranked = sorted(
            [
                {
                    "cause_id": cid,
                    "score": max(0, data["score"]),
                    "confidence": self.calc_confidence(max(0, data["score"])),
                    "matched_symptoms": data["matched_symptoms"],
                    "matched_relasi": data["matched_relasi"],
                    "matched_relations_list": data.get("matched_relations_list", []),
                    "confirmed": data.get("confirmed", False),
                }
                for cid, data in cause_data.items()
            ],
            key=lambda x: (x["score"], x["confirmed"]),
            reverse=True,
        )
        return ranked
