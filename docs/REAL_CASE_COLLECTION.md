# 📝 Real-Case Collection Workflow

**Tujuan**: Mengumpulkan kasus nyata dari motor karburator untuk validasi engine FROZEN.

---

## 🎯 Scope

| Aspek | Target |
|---|---|
| **Jumlah** | 100 kasus nyata (sudah ada plan di `docs/REAL_VALIDATION_100_PLAN.md`) |
| **Source** | Bengkel langganan, forum motor, grup Facebook, komunitas |
| **Format** | `data/real_cases.jsonl` (JSON Lines) |
| **Privacy** | NO PII — nama, no HP, alamat TIDAK disimpan |
| **Labeler** | Mekanik senior / orang yang punya motor tsb |

---

## 📋 Apa yang Dikumpulkan per Kasus?

### Minimum (wajib)
- **motor_id**: salah satu dari 8 motor Karbuin
- **user_input**: keluhan asli user (verbatim, bahasa bebas)
- **expected_cause**: penyebab aktual (dari mekanik / yang terjadi setelah dibongkar)

### Recommended (lebih baik)
- **explicit_symptoms**: list gejala yang user pilih secara eksplisit
- **actual_fix**: tindakan yang dilakukan (ganti busi, kuras bensin, dll)
- **actual_cost**: estimasi biaya yang dikeluarkan (Rp)
- **diy_or_mechanic**: apakah user kerjain sendiri atau ke bengkel
- **location**: kota/kabupaten (untuk statistik geografis)
- **year_of_incident**: kapan kejadian (YYYY-MM)

### Optional (nice to have)
- **photo_url**: foto kerusakan / komponen
- **notes**: catatan tambahan dari labeler
- **source**: dari mana kasus ini (bengkel, forum, dll)
- **confidence_in_label**: 1-5, seberapa yakin labeler dengan expected_cause

---

## 📥 Format JSONL (1 kasus per baris)

```jsonl
{"ts": "2026-06-24T12:00:00Z", "case_id": "RC001", "motor_id": "yamaha_mio_sporty", "motor_year": 2010, "user_input": "motor brebet di tanjakan, bensin jadi boros", "explicit_symptoms": ["brebet", "bensin_boros"], "expected_cause": "busi_aus", "actual_fix": "ganti busi NGK CPR8EA-9", "actual_cost": 25000, "diy_or_mechanic": "diy", "location": "Bandung", "year_of_incident": "2026-05", "source": "bengkel_rudi", "confidence_in_label": 5}
{"ts": "2026-06-24T13:00:00Z", "case_id": "RC002", "motor_id": "honda_supra_x125_karbu", "motor_year": 2015, "user_input": "langsam naik turun sendiri", "explicit_symptoms": ["langsam_turun_naik"], "expected_cause": "karburator_kotor", "actual_fix": "bersihkan karburator + setel langsam", "actual_cost": 75000, "diy_or_mechanic": "mechanic", "location": "Jakarta", "year_of_incident": "2026-04", "source": "forum_kaskus", "confidence_in_label": 4}
```

---

## 🔄 Workflow Pengumpulan

### Step 1: Setup spreadsheet (optional, untuk tracking)
Buat Google Sheet dengan kolom:

| case_id | date | motor | user_input | expected | actual_fix | cost | diy/mech | location | source | status |
|---|---|---|---|---|---|---|---|---|---|---|
| RC001 | 2026-05-15 | Mio Sporty | brebet di tanjakan, boros | busi_aus | ganti busi | 25k | diy | Bandung | bengkel_rudi | ✓ verified |

### Step 2: Convert ke JSONL
- Satu kasus = satu baris JSON
- File: `data/real_cases.jsonl`
- Append-only (tidak boleh edit case existing, kalau salah tambah baru dengan case_id baru + note "corrected_from_RC001")

### Step 3: Validasi format
```bash
# Valid: parse JSONL
python3 -c "
import json
with open('data/real_cases.jsonl') as f:
    for i, line in enumerate(f, 1):
        ev = json.loads(line)
        # Check required fields
        for k in ['case_id', 'motor_id', 'user_input', 'expected_cause']:
            assert k in ev, f'Line {i} missing {k}'
        # Check motor exists in KB
        from karbuin import KB
        assert ev['motor_id'] in [m['id'] for m in KB.motor], f'Line {i} invalid motor {ev[\"motor_id\"]}'
print('All valid')"
```

### Step 4: Run validation engine
```bash
# Score Karbuin against each case
python3 scripts/validate_real_cases.py
# Output: accuracy report per motor, per cause
```

---

## 📊 Validation Metrics

Saat engine dijalankan terhadap `real_cases.jsonl`, hitung:

| Metric | Formula | Target |
|---|---|---|
| **Top-1 Accuracy** | `correct_top1 / total` | ≥ 80% |
| **Top-3 Accuracy** | `correct_top3 / total` | ≥ 95% |
| **Confidence Calibration** | `avg(confidence where correct)` vs `avg(confidence where wrong)` | gap ≥ 0.2 |
| **False Negative Rate** | `cases rejected (conf<60%) / total` | ≤ 10% |
| **Motor Coverage** | `cases with valid motor_id / total` | = 100% |
| **Avg User Input Length** | mean char count | 30-150 |

---

## 🚫 Anti-pattern: Apa yang TIDAK boleh dikumpulkan

- ❌ **Tidak ada kasus sintetik** — hanya kasus nyata dari lapangan
- ❌ **Tidak ada PII** — nama, no HP, alamat lengkap, email TIDAK boleh masuk
- ❌ **Tidak ada duplicate** — kalau motor sama dengan keluhan sama persis, jangan duplikasi
- ❌ **Tidak ada test case yang sudah ada di test pack** — Karbuin punya 50 test case di `data/test_pack/`
- ❌ **Tidak ada motor non-karbu** — kalau ada kasus injeksi (Vixion, NMAX, Aerox), masukkan ke list "deferred" dulu, jangan masuk real_cases.jsonl

---

## 🎯 Channel Pengumpulan

### Channel 1: Bengkel langsung
**Best for**: high-quality labeled data
**Process**:
1. Kunjungi bengkel motor langganan
2. Minta izin record keluhan + diagnosa + perbaikan
3. Bayar labeler fee (opsional, tergantung bengkel)
4. Convert ke JSONL dengan `actual_cost`, `actual_fix`, `diy_or_mechanic` filled

### Channel 2: Forum / grup Facebook
**Best for**: volume tinggi
**Process**:
1. Join grup "Motor Karburator Indonesia", "Yamaha Mio Bekas", dll
2. Cari thread yang punya info lengkap (keluhan + solusi)
3. Extract ke format JSONL dengan `source: "forum_<name>"`
4. ⚠️ **Always anonymize**: jangan include username asli, ganti jadi `forum_user_001`

### Channel 3: Survey
**Best for**: dataset diversity
**Process**:
1. Buat Google Form dengan pertanyaan terstruktur
2. Share di komunitas motor
3. Export CSV → convert ke JSONL
4. ⚠️ **Add disclaimer**: "Data digunakan untuk perbaikan sistem, tanpa PII"

### Channel 4: User-submitted (via Karbuin web)
**Best for**: continuous collection
**Process**:
1. Tambah tombol "Lapor Hasil Aktual" di /result page
2. User isi form singkat: "Apakah diagnosa Karbuin benar?"
3. Submit → auto-add ke JSONL dengan `source: "user_submitted"`, `expected_cause: "correct"` atau `"incorrect"`
4. Ini built-in feedback loop

---

## 📈 Roadmap

| Phase | Target | Deadline |
|---|---|---|
| **v1.1.3** (sekarang) | Workflow doc + format spec | DONE |
| **v1.1.4** | 10 kasus pertama (pilot, internal testing) | 1 minggu |
| **v1.2.0** | 50 kasus (Channel 1 + 2 mix) | 1 bulan |
| **v1.3.0** | 100 kasus (all channels) + validation report | 2 bulan |
| **v2.0.0** | 500+ kasus + release v2 dengan KB expansion (kalau ada yang missing) | 6 bulan |

---

## 🔗 Related Files

- `data/real_cases.jsonl` — actual data (jika sudah ada)
- `scripts/validate_real_cases.py` — validation runner (akan dibuat di v1.1.4)
- `docs/REAL_VALIDATION_100_PLAN.md` — initial 100-case plan
- `docs/VALIDATION_DATASET_FORMAT.md` — field specification (sister doc)
- `karbuin/telemetry.py` — production data source untuk comparison

---

**Engine FROZEN**: Kasus nyata yang dikumpulkan digunakan untuk **VALIDASI**, bukan untuk auto-update KB. Kalau ternyata ada gap besar di engine, akan jadi bahan diskusi untuk v2.0.0 (yang juga FROZEN saat ini).