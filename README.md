# 🔧 Karbuin — Diagnosa Motor Karburator Sendiri

**Karbuin** adalah sistem diagnosa berbasis pengetahuan untuk motor karburator Indonesia. Bukan AI generik. Bukan diagnosa generik. Kurasi dari pengetahuan bengkel lokal, untuk motor-motor yang umum di jalan Indonesia.

> **Status**: MVP v1.0.0 (audited 2026-06-25). Engine v1 FROZEN.

## 🌟 Highlight

- **Bahasa bengkel**: "brebet", "nembak", "geyong", "diengkol", "tepok" — bahasa lokal, bukan istilah buku.
- **Confidence score**: Tahu pasti seberapa yakin — bukan tebak-tebakan.
- **4 tier solusi**: Gratis → Hemat → Ganti → Overhaul.
- **Lokasi spesifik per motor**: "Di rumah filter, di belakang karburator" — bukan lokasi generik.
- **Disambiguation follow-up**: 2-3 pertanyaan lanjutan bisa naikkan akurasi 80% → 95%.
- **Verifikasi manual**: Setiap lokasi, harga, dan penyebab melalui kurasi.

## 📊 Data Cakupan (Audit 2026-06-25)

| Dataset | Count |
|---|---|
| Motor | 8 (Honda 3, Yamaha 3, Suzuki 1, Kawasaki 1) |
| Komponen | 30 |
| Gejala (symptoms) | 25 |
| Penyebab (causes) | 32 |
| Relasi gejala→penyebab | 124 |
| Solusi (4 tier) | 96 |
| Harga part + jasa | 24 |
| Lokasi per motor | 163 |
| Image registry | 108 |

## 🎯 Akurasi (Test Pack 50 — synthetic + UAT 5 — verified)

- **UAT 5/5 PASS** (verified)
- **Test Pack 50**: 40/50 PASS direct, 44/50 effective (with disambiguation follow-up)
- **Ambiguous rate**: 10%
- **FAIL rate**: 0%

## 🏗️ Arsitektur

- **Stack**: Python stdlib (http.server) + Vanilla JS + HTML + CSS + JSON data
- **No npm. No pip. No bundler.** Bisa dijalankan di WSL/Linux/Mac tanpa install apa pun.
- **Single binary**: `server.py` serve static + API.
- **No database**: data di JSON files.

## 🚀 Cara Menjalankan (Local)

```bash
cd /home/hebryn/projects/motorcycle-karbu-expert
python3 server.py --port 8000
```

Akses:
- `http://localhost:8000/` — Beranda
- `http://localhost:8000/diagnose` — Halaman diagnosa
- `http://localhost:8000/result?motor=...&input=...` — Hasil
- `http://localhost:8000/library` — Library komponen
- `http://localhost:8000/method` — Metode & confidence

## 📁 Struktur

```
motorcycle-karbu-expert/
├── server.py               # HTTP server (stdlib)
├── karbuin/                # Engine
│   ├── kb.py               # Knowledge Base loader
│   ├── parser.py           # Free-text → gejala (substring + alias)
│   ├── inference.py        # Ranker + K=6 confidence formula
│   ├── confidence.py       # Saturating formula
│   ├── safety.py           # Output enricher + filters
│   └── diagnose.py         # High-level wrapper
├── data/seed/              # Knowledge base
│   ├── motor.json          # 8 motor Indonesia
│   ├── komponen.json       # 30 komponen
│   ├── gejala.json         # 25 gejala + alias bengkel
│   ├── penyebab.json       # 32 penyebab + follow-up
│   ├── relasi_gejala_penyebab.json  # 124 relasi
│   ├── solusi.json         # 96 solusi (4 tier)
│   ├── harga.json          # 24 harga + jasa
│   ├── lokasi_komponen.json # 163 lokasi per motor
│   └── image_component.json # 108 image registry
├── ui/                     # Frontend
│   ├── index.html          # Beranda
│   ├── diagnose.html       # Input motor + keluhan
│   ├── result.html         # Hasil + cara cek + solusi
│   ├── library.html        # Library komponen
│   ├── method.html         # Metode & confidence
│   ├── css/                # 5 stylesheets
│   └── js/                 # 8 modules (vanilla)
├── scripts/                # Audit + maintenance
├── design.md               # Design spec lengkap
├── .gitignore
├── README.md
└── CHANGELOG.md
```

## 🔬 Engine: Confidence Formula

**K=6 (saturating)** — FROZEN.

```
confidence = 1 - exp(-score / 6)
```

- `<60%` → reject ("belum cukup data")
- `60-75%` → sedang
- `75-90%` → tinggi
- `>90%` → sangat tinggi

Mengapa **K=6**: K=4 terlalu tinggi (avg 97.9%, no headroom), K=8 terlalu konservatif (avg 86.6%), K=6 sweet spot (avg 92.9%).

## 🛡️ Guard: Karbu-Only

Sistem MENOLAK diagnosis untuk motor injeksi (PGM-FI, YMJET-FI, dll). Pola regex: `9 kata kunci` di motor.type + keluhan. Lihat `karbuin/kb.py` untuk detail.

## 🧪 Testing

```bash
# UAT (5 kasus terverifikasi manual)
python3 /tmp/uat_5_hard.py

# Test Pack 50 (50 kasus synthetic)
python3 /tmp/run_test_pack.py

# Test Pack 50 v2 (dengan disambiguation follow-up)
python3 /tmp/run_test_pack_v2.py
```

## 📜 Lisensi

TBD — internal Hybern + Karbuin project.

## 👤 Maintainer

Karbuin Curator · karbuin@karbuin.id
