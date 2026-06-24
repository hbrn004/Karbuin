# 100 Real-World Test Cases — Methodology

> **Tujuan**: Validasi Karbuin terhadap kasus nyata dari pengguna, bukan benchmark synthetic.
> **Status**: DRAFT v1.0 (2026-06-25)
> **Owner**: Karbuin Curator

## 🎯 Sasaran

- **Minimal**: 100 kasus nyata
- **Source**: Bengkel motor, komunitas motor, pengguna awam
- **Format**: Tiap kasus = {id, motor_id, user_input, ground_truth_cause, ground_truth_notes}
- **Distribution**: Mirip dengan distribusi keluhan di jalan (top-5 kategori 60-70%)

## 📊 Distribusi Target (100 kasus)

| Kategori | Target | Reason |
|---|---|---|
| brebet | 15 | Symptom paling umum |
| susah_hidup_pagi | 12 | Musim hujan, motor lama |
| bensin_boros | 10 | Keluhan umum |
| langsam_turun_naik | 10 | Idle issue, banyak penyebab |
| kehilangan_tenaga | 8 | Older bikes |
| aki_tekor / lampu_redup | 7 | Electrical |
| asap_putih / asap_hitam | 6 | Engine internal |
| nembak | 6 | Mid-RPM issue |
| langsam_tinggi | 5 | Adjustment |
| susah_hidup_panas | 4 | Hot start |
| oli_cepat_habis | 4 | Mechanical |
| overflow_karbu | 4 | Float issue |
| kompresi_rendah | 3 | Older high-mileage |
| kabel_gas_seret | 3 | Wear & tear |
| combo / multi-symptom | 3 | User reports multiple |
| **Total** | **100** | |

## 📝 Distribusi Motor

Mirip market share motor karbu di Indonesia (estimasi):

| Motor | Target | Note |
|---|---|---|
| Honda Supra X125 | 25 | Motor paling umum di Indonesia |
| Yamaha Mio Sporty | 18 | Beat competitor, MIO dulu injeksi |
| Honda Revo | 12 | Murah, banyak |
| Yamaha Jupiter Z | 12 | Sport bebek |
| Honda Tiger 2000 | 10 | Sport legendaris, masih banyak |
| Suzuki Smash | 8 | Murah, banyak |
| Yamaha Fino | 8 | Retro, banyak anak muda |
| Kawasaki Kaze R | 7 | Sport murah |
| **Total** | **100** | |

## 🔍 Sumber Data

### Tier 1 (Paling Valid) — 50 kasus

1. **Bengkel rekanan (3-5 bengkel)** di Jakarta/Bekasi/Bandung
   - Minta 10-15 kasus per bengkel
   - Data: motor, keluhan asli, penyebab final (setelah dicek mekanik)
   - Format: foto struk bengkel, video diagnosa, atau catatan mekanik
2. **Mekanik online**: posting di grup Facebook mekanik motor (NMC, FORBIK)
3. **YouTube channel bengkel**: extract kasus dari video diagnosa

### Tier 2 (Valid tapi Kurang Verified) — 30 kasus

4. **Komunitas motor**: posting di grup Beat, Mio, Supra, Jupiter
5. **Reddit r/indonesia atau r/motorcycle**
6. **Posting di marketplace motor**: kadang ada diskusi masalah

### Tier 3 (Synthetic-Realistic) — 20 kasus

7. **Kasus fiktif yang realistis**: dibuat berdasarkan pengetahuan bengkel
   - Marked sebagai "synthetic" bukan "real"
   - Hanya untuk augmentasi data, bukan validasi utama

## 📋 Format Pencatatan

Buat file `data/real_validation_100.json` dengan struktur:

```json
[
  {
    "id": "R001",
    "source": "bengkel_jakarta_selatan",
    "source_tier": 1,
    "collected_at": "2026-07-01",
    "collector_notes": "Bengkel Pak Ahmad, Jakarta Selatan, mekanik senior 15 tahun",
    "motor_id": "honda_supra_x125_karbu",
    "motor_year": 2018,
    "mileage_km": 45000,
    "user_input_asli": "Mas, motor saya pagi-pagi ngga mau hidup, kayaknya diengkol berat",
    "user_input_normalized": "susah hidup pagi starter berat",
    "ground_truth_cause_id": "busi_lembab_basah",
    "ground_truth_notes": "Busi berkarat karena jarang dipakai, motor jarang dipanaskan",
    "verified_by_mechanic": "Pak Ahmad",
    "verification_date": "2026-07-01"
  }
]
```

## 🧪 Cara Test

```python
# 1. Load real validation
real_cases = json.load(open('data/real_validation_100.json'))

# 2. For each, call diagnose API
for case in real_cases:
    r = requests.post('http://localhost:8000/api/diagnose', json={
        'motor_id': case['motor_id'],
        'user_input': case['user_input_normalized']
    })
    top = r.json()['results'][0]['cause']['id']
    if top == case['ground_truth_cause_id']:
        result = 'PASS'
    elif top in acceptable_set:
        result = 'PARTIAL'
    elif r.json()['confidence'] < 0.6:
        result = 'AMBIGUOUS'
    else:
        result = 'FAIL'

# 3. Aggregate report
```

## 📈 Grading

| Grade | Kriteria | Action |
|---|---|---|
| **PASS** | Top-1 = ground_truth | Highlight success case |
| **PARTIAL** | Top-2/3 acceptable, ground_truth di sana | Investigate ranking |
| **AMBIGUOUS** | Top-1 ≠ ground_truth, conf < 60% | OK (system admits uncertainty) |
| **FAIL** | Top-1 ≠ ground_truth, conf ≥ 60% | **CRITICAL — perlu perbaikan** |

**Target**:
- **PASS** ≥ 70% (dari 100 kasus)
- **PARTIAL** ≤ 15%
- **AMBIGUOUS** ≤ 10%
- **FAIL** ≤ 5% (maks 5 dari 100)

## 🔄 Iterasi Perbaikan

Setelah 100 kasus pertama, identifikasi:
1. **FAIL cases** — top-prioritas, fix KB atau parser
2. **PARTIAL cases** — adjust weight relasi
3. **Categories yang sering FAIL** — perlu tambahan penyebab atau alias
4. **Gejala yang sering missed** — perlu lebih banyak alias

Lakukan iterasi:
- V1: kumpulkan 100 kasus
- V2: fix FAIL, kumpulkan 100 kasus baru
- V3: validate improvement

## ⚠️ Limitasi & Etika

1. **No PII**: jangan simpan nama, no HP, alamat bengkel, foto wajah
2. **Consent**: minta izin mekanik/pemilik motor sebelum pakai kasus
3. **Anonymization**: ganti nama bengkel jadi "bengkel_X", nama mekanik jadi "Pak A/B"
4. **Validation source**: hanya dari mekanik bersertifikat atau pengalaman >5 tahun
5. **No medical/insurance claim**: ini alat bantu, bukan pengganti diagnosa mekanik

## 📅 Timeline

| Milestone | Target Date | Status |
|---|---|---|
| Setup form + list bengkel rekanan | 2026-07-01 | Pending |
| Kumpulkan 30 kasus Tier 1 | 2026-07-15 | Pending |
| Kumpulkan 50 kasus (Tier 1 + Tier 2) | 2026-08-01 | Pending |
| Tambahkan 20 synthetic-realistic | 2026-08-05 | Pending |
| Run first validation 100 | 2026-08-10 | Pending |
| Fix FAIL cases | 2026-08-15 | Pending |
| Run validation V2 (100 baru) | 2026-08-30 | Pending |

## 📤 Output

Setelah selesai, hasil akan dipublikasikan di:
- `/data/real_validation_100.json` (cases)
- `/data/real_validation_report_v1.json` (results per case)
- `CHANGELOG.md` entry untuk v1.2.0

## 👤 Penanggung Jawab

Karbuin Curator · karbuin@karbuin.id
