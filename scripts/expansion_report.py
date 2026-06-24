"""Expansion report — Phase 1.5 metrics.

Shows:
- Top 20 gejala paling umum (by relasi count)
- Top 20 penyebab paling umum (by total weight in relasi)
- Coverage lokasi per motor (X/11 focus components)
- Coverage gambar per motor (X/11 focus components)
- Alias coverage stats
- Phase 1.5 target completion status
"""
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from karbuin import KnowledgeBase
from karbuin.parser import SymptomParser


# 11 focus components per Phase 1.5 user instruction
FOCUS_COMPONENTS = {
    "karburator", "pilot_jet", "main_jet", "intake_manifold", "busi",
    "koil", "cdi", "filter_udara", "kran_bensin", "selang_bensin", "ring_piston"
}


def main():
    project_root = Path(__file__).resolve().parent.parent
    seed_dir = project_root / "data" / "seed"
    kb = KnowledgeBase(seed_dir)
    kb.parser = SymptomParser(kb)  # for parser coverage test
    stats = kb.coverage_stats()

    print("=" * 78)
    print("KARBUIN — EXPANSION REPORT (Phase 1.5)")
    print("=" * 78)
    print()

    # ========== TARGET COMPLETION ==========
    print("[PHASE 1.5 TARGETS]")
    lokasi_pct = stats['lokasi_verified'] / stats['lokasi_total'] * 100 if stats['lokasi_total'] else 0
    image_pct = stats['image_verified'] / stats['image_total'] * 100 if stats['image_total'] else 0
    harga_pct = stats['harga_verified'] / stats['harga'] * 100 if stats['harga'] else 0

    def status_emoji(actual, target=70):
        return "✅" if actual >= target else "❌"

    print(f"  Lokasi verified   : {stats['lokasi_verified']}/{stats['lokasi_total']} = {lokasi_pct:5.1f}%  target 70%  {status_emoji(lokasi_pct)}")
    print(f"  Image verified    : {stats['image_verified']}/{stats['image_total']} = {image_pct:5.1f}%  target 70%  {status_emoji(image_pct)}")
    print(f"  Harga verified    : {stats['harga_verified']}/{stats['harga']} = {harga_pct:5.1f}%  target 70%  {status_emoji(harga_pct)}")
    print()

    # ========== ENTITY COUNTS ==========
    print("[ENTITY COUNTS]")
    print(f"  Motor           : {stats['motor']:>3}")
    print(f"  Komponen        : {stats['komponen']:>3}")
    print(f"  Gejala          : {stats['gejala']:>3}")
    print(f"  Penyebab        : {stats['penyebab']:>3}")
    print(f"  Relasi          : {stats['relasi']:>3}  (verified: {stats['relasi_verified']:>3})")
    print(f"  Solusi          : {stats['solusi']:>3}")
    print()

    # ========== ALIAS STATS ==========
    print("[ALIAS COVERAGE]")
    total_aliases = sum(len(g.get("aliases", [])) for g in kb.gejala)
    print(f"  Total alias gejala  : {total_aliases}")
    print(f"  Avg per gejala      : {total_aliases/len(kb.gejala):.1f}")
    print(f"  Gejala w/ no alias  : {sum(1 for g in kb.gejala if not g.get('aliases'))}")
    print()

    # ========== TOP 20 GEJALA by relasi count ==========
    print("[TOP 20 GEJALA — paling umum (by relasi count)]")
    gejala_count = defaultdict(int)
    gejala_total_weight = defaultdict(int)
    for r in kb.relasi:
        gejala_count[r["symptom_id"]] += 1
        gejala_total_weight[r["symptom_id"]] += r["weight"]

    top_gejala = sorted(gejala_count.items(), key=lambda x: x[1], reverse=True)[:20]
    print(f"  {'Rank':<6} {'ID':<25} {'Name':<25} {'#Relasi':>8} {'ΣWeight':>9} {'Aliases':>9}")
    print(f"  {'-'*6} {'-'*25} {'-'*25} {'-'*8} {'-'*9} {'-'*9}")
    for i, (gid, cnt) in enumerate(top_gejala, 1):
        g = kb.get_gejala(gid)
        name = g["name"] if g else "?"
        aliases = len(g.get("aliases", [])) if g else 0
        w = gejala_total_weight[gid]
        print(f"  {i:<6} {gid:<25} {name:<25} {cnt:>8} {w:>9} {aliases:>9}")
    print()

    # ========== TOP 20 PENYEBAB by relasi weight ==========
    print("[TOP 20 PENYEBAB — paling umum (by Σ weight in relasi)]")
    penyebab_count = defaultdict(int)
    penyebab_total_weight = defaultdict(int)
    for r in kb.relasi:
        penyebab_count[r["cause_id"]] += 1
        penyebab_total_weight[r["cause_id"]] += r["weight"]

    top_penyebab = sorted(penyebab_total_weight.items(), key=lambda x: x[1], reverse=True)[:20]
    print(f"  {'Rank':<6} {'ID':<25} {'Name':<25} {'#Relasi':>8} {'ΣWeight':>9}")
    print(f"  {'-'*6} {'-'*25} {'-'*25} {'-'*8} {'-'*9}")
    for i, (cid, w) in enumerate(top_penyebab, 1):
        p = kb.get_penyebab(cid)
        name = p["name"] if p else "?"
        cnt = penyebab_count[cid]
        print(f"  {i:<6} {cid:<25} {name[:25]:<25} {cnt:>8} {w:>9}")
    print()

    # ========== LOKASI COVERAGE PER MOTOR ==========
    print("[COVERAGE LOKASI PER MOTOR — focus components only]")
    print(f"  Target: 11/11 = 100% (semua focus components punya lokasi verified per motor)")
    print()
    print(f"  {'Motor':<25} {'Lokasi v/total':>16} {'%':>7}  Status")
    print(f"  {'-'*25} {'-'*16} {'-'*7}  ------")
    for motor in kb.motor:
        mid = motor["id"]
        # Count focus components that have verified location for this motor
        verified_count = 0
        for comp_id in FOCUS_COMPONENTS:
            for loc in kb.lokasi_komponen:
                if loc["motor_id"] == mid and loc["component_id"] == comp_id and loc["verified"]:
                    verified_count += 1
                    break
        total = len(FOCUS_COMPONENTS)
        pct = verified_count / total * 100
        status = "✅" if verified_count == total else ("⚠" if verified_count >= total * 0.7 else "❌")
        print(f"  {motor['model']:<25} {verified_count:>6}/{total:<6} {pct:>6.1f}%  {status}")
    print()

    # ========== IMAGE COVERAGE PER MOTOR ==========
    print("[COVERAGE GAMBAR PER MOTOR — focus components only]")
    print(f"  Target: lokasi (location) image verified ≥ 1 per focus component per motor")
    print()
    print(f"  {'Motor':<25} {'Image v/total':>16} {'%':>7}  Status")
    print(f"  {'-'*25} {'-'*16} {'-'*7}  ------")
    for motor in kb.motor:
        mid = motor["id"]
        # Count focus components that have at least 1 verified location image for this motor
        verified_count = 0
        for comp_id in FOCUS_COMPONENTS:
            for img in kb.image_component:
                if (img.get("motor_specific") == mid
                    and img["component_id"] == comp_id
                    and img["image_type"] == "location"
                    and img["verified"]):
                    verified_count += 1
                    break
        total = len(FOCUS_COMPONENTS)
        pct = verified_count / total * 100
        status = "✅" if verified_count == total else ("⚠" if verified_count >= total * 0.7 else "❌")
        print(f"  {motor['model']:<25} {verified_count:>6}/{total:<6} {pct:>6.1f}%  {status}")
    print()

    # ========== PARSER COVERAGE (alias match tests) ==========
    print("[PARSER COVERAGE TEST — common phrasings]")
    test_phrases = [
        "motor brebet trus bensin boros banget",
        "pagi gak mau nyala tapi siang nyala normal",
        "bunyi tek tek di kepala silinder",
        "asap putih tebal banget",
        "starter berat susah diengkol",
        "aki tekor lampu redup",
        "oli cepat habis dan berkurang terus",
        "motor ngempos ga kuat nanjak",
        "langsam tinggi rpm gak turun",
        "nembak knalpot",
    ]
    print(f"  {'Phrase':<55} {'Matched'}")
    print(f"  {'-'*55} {'-'*30}")
    for phrase in test_phrases:
        matched = kb.parser.parse_with_details(phrase)
        if matched:
            ids = ", ".join(m["symptom_id"] for m in matched)
            print(f"  {phrase:<55} ✓ {ids}")
        else:
            print(f"  {phrase:<55} ✗ NO MATCH")
    print()

    # ========== SAFETY VERIFY ==========
    print("[SAFETY VERIFY — penyebab with related_components]")
    no_comp = [p["id"] for p in kb.penyebab if not p.get("related_components")]
    if no_comp:
        print(f"  ⚠ Penyebab tanpa related_components: {no_comp}")
        print(f"    Engine akan skip penyebab ini (safety) — perlu tambahkan komponen")
    else:
        print(f"  ✅ Semua penyebab punya related_components (no safety skip)")
    print()


if __name__ == "__main__":
    main()