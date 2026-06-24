"""Sample diagnosis — demonstrates 3 scenarios:
  1. High-confidence multi-gejala diagnosis (motor brebet + bensin boros)
  2. Low-confidence / "data tidak cukup" (vague input)
  3. Unverified location handling (motor-specific but lokasi belum verified)
"""
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from karbuin import KnowledgeBase, Diagnoser


def pretty(result: dict, scenario: str):
    """Format result dict for readable display."""
    lines = []
    lines.append("=" * 78)
    lines.append(f"SCENARIO: {scenario}")
    lines.append("=" * 78)
    lines.append(f"Motor: {result.get('motor_id') or '(tidak dipilih)'}")
    lines.append("")

    # Parsed symptoms
    if result.get("parsed_symptoms"):
        lines.append(f"[PARSED SYMPTOMS]")
        for p in result["parsed_symptoms"]:
            lines.append(f"  - {p['symptom_id']:<25} matched: \"{p['matched_phrase']}\" (conf {p['confidence']:.2f})")
        lines.append("")

    lines.append(f"[STATUS] {result['status']}")
    if "message" in result:
        lines.append(f"[MESSAGE] {result['message']}")
    if "summary" in result:
        lines.append(f"[SUMMARY] {result['summary']}")
    lines.append("")

    # Results (or partial)
    results_key = "results" if result["status"] == "ok" else "partial_results"
    items = result.get(results_key, [])
    if not items:
        lines.append("[NO RESULTS]")
        return "\n".join(lines)

    for i, r in enumerate(items, 1):
        lines.append(f"--- Result #{i} ---")
        lines.append(f"Penyebab : {r['cause']['name']}")
        lines.append(f"Aliases  : {', '.join(r['cause'].get('aliases', []))}")
        lines.append(f"Score    : {r['score']}/{r['max_possible']}  Confidence: {r['confidence']:.0%}  → {r['tier_label']}")
        lines.append(f"Reasoning: {r['reasoning']}")
        lines.append("")
        lines.append(f"  Komponen dicurigai ({len(r['components'])}):")
        for c in r["components"]:
            lines.append(f"    • {c['name']} — {c['function']}")
            lines.append(f"      Cara cek: {c['inspection_method'][:80]}...")
            lines.append(f"      Alat: {', '.join(c.get('tools_needed', []))}")
        lines.append("")

        # Solutions tiered
        lines.append(f"  Solusi:")
        for tier in ["free", "budget", "mid", "full"]:
            sols = r["solutions"].get(tier, [])
            if sols:
                lines.append(f"    [{tier.upper()}]")
                for s in sols:
                    lines.append(f"      - {s['description'][:90]}...")
                    lines.append(f"        alat: {', '.join(s.get('tools_needed', []))} | "
                                 f"waktu: {s['time_estimate_min']}m | "
                                 f"success: {s['success_rate']:.0%}")
        lines.append("")

        # Prices
        if r["prices"]:
            lines.append(f"  Estimasi harga (national_range):")
            for p in r["prices"]:
                lines.append(f"    • {p['item_id']}: part Rp{p['part_price_min']:,}-Rp{p['part_price_max']:,} | "
                             f"jasa Rp{p['labor_price_min']:,}-Rp{p['labor_price_max']:,}")
        else:
            lines.append(f"  Estimasi harga: belum tersedia")
        lines.append("")

        # Images
        if r["images"]:
            lines.append(f"  Gambar komponen:")
            for img in r["images"]:
                motor_tag = f" ({img['motor_specific']})" if img.get("motor_specific") else " (generic)"
                url = img.get("image_url") or "[gambar belum tersedia]"
                lines.append(f"    • {img['image_type']}{motor_tag}: {url}")
        else:
            lines.append(f"  Gambar komponen: gambar belum tersedia")
        lines.append("")

        # Locations
        if result.get("motor_id"):
            if r["locations"]:
                lines.append(f"  Lokasi terverifikasi pada motor:")
                for loc in r["locations"]:
                    lines.append(f"    • [{loc['component_id']}] {loc['location_description']}")
                    lines.append(f"      Akses: {loc['access_method']}")
                    lines.append(f"      Alat: {', '.join(loc['tools_needed'])} | waktu: {loc['time_estimate_min']}m")
            if r["location_unverified_components"]:
                lines.append(f"  ⚠ Lokasi model spesifik belum terverifikasi untuk: "
                             f"{', '.join(r['location_unverified_components'])}")
                lines.append(f"    → menampilkan label \"Lokasi model spesifik belum terverifikasi\"")
        lines.append("")
        lines.append("")

    # Location summary
    if "location_summary" in result:
        ls = result["location_summary"]
        lines.append(f"[LOCATION SUMMARY] {ls['message']}")
        lines.append("")

    return "\n".join(lines)


def main():
    project_root = Path(__file__).resolve().parent.parent
    seed_dir = project_root / "data" / "seed"
    print(f"Loading KnowledgeBase from {seed_dir}...")
    kb = KnowledgeBase(seed_dir)
    print(f"  motor={len(kb.motor)} komponen={len(kb.komponen)} gejala={len(kb.gejala)} "
          f"penyebab={len(kb.penyebab)} relasi={len(kb.relasi)} solusi={len(kb.solusi)}\n")

    diagnoser = Diagnoser(kb)

    # ========== SCENARIO 1: High confidence ==========
    print(pretty(diagnoser.diagnose(
        user_input="motor brebet trus bensin boros banget",
        motor_id="honda_supra_x125_karbu",
    ), "1. High-Confidence (brebet + bensin boros → filter_udara_kotor)"))

    # ========== SCENARIO 2: Low confidence (vague input) ==========
    print(pretty(diagnoser.diagnose(
        user_input="motor bunyi tek tek pas pagi susah hidup",
        motor_id="honda_revo_karbu",
    ), "2. Multi-Gejala Starter Issue (bunyi tek tek + susah hidup pagi)"))

    # ========== SCENARIO 3: Data tidak cukup (vague) ==========
    print(pretty(diagnoser.diagnose(
        user_input="motor agak aneh",
        motor_id=None,
    ), "3. Low-Confidence / 'Data Tidak Cukup' (vague input)"))

    # ========== SCENARIO 4: Unverified location for motor-specific ==========
    # Honda Tiger 2000 with ring_piston_aus symptoms
    print(pretty(diagnoser.diagnose(
        user_input="asap putih tebal oli boros tenaga hilang",
        motor_id="honda_tiger_2000",
    ), "4. Tiger 2000 + Ring Piston Aus (motor-specific cause, lokasi unverified)"))


if __name__ == "__main__":
    main()