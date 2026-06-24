"""Diagnoser — main entry point. Orchestrates parse → rank → gate → enrich."""
from __future__ import annotations
import re

from .kb import KnowledgeBase
from .parser import SymptomParser
from .inference import DiagnosisEngine
from .safety import gate, gate_with_disambiguation, enrich, summarize_locations


# Keywords that strongly suggest a non-carburetor (injection / fuel-injected) motor.
# These trigger a karbu-only warning. The user must know that Karbuin's data
# is sourced from carburetor motorcycles and may not apply to injection models.
KARBU_INCOMPATIBLE_KEYWORDS = [
    r"\binjeksi(?:si)?\b",     # "injeksi", "injeksian", etc.
    r"\bfi\b",                 # fuel injection (acronym)
    r"\befi\b",                # electronic fuel injection
    r"\binjection\b",
    r"\bsistem\s+injeksi\b",
    r"\bsuntik\b",             # slang for injection
    r"\bsuntikan\b",
    r"\bpgm[-\s]?fi\b",        # Honda PGM-FI
    r"\bvva\b",                # Variable Valve Actuation (often paired with FI)
]


def detect_karbu_incompatibility(user_input: str, motor_id: str | None) -> dict | None:
    """Scan free-text + motor_id for injection-related keywords.

    Returns:
        None if no concern found.
        dict with {detected, matched_keywords, message} otherwise.
    """
    text = (user_input or "").lower()
    matches: list[str] = []
    for pattern in KARBU_INCOMPATIBLE_KEYWORDS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            matches.append(m.group(0).strip())
    # Also check motor_id: if it contains 'injeksi', 'fi', or 'efi' as substring
    if motor_id:
        m_low = motor_id.lower()
        for kw in ("injeksi", "_fi", "-fi", "efi"):
            if kw in m_low:
                matches.append(f"motor_id:{motor_id}")
                break
    if not matches:
        return None
    return {
        "detected": True,
        "matched_keywords": list(dict.fromkeys(matches)),
        "message": (
            "Karbuin saat ini hanya mendukung motor karburator. "
            "Motor injeksi (FI/EFI/PGM-FI) menggunakan sistem bahan bakar yang berbeda "
            "(electronic fuel injection, sensor, ECU) dan tidak dapat didiagnosa dengan akurat "
            "oleh Karbuin. Untuk motor injeksi, silakan konsultasi ke bengkel resmi "
            "atau gunakan scanner OBD/ECU."
        ),
    }


class Diagnoser:
    def __init__(self, kb: KnowledgeBase):
        self.kb = kb
        self.parser = SymptomParser(kb)
        # v1.2.2: init synonym resolver + fuzzy matcher for v1.2 enhanced parse
        self.parser.init_v12()
        self.engine = DiagnosisEngine(kb)

    def diagnose(
        self,
        user_input: str = "",
        motor_id: str | None = None,
        explicit_symptoms: list[str] | None = None,
        confirmed_causes: list[str] | None = None,
        answer_adjustments: dict[str, int] | None = None,
    ) -> dict:
        """Full diagnosis pipeline.

        Args:
            user_input: free-text description from user
            motor_id: optional motor ID for filter + location lookup
            explicit_symptoms: optional list of symptom IDs (user pre-selected)
            confirmed_causes: cause IDs user confirmed via follow-up questions
            answer_adjustments: {cause_id: weight_delta} for both yes/no answers

        Returns:
            Structured diagnosis result with status, results, summary, etc.
        """
        # 1. Parse (v1.2.2: parse_v12 = alias + synonym groups + fuzzy + context)
        v12 = self.parser.parse_v12(user_input)
        parsed = [
            {
                "symptom_id": sid,
                "matched_phrase": phrase,
                "confidence": conf,
                "source": src,
            }
            for sid, conf, src, phrase in v12["matches"]
        ]
        parsed_ids = [p["symptom_id"] for p in parsed]
        explicit_ids = explicit_symptoms or []
        all_symptoms = list(dict.fromkeys(parsed_ids + explicit_ids))  # preserve order, dedupe

        # 2. Rank (with optional follow-up refinement)
        ranked = self.engine.rank(
            all_symptoms,
            motor_id,
            confirmed_causes=confirmed_causes,
            answer_adjustments=answer_adjustments,
        )

        # 3. Gate (v1.2.2: includes disambiguation check)
        g = gate_with_disambiguation(ranked)

        # 4. Build response
        response = {
            "motor_id": motor_id,
            "parsed_symptoms": parsed,
            "explicit_symptoms": explicit_ids,
            "all_symptoms": all_symptoms,
            "confirmed_causes": confirmed_causes or [],
            "is_followup": bool(confirmed_causes or answer_adjustments),
        }

        # 4.5. Karbu-only guard — warn user if input mentions injection / FI / EFI.
        karbu_warn = detect_karbu_incompatibility(user_input, motor_id)
        if karbu_warn:
            response["karbu_warning"] = karbu_warn

        if not g["safe"]:
            response["status"] = g["reason"]
            response["message"] = g["message"]
            response["partial_results"] = enrich(ranked[:3], self.kb, motor_id)
            # v1.2.2: if ambiguous_top_results, also return follow-up questions
            # from the top-2 candidates so the caller can re-run with
            # answer_adjustments. Use enriched partial_results so cause objects
            # are populated (collect_followups needs cause.name/id).
            if g["reason"] == "ambiguous_top_results":
                response["top_two"] = g["top_two"]
                response["delta"] = g["delta"]
                response["follow_up_questions"] = collect_followups(
                    response["partial_results"][:2]
                )
            return response

        # 5. Enrich top results
        results = enrich(ranked[:5], self.kb, motor_id)
        response["status"] = "ok"
        response["results"] = results
        response["location_summary"] = summarize_locations(motor_id, results)

        # 6. Build ringkasan (top-line summary for UI hero card)
        if results:
            top = results[0]
            response["ringkasan"] = build_ringkasan(top, motor_id, self.kb)
            response["summary"] = (
                f"{len(results)} penyebab teratas dianalisis. "
                f"Tertinggi: {top['cause']['name']} "
                f"({top['tier_label']}, {top['confidence']:.0%})."
            )
            # 7. Build follow-up question list from top 2 results
            response["follow_up_questions"] = collect_followups(results[:2])
        else:
            response["ringkasan"] = "Tidak ada penyebab yang bisa ditampilkan."
            response["summary"] = "Tidak ada penyebab yang bisa ditampilkan."
            response["follow_up_questions"] = []
        return response


def build_ringkasan(top: dict, motor_id: str | None, kb: KnowledgeBase) -> str:
    """Build the one-sentence top-line summary for the result hero.

    Example:
    'Kemungkinan terbesar adalah Filter Udara Kotor.
     Kerusakan ini umumnya menyebabkan brebet dan bensin boros.
     Biaya perbaikan berkisar Rp20.000–75.000 dan dapat
     dilakukan sendiri oleh pemula.'
    """
    cause = top["cause"]
    name = cause["name"]

    # Gejala description
    matched = top["matched_symptoms"]  # names from safety.enrich
    if matched:
        gejala_text = " dan ".join(matched[:2]) if len(matched) <= 2 else f"{matched[0]} dan {len(matched)-1} gejala lain"
    else:
        gejala_text = "gejala yang Anda sebutkan"

    # Cost
    prices = top.get("prices", [])
    cost_text = "biaya belum tersedia"
    if prices:
        min_p = min(p.get("part_price_min", 0) or 0 for p in prices)
        max_p = max(p.get("part_price_max", 0) or 0 for p in prices)
        # Add typical labor
        labor_min = min((p.get("labor_price_min", 0) or 0) for p in prices)
        labor_max = max((p.get("labor_price_max", 0) or 0) for p in prices)
        if min_p and max_p:
            low = min_p + (labor_min or 0)
            high = max_p + (labor_max or 0)
            if high > 0:
                cost_text = f"Biaya perbaikan berkisar Rp{low:,.0f}–Rp{high:,.0f}".replace(",", ".")

    # DIY level
    diy = cause.get("diy_level", "menengah")
    diy_text = {
        "pemula": "dapat dilakukan sendiri oleh pemula",
        "menengah": "perlu keterampilan tingkat menengah",
        "mekanik": "sebaiknya dibawa ke mekanik",
    }.get(diy, "perlu bantuan mekanik")

    sentences = [
        f"Kemungkinan terbesar adalah {name}.",
        f"Kerusakan ini umumnya menyebabkan {gejala_text}.",
        f"{cost_text} dan {diy_text}.",
    ]
    return " ".join(sentences)


def collect_followups(top_results: list[dict]) -> list[dict]:
    """Collect follow-up questions from top 2 results.

    Returns list of {question_id, cause_id, question, yes_weight_bonus, no_weight_penalty}
    """
    out = []
    seen = set()
    for r in top_results:
        cause = r["cause"]
        for q in cause.get("follow_up_questions", []):
            if q["id"] in seen:
                continue
            seen.add(q["id"])
            out.append({
                "question_id": q["id"],
                "cause_id": cause["id"],
                "cause_name": cause["name"],
                "question": q["question"],
                "yes_weight_bonus": q.get("yes_weight_bonus", 0),
                "no_weight_penalty": q.get("no_weight_penalty", 0),
            })
    return out[:3]  # max 3 follow-up questions at a time
