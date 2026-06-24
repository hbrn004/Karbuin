"""Coverage report — stats on knowledge base completeness."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from karbuin import KnowledgeBase


def main():
    project_root = Path(__file__).resolve().parent.parent
    seed_dir = project_root / "data" / "seed"
    kb = KnowledgeBase(seed_dir)
    stats = kb.coverage_stats()

    print("=" * 78)
    print("KARBUIN — KNOWLEDGE BASE COVERAGE REPORT")
    print("=" * 78)
    print()
    print(f"[CORE ENTITIES]")
    print(f"  Motor           : {stats['motor']:>3}")
    print(f"  Komponen        : {stats['komponen']:>3}")
    print(f"  Gejala          : {stats['gejala']:>3}")
    print(f"  Penyebab        : {stats['penyebab']:>3}")
    print(f"  Relasi          : {stats['relasi']:>3}  (verified: {stats['relasi_verified']:>3} | "
          f"unverified: {stats['relasi'] - stats['relasi_verified']:>3})")
    print()
    print(f"[KNOWLEDGE ARTIFACTS]")
    print(f"  Solusi          : {stats['solusi']:>3}")
    print(f"  Harga           : {stats['harga']:>3}  (verified: {stats['harga_verified']:>3})")
    print(f"  Lokasi komponen : {stats['lokasi_total']:>3}  (verified: {stats['lokasi_verified']:>3} | "
          f"unverified: {stats['lokasi_total'] - stats['lokasi_verified']:>3})")
    print(f"  Image component : {stats['image_total']:>3}  (verified: {stats['image_verified']:>3})")
    print(f"  Sumber ref      : {stats['sumber_referensi']:>3}")
    print()

    # Verification rates
    print(f"[VERIFICATION RATES]")
    relasi_rate = stats['relasi_verified'] / stats['relasi'] * 100
    lokasi_rate = stats['lokasi_verified'] / stats['lokasi_total'] * 100 if stats['lokasi_total'] else 0
    image_rate = stats['image_verified'] / stats['image_total'] * 100 if stats['image_total'] else 0
    print(f"  Relasi          : {relasi_rate:>5.1f}% verified")
    print(f"  Lokasi          : {lokasi_rate:>5.1f}% verified  ⚠ KRITIS — lokasi tidak boleh ditampilkan jika unverified")
    print(f"  Image           : {image_rate:>5.1f}% verified")
    print()

    # Per-motor coverage
    print(f"[PER-MOTOR COVERAGE]")
    print(f"  {'Motor':<25} {'Causes':>8} {'Lokasi v/total':>16}")
    print(f"  {'-'*25} {'-'*8} {'-'*16}")
    for mid, info in stats["motor_coverage"].items():
        loc_str = f"{info['verified_lokasi']}/{info['total_lokasi']}"
        print(f"  {info['model']:<25} {info['reachable_causes']:>8} {loc_str:>16}")
    print()

    # === Missing data summary ===
    print(f"[DATA YANG MASIH KOSONG / PERLU VERIFIKASI]")
    print()

    # 1. Unverified locations
    print(f"  ⚠ Lokasi belum terverifikasi: {stats['lokasi_total'] - stats['lokasi_verified']} entries")
    print(f"    → semua lokasi di seed saat ini verified=false")
    print(f"    → perlu input mekanik / foto asli + validasi")
    print()

    # 2. Image kosong
    print(f"  ⚠ Image component verified: 0/{stats['image_total']}")
    print(f"    → registry sudah ada tapi image_url semua null")
    print(f"    → perlu foto original + hosting + set verified=true")
    print()

    # 3. Harga verified
    if stats['harga_verified'] < stats['harga']:
        print(f"  ⚠ Harga belum verified: {stats['harga'] - stats['harga_verified']}/{stats['harga']} entries")
        print(f"    → range sudah ada (national_range) tapi verified=false")
        print(f"    → perlu cross-check dengan survey bengkel")
    print()

    # 4. Penyebab tanpa komponen
    no_comp = []
    for p in kb.penyebab:
        if not p.get("related_components"):
            no_comp.append(p["id"])
    if no_comp:
        print(f"  ⚠ Penyebab tanpa related_components: {len(no_comp)}")
        for cid in no_comp:
            print(f"    - {cid}")
        print(f"    → engine akan skip penyebab ini (safety)")
        print(f"    → perlu tambahkan komponen atau tandai sebagai out-of-scope")
    print()

    # 5. Komponen tanpa lokasi untuk motor manapun
    components_with_lokasi = {loc["component_id"] for loc in kb.lokasi_komponen}
    components_no_lokasi = [k["id"] for k in kb.komponen if k["id"] not in components_with_lokasi]
    if components_no_lokasi:
        print(f"  ⚠ Komponen tanpa data lokasi sama sekali: {len(components_no_lokasi)}")
        for cid in components_no_lokasi:
            print(f"    - {cid}")
        print(f"    → untuk komponen ini, lokasi spesifik motor TIDAK BISA ditampilkan")
        print(f"    → perlu tambah entry lokasi per motor × komponen ini")
    print()

    # 6. Gejala tanpa penyebab
    gejala_with_relasi = {r["symptom_id"] for r in kb.relasi}
    gejala_no_relasi = [g["id"] for g in kb.gejala if g["id"] not in gejala_with_relasi]
    if gejala_no_relasi:
        print(f"  ⚠ Gejala tanpa relasi penyebab: {len(gejala_no_relasi)}")
        for gid in gejala_no_relasi:
            print(f"    - {gid}")
    print()

    # 7. Penyebab tanpa relasi
    penyebab_with_relasi = {r["cause_id"] for r in kb.relasi}
    penyebab_no_relasi = [p["id"] for p in kb.penyebab if p["id"] not in penyebab_with_relasi]
    if penyebab_no_relasi:
        print(f"  ⚠ Penyebab tanpa relasi gejala: {len(penyebab_no_relasi)}")
        for cid in penyebab_no_relasi:
            print(f"    - {cid}")
        print(f"    → penyebab ini tidak akan pernah muncul di diagnosis")
        print(f"    → perlu tambah relasi gejala → penyebab ini")
    print()

    # 8. Motor tanpa lokasi sama sekali
    motors_with_lokasi = {loc["motor_id"] for loc in kb.lokasi_komponen}
    motors_no_lokasi = [m["id"] for m in kb.motor if m["id"] not in motors_with_lokasi]
    if motors_no_lokasi:
        print(f"  ⚠ Motor tanpa data lokasi sama sekali: {len(motors_no_lokasi)}")
        for mid in motors_no_lokasi:
            motor_name = next(m["model"] for m in kb.motor if m["id"] == mid)
            print(f"    - {mid} ({motor_name})")
        print(f"    → untuk motor ini, TIDAK ADA lokasi spesifik yang bisa ditampilkan")
        print(f"    → perlu tambah entry lokasi untuk motor × komponen penting")
    print()


if __name__ == "__main__":
    main()