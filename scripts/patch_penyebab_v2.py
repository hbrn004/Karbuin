"""Patch penyebab.json — add risk_level + follow_up_questions."""
import json
from pathlib import Path

# Mapping based on mechanical reasoning + user feedback
RISK_MAP = {
    "filter_udara_kotor": "low",        # Aman dipakai, cuma brebet/boros
    "bensin_kotor": "low",              # Mesin masih hidup, gak maksimal
    "pilot_jet_clogged": "low",         # Low RPM only
    "main_jet_clogged": "low",          # High RPM only
    "busi_aus": "low",                  # Percikan lemah, masih hidup
    "busi_rusak": "medium",             # Bisa mati mendadak
    "karburator_overflow": "medium",    # Bisa flooding
    "intake_leak": "low",               # Cuma brebet
    "vacuum_bocor": "low",              # Cuma RPM fluktuatif
    "koil_lemah": "medium",             # Bisa mogok
    "kiprok_rusak": "medium",           # Aki tekor → mogok
    "aki_lemah": "medium",              # Mogok mendadak
    "kran_bensin_mampet": "low",        # Cuma pelan
    "kipas_rusak": "high",              # Overheat → jebol
    "overheat_cooling": "high",         # Overheat → jebol
    "ring_piston_aus": "high",          # Kompresi hilang, oli ruang bakar
    "klep_renggang": "medium",          # Tenaga hilang, makin parah
    "seal_klep_bocor": "medium",        # Oli terkontaminasi
    "cdi_rusak": "medium",              # Mogok mendadak
    "timing_kemas_terlambat": "low",    # Cuma tenaga hilang
}

# Follow-up questions for top 6 high-frequency causes
# Format: question, yes_effect (cause bonus), no_effect (cause penalty)
FOLLOWUP = {
    "filter_udara_kotor": [
        {
            "id": "fu_filter_visible",
            "question": "Apakah filter udara terlihat kotor atau tersumbat saat dibuka?",
            "yes_weight_bonus": 5,
            "no_weight_penalty": 3,
        },
        {
            "id": "fu_filter_recent_clean",
            "question": "Apakah filter udara sudah pernah dicuci atau diganti dalam 6 bulan terakhir?",
            "yes_weight_bonus": -4,   # recently cleaned → less likely
            "no_weight_bonus": 3,     # never cleaned → more likely
        },
    ],
    "aki_lemah": [
        {
            "id": "fu_aki_lamp_dim",
            "question": "Apakah lampu redup atau berkedip saat mesin idle?",
            "yes_weight_bonus": 4,
            "no_weight_penalty": 2,
        },
        {
            "id": "fu_aki_age",
            "question": "Apakah aki sudah berusia lebih dari 2 tahun?",
            "yes_weight_bonus": 3,
            "no_weight_penalty": 1,
        },
    ],
    "ring_piston_aus": [
        {
            "id": "fu_ring_oil_smoke",
            "question": "Apakah asap putih tebal keluar dari knalpot, terutama saat gas ditarik?",
            "yes_weight_bonus": 4,
            "no_weight_penalty": 3,
        },
        {
            "id": "fu_ring_oli_bertambah",
            "question": "Apakah oli mesin cepat habis dan perlu ditambah terus?",
            "yes_weight_bonus": 4,
            "no_weight_penalty": 2,
        },
    ],
    "intake_leak": [
        {
            "id": "fu_intake_carb_cleaner",
            "question": "Apakah RPM mesin berubah (naik atau turun) saat carb cleaner disemprot ke sambungan intake?",
            "yes_weight_bonus": 6,   # Very strong confirmation
            "no_weight_penalty": 3,
        },
    ],
    "main_jet_clogged": [
        {
            "id": "fu_main_jet_high_rpm",
            "question": "Apakah masalah HILANG saat langsam tapi MUNCUL saat gas ditarik (RPM tinggi)?",
            "yes_weight_bonus": 5,
            "no_weight_penalty": 2,
        },
    ],
    "cdi_rusak": [
        {
            "id": "fu_cdi_no_spark",
            "question": "Apakah sama sekali TIDAK ada percikan api di busi saat diengkol?",
            "yes_weight_bonus": 5,
            "no_weight_penalty": 3,
        },
    ],
}

# DIY level mapping based on difficulty
DIY_MAP = {
    # easy → pemula
    "filter_udara_kotor": "pemula",
    "bensin_kotor": "pemula",
    "pilot_jet_clogged": "pemula",
    "busi_aus": "pemula",
    "busi_rusak": "pemula",
    "intake_leak": "pemula",
    "vacuum_bocor": "pemula",
    "kiprok_rusak": "menengah",  # butuh multimeter
    "aki_lemah": "pemula",
    "kran_bensin_mampet": "pemula",
    "main_jet_clogged": "menengah",
    "karburator_overflow": "menengah",
    "koil_lemah": "menengah",
    "klep_renggang": "menengah",
    "seal_klep_bocor": "menengah",
    "timing_kemas_terlambat": "mekanik",
    "cdi_rusak": "mekanik",
    "kipas_rusak": "menengah",
    "overheat_cooling": "mekanik",
    "ring_piston_aus": "mekanik",
}

# Time estimate per cause (in minutes, includes diagnosis + fix)
TIME_MAP = {
    "filter_udara_kotor": 15,
    "bensin_kotor": 30,
    "pilot_jet_clogged": 45,
    "main_jet_clogged": 45,
    "busi_aus": 20,
    "busi_rusak": 15,
    "karburator_overflow": 60,
    "intake_leak": 30,
    "vacuum_bocor": 30,
    "koil_lemah": 45,
    "kiprok_rusak": 45,
    "aki_lemah": 30,
    "kran_bensin_mampet": 20,
    "kipas_rusak": 60,
    "overheat_cooling": 120,
    "ring_piston_aus": 480,    # 8 jam
    "klep_renggang": 60,
    "seal_klep_bocor": 240,    # 4 jam
    "cdi_rusak": 60,
    "timing_kemas_terlambat": 90,
}


def main():
    p = Path("/home/hebryn/projects/motorcycle-karbu-expert/data/seed/penyebab.json")
    data = json.loads(p.read_text(encoding="utf-8"))
    for cause in data:
        cid = cause["id"]
        cause["risk_level"] = RISK_MAP.get(cid, "low")
        cause["diy_level"] = DIY_MAP.get(cid, "menengah")
        cause["estimated_minutes"] = TIME_MAP.get(cid, 60)
        if cid in FOLLOWUP:
            cause["follow_up_questions"] = FOLLOWUP[cid]
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Patched {len(data)} penyebab with risk_level + diy_level + estimated_minutes + follow_up_questions")


if __name__ == "__main__":
    main()
