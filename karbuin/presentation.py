"""karbuin/presentation.py — User-facing presentation layer for diagnosis results.

PURE presentation wrapper — does NOT modify the diagnosis engine.
Adds:
- top_3: top 3 causes with confidence percentages
- checklist: inspection steps extracted from components
- summary_card: human-friendly one-line summary
- human_tier: confidence → human label

Usage in server.py:
    from karbuin.presentation import build_presentation
    result["presentation"] = build_presentation(result)
"""
from __future__ import annotations
from typing import Any


def _confidence_pct(conf: float) -> str:
    """Format confidence as human-friendly percentage string."""
    return f"{round(conf * 100)}%"


def _human_tier(confidence: float) -> str:
    """Map confidence to a human-readable tier label."""
    if confidence >= 0.85:
        return "Sangat mungkin"
    if confidence >= 0.70:
        return "Kemungkinan tinggi"
    if confidence >= 0.50:
        return "Kemungkinan sedang"
    if confidence >= 0.30:
        return "Kemungkinan rendah"
    return "Sangat rendah"


def build_top_3(results: list[dict], cause_lookup=None) -> list[dict]:
    """Extract top 3 diagnoses as a flat, user-friendly list.

    Handles two input formats:
    1. Rich result dict: {cause: {id, name, ...}, confidence, ...}
    2. Flat top_two dict: {cause_id, confidence}  (from ambiguous_top_results)

    If cause_lookup callable is provided, the flat format will be enriched
    with the full cause record from the KB.
    """
    top = []
    for i, r in enumerate(results[:3], start=1):
        if "cause" in r and isinstance(r.get("cause"), dict):
            # Rich format
            cause = r["cause"] or {}
            cause_id = cause.get("id")
            cause_name = cause.get("name", "")
            category = cause.get("category", "")
            risk_label = r.get("risk_label", "")
            diy_label = r.get("diy_label", "")
            time_text = r.get("time_text", "")
        elif "cause_id" in r:
            # Flat format (ambiguous_top_results)
            cause_id = r.get("cause_id")
            cause_name = cause_id or ""
            category = ""
            risk_label = ""
            diy_label = ""
            time_text = ""
            # Enrich via lookup if provided
            if cause_lookup and cause_id:
                full_cause = cause_lookup(cause_id)
                if full_cause:
                    cause_name = full_cause.get("name", cause_id)
                    category = full_cause.get("category", "")
        else:
            continue

        confidence = r.get("confidence", 0.0)
        top.append({
            "rank": i,
            "cause_id": cause_id,
            "cause_name": cause_name,
            "category": category,
            "confidence": confidence,
            "confidence_pct": _confidence_pct(confidence),
            "tier_label": _human_tier(confidence),
            "severity": risk_label,
            "diy": diy_label,
            "time": time_text,
        })
    return top


def _resolve_ranked_list(result: dict) -> list[dict]:
    """Resolve the ranked causes list from result.

    For 'ok' / 'ambiguous' / 'low_confidence' → use 'results'.
    For 'ambiguous_top_results' → use 'top_two' (engine uses this when
        top 2 are too close to call).
    For 'no_symptom_match' / unknown → empty list.
    """
    status = result.get("status", "")
    if status == "ambiguous_top_results":
        return result.get("top_two", []) or []
    return result.get("results", []) or []


def build_checklist(results: list[dict], top_n: int = 3) -> list[dict]:
    """Generate inspection checklist from top causes' components.

    Each component carries an inspection_method field. We collect
    unique components across the top N causes and emit them as
    a deduplicated checklist with priority (cause rank).
    """
    checklist: list[dict] = []
    seen_component_ids: set[str] = set()
    for i, r in enumerate(results[:top_n], start=1):
        cause = r.get("cause", {}) or {}
        cause_id = cause.get("id", "")
        for comp in r.get("components", []) or []:
            cid = comp.get("id")
            if not cid or cid in seen_component_ids:
                continue
            seen_component_ids.add(cid)
            method = comp.get("inspection_method", "") or comp.get("description", "")
            if not method:
                continue
            checklist.append({
                "step": method,
                "component_id": cid,
                "component_name": comp.get("name", ""),
                "tools_needed": comp.get("tools_needed", []) or [],
                "difficulty": comp.get("inspection_difficulty", "medium"),
                "related_cause": cause_id,
                "cause_rank": i,
            })
    return checklist


def _resolve_cause_id(r: dict) -> str:
    """Extract cause_id from either rich or flat dict format."""
    if "cause" in r and isinstance(r.get("cause"), dict):
        return (r["cause"] or {}).get("id", "")
    return r.get("cause_id", "")


def build_summary_card(result: dict, motor_id: str | None = None, cause_lookup=None) -> dict:
    """Build a human-friendly summary card for the diagnose result."""
    status = result.get("status", "unknown")
    ranked = _resolve_ranked_list(result)
    n_results = len(ranked)
    top = ranked[0] if ranked else None

    def _cause_name(cause_id: str) -> str:
        if cause_lookup and cause_id:
            full = cause_lookup(cause_id)
            if full and full.get("name"):
                return full["name"]
        return cause_id or "?"

    if status == "ok" and top:
        top_id = _resolve_cause_id(top)
        top_name = _cause_name(top_id)
        top_pct = _confidence_pct(top.get("confidence", 0.0))
        return {
            "headline": f"{top_name} — {top_pct}",
            "subline": f"Diagnosis utama berdasarkan {len(top.get('matched_symptoms', []))} gejala cocok",
            "total_alternatives": max(n_results - 1, 0),
        }
    if status in ("ambiguous", "ambiguous_top_results"):
        names = [_cause_name(_resolve_cause_id(r)) for r in ranked[:2]]
        if len(names) >= 2:
            return {
                "headline": f"2 penyebab mirip: {' vs '.join(names)}",
                "subline": "Perlu info tambahan untuk menentukan penyebab utama",
                "total_alternatives": max(n_results - 2, 0),
            }
        return {
            "headline": "Diagnosis belum pasti",
            "subline": "Sistem perlu klarifikasi lebih lanjut",
            "total_alternatives": n_results,
        }
    if status == "low_confidence":
        return {
            "headline": "Penyebab belum pasti",
            "subline": "Gejala dikenali tapi penyebab utama confidence rendah",
            "total_alternatives": n_results,
        }
    if status == "no_symptom_match":
        msg = result.get("message", "")
        return {
            "headline": "Gejala belum dikenali",
            "subline": msg or "Coba jelaskan dengan bahasa lain",
            "total_alternatives": 0,
        }
    return {
        "headline": status,
        "subline": "",
        "total_alternatives": n_results,
    }


def build_presentation(result: dict, motor_id: str | None = None, cause_lookup=None) -> dict:
    """Top-level wrapper: enrich engine result with presentation fields.

    Returns a new dict with all original fields preserved plus
    a `presentation` key holding top_3, checklist, summary_card.

    Args:
        result: Engine diagnose() result.
        motor_id: Optional motor context.
        cause_lookup: Optional callable(cause_id) -> cause dict.
            If None, flat-format causes (ambiguous_top_results) will only
            show cause_id without human-friendly name.
    """
    ranked = _resolve_ranked_list(result)
    return {
        "summary_card": build_summary_card(result, motor_id, cause_lookup=cause_lookup),
        "top_3": build_top_3(ranked, cause_lookup=cause_lookup),
        "checklist": build_checklist(ranked, top_n=3),
        "total_results": len(ranked),
    }


__all__ = [
    "build_presentation",
    "build_top_3",
    "build_checklist",
    "build_summary_card",
    "_confidence_pct",
    "_human_tier",
]
