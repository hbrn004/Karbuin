"""Safety guards — no-hallucination gates + output enrichment.

CRITICAL: All guards here are MANDATORY before any result reaches the user.
Rule: "Data tidak cukup" > wrong diagnosis.
"""
from __future__ import annotations

from .confidence import classify_tier

CONFIDENCE_THRESHOLD = 0.60
MAX_RESULTS = 5


def gate(ranked: list[dict]) -> dict:
    """Decide whether diagnosis is safe to show.

    Returns:
        {'safe': bool, 'reason': str, 'message': str, ...}
    """
    if not ranked:
        return {
            "safe": False,
            "reason": "no_symptom_match",
            "message": (
                "Gejala yang Anda sebutkan tidak dikenali sistem. "
                "Coba jelaskan dengan bahasa lain, misal: 'motor brebet', "
                "'susah hidup pagi', 'bensin boros', 'langsam tinggi'."
            ),
        }
    if ranked[0]["confidence"] < CONFIDENCE_THRESHOLD:
        return {
            "safe": False,
            "reason": "confidence_too_low",
            "message": (
                "Data tidak cukup untuk diagnosis yang yakin. "
                "Tambahkan gejala lain atau pilih model motor spesifik "
                "untuk hasil lebih akurat."
            ),
            "top_confidence": ranked[0]["confidence"],
        }
    return {"safe": True}


def enrich(ranked: list[dict], kb, motor_id: str | None = None) -> list[dict]:
    """Enrich ranked causes with components, solutions, prices, images, locations.

    SAFETY RULES enforced here:
    - Causes without related_components are SKIPPED (no fabrication)
    - Images only included if verified
    - Locations only included if verified AND motor matches
    - Prices only included if exist (no estimation)
    """
    results = []
    for cause in ranked[:MAX_RESULTS]:
        cause_obj = kb.get_penyebab(cause["cause_id"])
        if not cause_obj:
            continue

        # SAFETY: causes must have related_components
        related = cause_obj.get("related_components", [])
        if not related:
            # Skip — cannot show cause without components
            continue

        # Components
        components = []
        for cid in related:
            c = kb.get_komponen(cid)
            if c:
                components.append(c)

        # Solutions tiered (free/budget/mid/full)
        solutions = {"free": [], "budget": [], "mid": [], "full": []}
        for sol in kb.get_solutions_for_cause(cause["cause_id"]):
            tier = sol.get("tier")
            if tier in solutions:
                solutions[tier].append(sol)

        # Prices (only if exist)
        prices = []
        for c in components:
            prices.extend(kb.get_prices_for_component(c["id"]))

        # Images (only verified)
        images = []
        for c in components:
            imgs = kb.get_images_for_component(c["id"], motor_id)
            if imgs:
                images.extend(imgs)

        # Locations (only verified for this motor)
        locations = []
        location_unverified_components = []
        if motor_id:
            for c in components:
                loc = kb.get_location(motor_id, c["id"])
                if loc:
                    # Normalize time field for API consumers
                    if "time_estimate_min" in loc and "estimated_time_minutes" not in loc:
                        loc["estimated_time_minutes"] = loc.get("time_estimate_min")
                    locations.append(loc)
                else:
                    location_unverified_components.append(c["id"])

        # Reasoning (explain why this cause scored high)
        matched_names = []
        matched_relations = []
        for sid in cause["matched_symptoms"]:
            g = kb.get_gejala(sid)
            if g:
                matched_names.append(g["name"])
            # Phase 1.6: collect matched relasi for VERIFIED/POPULATED badge
            for r in cause.get("matched_relations_list", []):
                if r["symptom_id"] == sid:
                    matched_relations.append({
                        "symptom_id": sid,
                        "cause_id": cause_obj["id"],
                        "weight": r["weight"],
                        "verified": r.get("verified", False),
                        "populated": r.get("populated", False),
                        "source_type": r.get("source_type", "unknown"),
                        "confidence": r.get("confidence", "low"),
                    })
        # Scale "max possible" to a sensible target for display: 2x highest
        # observed score, or 20, whichever is higher. The new confidence
        # formula is saturating (no fixed max), so we synthesize a display
        # denominator that always shows the cause as the strongest.
        observed_top = max((c["score"] for c in ranked), default=0) or 1
        display_max = max(20, observed_top + 5)
        reasoning = (
            f"Dari {len(cause['matched_symptoms'])} gejala yang cocok "
            f"({', '.join(matched_names)}), penyebab \"{cause_obj['name']}\" "
            f"mendapat skor {cause['score']}/{display_max} "
            f"(confidence {cause['confidence']:.0%})."
        )

        # DIY level
        diy_level = cause_obj.get("diy_level", "menengah")
        diy_label = {
            "pemula": "Pemula",
            "menengah": "Menengah",
            "mekanik": "Mekanik",
        }.get(diy_level, "Menengah")

        # Risk level
        risk_level = cause_obj.get("risk_level", "low")
        risk_label = {
            "low": "Aman dipakai",
            "medium": "Sebaiknya diperbaiki",
            "high": "Jangan digunakan",
        }.get(risk_level, "Aman dipakai")

        # Estimated time
        est_minutes = cause_obj.get("estimated_minutes", 60)
        if est_minutes < 60:
            time_text = f"{est_minutes} menit"
        elif est_minutes < 1440:
            hours = est_minutes / 60
            time_text = f"{hours:.0f} jam" if hours == int(hours) else f"{hours:.1f} jam"
        else:
            days = est_minutes / 1440
            time_text = f"{days:.0f} hari"

        # Display denominator — see reasoning block above.
        # Use max(20, top_score + 5) so cause always appears strongest.
        observed_top = max((c["score"] for c in ranked), default=0) or 1
        display_max = max(20, observed_top + 5)
        results.append({
            "cause": cause_obj,
            "score": cause["score"],
            "max_possible": display_max,
            "confidence": cause["confidence"],
            "tier_label": classify_tier(cause["confidence"]),
            "matched_symptoms": matched_names,
            "matched_relations": matched_relations,
            "components": components,
            "solutions": solutions,
            "prices": prices,
            "images": images,
            "locations": locations,
            "location_unverified_components": location_unverified_components,
            "reasoning": reasoning,
            "risk_level": risk_level,
            "risk_label": risk_label,
            "diy_level": diy_level,
            "diy_label": diy_label,
            "estimated_minutes": est_minutes,
            "time_text": time_text,
            "confirmed": cause.get("confirmed", False),
            "follow_up_questions": [
                {**q, "cause_id": cause_obj["id"], "cause_name": cause_obj["name"]}
                for q in cause_obj.get("follow_up_questions", [])
            ],
        })

    return results


def summarize_locations(motor_id: str | None, results: list[dict]) -> dict:
    """Build summary of location verification status."""
    if not motor_id:
        return {
            "motor_selected": False,
            "verified_count": 0,
            "unverified_count": 0,
            "message": "Model motor tidak dipilih — lokasi spesifik tidak ditampilkan.",
        }
    verified = 0
    unverified = 0
    for r in results:
        verified += len(r.get("locations", []))
        unverified += len(r.get("location_unverified_components", []))
    return {
        "motor_selected": True,
        "motor_id": motor_id,
        "verified_count": verified,
        "unverified_count": unverified,
        "message": (
            f"Lokasi terverifikasi untuk {verified} komponen pada motor ini. "
            f"{unverified} komponen belum terverifikasi — "
            f"ditampilkan dengan label 'belum diverifikasi'."
            if unverified
            else f"Semua lokasi terverifikasi untuk motor ini."
        ),
    }