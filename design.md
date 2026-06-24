# Karbuin — Motorcycle Carburetor Diagnostic Expert System — Design v0.1

> **Brand:** **Karbuin** (Karburator + Indonesia)
> **Status:** DESIGN — belum ada kode. Untuk review sebelum implementasi.
> **Project:** NEW (terpisah dari motorcycle-diag v5 frozen)
> **Prinsip:** KB = source of truth, LLM = wrapper, akurasi > kelengkapan > UX > tampilan.

## TL;DR

**Karbuin** = expert system / knowledge graph untuk diagnosis motor karburator
Indonesia. Berbasis SQLite (dev) → PostgreSQL (prod), 11 entity, weighted
inference engine, no-hallucination guards WAJIB.

## 1. Tech Stack

| Layer       | Pilihan                              | Alasan                                     |
| ----------- | ------------------------------------ | ------------------------------------------ |
| Backend     | Python 3.11+                         | ecosystem AI/data, library-rich            |
| DB          | SQLite (dev) → PostgreSQL (prod)     | zero-config dev, easy migration            |
| KB format   | JSON / YAML                          | human-readable, git-friendly               |
| ORM         | SQLAlchemy 2.0 + Pydantic v2         | type-safe, schema validation               |
| API         | FastAPI (Phase 2)                    | auto-docs, async                           |
| Frontend    | Next.js + Tailwind (Phase 2)         | mobile-first, modern                       |
| Parser      | Alias matching rule-based (no LLM)   | deterministic, auditable, no hallucination  |

## 2. Entity Schemas (11 entities)

### 2.1 `motor`
```json
{
  "id": "honda_supra_x125_2006",
  "brand": "Honda",
  "model": "Supra X 125",
  "year_start": 2006,
  "year_end": 2014,
  "fuel_system": "carburetor",
  "carb_type": "PE24",
  "engine_cc": 125,
  "category": "underbone",
  "common_aliases": ["supra 125", "supra fit", "supra x 125 karbu"]
}
```

### 2.2 `komponen`
```json
{
  "id": "intake_manifold",
  "name": "Intake Manifold / Karet Intake",
  "aliases": ["manifold", "karet manifold", "rubber inlet"],
  "category": "intake",
  "function": "Saluran campuran udara-bahan bakar dari karburator ke cylinder head",
  "default_location": "Antara karburator dan cylinder head",
  "inspection_method": "Hidupkan mesin idle, semprot carb cleaner di sambungan. RPM berubah = bocor.",
  "replacement_difficulty": "easy",
  "severity_if_failed": "medium"
}
```

### 2.3 `gejala`
```json
{
  "id": "langsam_tinggi",
  "name": "Langsam Tinggi",
  "aliases": ["langsam ngebut", "rpm tinggi", "idle naik sendiri", "gas spontan"],
  "category": "langsam",
  "severity": "medium",
  "description": "RPM idle di atas normal, tidak turun saat gas dilepas"
}
```

### 2.4 `penyebab`
```json
{
  "id": "intake_manifold_leak",
  "name": "Kebocoran Intake Manifold",
  "aliases": ["karet intake bocor", "manifold rembes"],
  "related_components": ["intake_manifold", "intake_clamp"],
  "likelihood_default": 0.7,
  "severity": "medium",
  "urgency": "medium",
  "description": "Karet intake retak/kendor → udara palsu → campuran kurus → RPM fluktuatif",
  "diagnosis_method": "Semprot carb cleaner di area sambungan saat idle. RPM naik = bocor."
}
```

### 2.5 `relasi_gejala_penyebab` (HEART OF SYSTEM)
```json
{
  "id": 1,
  "symptom_id": "langsam_tinggi",
  "cause_id": "intake_manifold_leak",
  "weight": 9,
  "motor_filter": null,
  "evidence": "5 kasus Honda Supra X 125 2010-2012 di Bengkel Pak Asep",
  "source_ref": "src_001",
  "verified": true
}
```

### 2.6 `solusi` (tiered)
```json
{
  "id": "sol_intake_free",
  "cause_id": "intake_manifold_leak",
  "tier": "free",
  "description": "Periksa klem manifold, kencangkan. Bersihkan area sambungan.",
  "tools_needed": ["kunci 8mm"],
  "time_estimate_min": 5,
  "difficulty": "easy",
  "success_rate": 0.3
}
```

Tier values: `free` | `budget` | `mid` | `full`

### 2.7 `harga`
```json
{
  "id": "harga_intake_manifold_honda_underbone",
  "item_type": "part",
  "item_id": "intake_manifold",
  "motor_compatibility": ["honda_*"],
  "part_price": {"min": 25000, "max": 90000, "currency": "IDR"},
  "labor_price": {"min": 10000, "max": 50000, "currency": "IDR"},
  "region": "national_range",
  "source_ref": "src_002",
  "verified": false,
  "last_updated": "2024-06-15"
}
```

### 2.8 `lokasi_komponen` (per model motor — KRITIS)
```json
{
  "id": "loc_honda_supra_x125_intake_manifold",
  "motor_id": "honda_supra_x125_2006",
  "component_id": "intake_manifold",
  "location_description": "Sisi kanan motor, antara karburator dan cylinder head",
  "access_method": "Lepas body cover kanan, buka 2 klem karburator, tarik manifold dari cylinder head",
  "tools_needed": ["kunci 8mm", "obeng plus"],
  "difficulty": "easy",
  "time_estimate_min": 15,
  "reference_images": [],
  "verified": false,
  "verified_by": null,
  "verification_date": null,
  "verifier_notes": null
}
```

### 2.9 `image_component`
```json
{
  "id": "img_intake_manifold_generic",
  "component_id": "intake_manifold",
  "image_url": null,
  "image_type": "component",
  "description": "Foto intake manifold standar Honda karbu",
  "motor_specific": null,
  "verified": false
}
```

`image_type`: `component` | `location` | `diagram` | `highlight`

### 2.10 `sumber_referensi` (auditability — WAJIB untuk tiap relasi/harga)
```json
{
  "id": "src_001",
  "entity_type": "relasi_gejala_penyebab",
  "entity_id": "1",
  "source_type": "manual_bengkel",
  "source_url": null,
  "source_text": "Bengkel Pak Asep, Indramayu, 5 kasus Supra X 125 2010-2012",
  "verified_by": "asep_ahmad",
  "date": "2024-06-15",
  "reliability": "high"
}
```

`source_type`: `manual_bengkel` | `forum` | `youtube` | `ahli` | `buku_panduan` | `manual_resmi`

### 2.11 `diagnosis_log` (audit + learning loop)
```json
{
  "id": "diag_001",
  "timestamp": "2024-06-20T10:30:00",
  "motor_id": "honda_supra_x125_2006",
  "user_input_raw": "motor bunyi tek tek trus langsam tinggi",
  "parsed_symptoms": ["bunyi_mesin_tidak_normal", "langsam_tinggi"],
  "top_causes": [{"cause_id": "intake_manifold_leak", "score": 0.85, "confidence": 0.78}],
  "shown_to_user": {},
  "user_confirmed": null,
  "feedback_text": null
}
```

## 3. ERD / Knowledge Graph

```
                ┌──────────────┐
                │    motor     │
                └──────┬───────┘
                       │ 1:N
                       ▼
                ┌──────────────┐    N:1    ┌──────────────┐
                │  lokasi_     ├───────────►│  komponen    │
                │  komponen    │           └──────┬───────┘
                └──────────────┘                  │ 1:N
                                                 ▼
                                          ┌──────────────┐
                                          │  image_      │
                                          │  component   │
                                          └──────────────┘

   ┌──────────────┐                  ┌──────────────┐
   │   gejala     │                  │  penyebab    │
   └──────┬───────┘                  └──────┬───────┘
          │ N                                │ N
          │            ┌─────────────────┐   │
          └───────────►│ relasi_gejala_  │◄──┘
                       │ penyebab        │
                       │ (weight 1-10)   │
                       └────────┬────────┘
                                │ 1:N
                                ▼
                         ┌──────────────┐
                         │   solusi     │
                         │ tier: free/  │
                         │ budget/mid/  │
                         │ full         │
                         └──────────────┘

   ┌──────────────┐         ┌──────────────┐
   │   harga      │         │  sumber_     │
   │ (part/labor) │         │  referensi   │
   └──────────────┘         │ (polymorphic)│
                           └──────────────┘

   ┌────────────────┐
   │ diagnosis_log  │ (audit + learning loop)
   └────────────────┘
```

## 4. Diagnosis Engine Algorithm

```python
def diagnose(user_input: str,
             motor_id: str | None = None,
             explicit_symptoms: list[str] | None = None) -> DiagnosisResult:

    # 1. Parse free-text → symptom IDs (rule-based alias matching)
    parsed = parse_user_input(user_input)
    active_symptoms = merge_symptoms(parsed, explicit_symptoms)

    # 2. Untuk setiap gejala, lookup relasi_gejala_penyebab
    cause_scores: dict[str, float] = {}
    for symptom_id, _ in active_symptoms:
        for rel in get_relations(symptom_id, motor_filter=motor_id):
            cause_scores[rel.cause_id] += rel.weight

    # 3. Normalize → confidence
    max_possible = len(active_symptoms) * 10
    ranked = sorted(
        [{"cause_id": cid, "score": s,
          "confidence": s / max_possible if max_possible else 0}
         for cid, s in cause_scores.items()],
        key=lambda x: x["score"], reverse=True
    )

    # 4. NO-HALLUCINATION GUARD
    if not ranked or ranked[0]["confidence"] < CONFIDENCE_THRESHOLD:
        return {
            "status": "data_tidak_cukup",
            "suggestion": "Tambahkan gejala lain atau pilih model motor spesifik.",
            "partial_results": ranked[:3]
        }

    # 5. Enrich top causes (max 5)
    results = []
    for cause in ranked[:5]:
        components = get_components(cause["cause_id"])
        images     = get_images(components, motor_id)        # hanya verified
        solutions  = get_solutions(cause["cause_id"])         # tiered
        prices     = get_prices(components, motor_id)         # range
        location   = get_location(components, motor_id)       # ONLY if verified
        reasoning  = generate_reasoning(cause, active_symptoms)

        results.append({
            "cause": cause, "components": components,
            "images": images, "solutions": solutions,
            "prices": prices, "location": location,
            "reasoning": reasoning
        })

    log_to_diagnosis_log(user_input, motor_id, active_symptoms, results)
    return {"status": "ok", "results": results}
```

## 5. No-Hallucination Guards (CRITICAL)

| Trigger                                          | Response                                                                   |
| ------------------------------------------------ | -------------------------------------------------------------------------- |
| Confidence < 60%                                 | "Data tidak cukup. Tambahkan gejala atau pilih model motor."               |
| Lokasi tidak verified untuk motor_id             | "Lokasi model spesifik belum terverifikasi" + foto generic saja           |
| Component image tidak ada                        | Placeholder, **JANGAN** pakai foto random                                  |
| Harga tidak ada                                  | "Harga belum tersedia" — **JANGAN** estimasi                               |
| User input tidak match gejala apapun             | "Kami tidak mengenali gejala. Coba: 'motor brebet', 'susah hidup pagi'"    |
| Solusi tier kosong                               | "Solusi belum tersedia, hubungi mekanik" — **JANGAN** bikin solusi         |
| Penyebab tanpa `related_components`              | TIDAK ditampilkan sama sekali                                             |
| `image_url` verified=false                       | TIDAK ditampilkan ke user (placeholder saja)                               |

## 6. Contoh Data Real (akan dibuat setelah approval)

Brand fokus: **Honda, Yamaha, Suzuki, Kawasaki** (motor karbu umum Indonesia)

| Motor                  | Tahun    | Karburator   |
| ---------------------- | -------- | ------------ |
| Honda Supra X 125      | 2006-14  | PE24         |
| Honda Revo X           | 2007-14  | PZ16         |
| Honda Tiger 2000       | 2000-05  | Single carb  |
| Yamaha Mio Sporty      | 2003-08  | Mikuni       |
| Yamaha Fino Karbu      | 2008-14  | Mikuni       |
| Yamaha Jupiter Z       | 2003-08  | Mikuni       |
| Suzuki Smash           | 2003-14  | Mikuni       |
| Kawasaki Kaze          | 2003-08  | Mikuni       |

Seed awal:
- **Komponen** (~15): busi, intake_manifold, pilot_jet, main_jet, filter_udara,
  kiprok, aki, CDI, koil, klep, kran_bensin, selang_bensin, saringan_bensin,
  throttle_body, karter
- **Gejala** (~15): langsam_tinggi, langsam_turun_naik, susah_hidup_pagi, brebet,
  ngempos, nembak, bensin_boros, asap_putih, asap_hitam, starter_berat,
  aki_tekor, oli_bocor, suara_mesin_abnormal, kehilangan_tenaga, overheating
- **Penyebab** (~20): intake_leak, pilot_jet_clogged, main_jet_clogged,
  busi_aus, busi_rusak, filter_kotor, kiprok_rusak, aki_lemah, koil_lemah,
  CDI_rusak, klep_renggang, karburator_kotor, bensin_kotor, vacuum_bocor,
  timing_kemas_terlambat, ring_piston_aus, seal_klep_bocor, saringan_bensin_mampet,
  kran_bensin_mampet, kipas_rusak
- **Relasi** (target 30-50 entry): menghubungkan gejala↔penyebab dengan weight
  + `sumber_referensi` (penting untuk trust)

## 7. Project Structure

```
motorcycle-karbu-expert/
├── design.md              ← INI (review)
├── data/
│   ├── schema/           ← JSON schema definitions
│   └── seed/             ← initial data per brand
├── engine/
│   ├── parser.py         ← free-text → symptoms (rule-based)
│   ├── inference.py      ← weighted diagnosis
│   ├── confidence.py     ← scoring + normalization
│   └── safety.py         ← no-hallucination guards
├── db/
│   ├── models.py         ← SQLAlchemy 2.0
│   └── migrations/       ← Alembic
├── api/                  ← FastAPI (Phase 2)
└── ui/                   ← Next.js (Phase 2)
```

## 8. SQLite → PostgreSQL Migration Path

- SQLAlchemy ORM: switch backend via `DATABASE_URL`
- JSON columns: SQLite TEXT (JSON-encoded) → PostgreSQL JSONB
- FTS: SQLite FTS5 (dev) → PostgreSQL tsvector (prod)
- Alembic: schema version control

## 9. Final Decisions (Phase 1 Lock)

### 9.1 Parser: Rule-Based Deterministic

- **No LLM** di Phase 1. Pure alias-matching + n-gram substring.
- **Alasan:** auditable, cepat, no hallucination, mudah debugging.
- **Phase 2/3:** NLP/embedding sebagai enhancement, optional.

### 9.2 Confidence Tiers

| Confidence   | Tier                  |
| ------------ | --------------------- |
| `< 0.60`     | Data tidak cukup      |
| `0.60 – 0.74`| Kemungkinan sedang    |
| `0.75 – 0.89`| Kemungkinan tinggi    |
| `≥ 0.90`     | Sangat tinggi         |

### 9.3 Seed Scope: 8 Motor (Honda/Yamaha/Suzuki/Kawasaki)

| Brand   | Model           | Karburator | Tahun     |
| ------- | --------------- | ---------- | --------- |
| Honda   | Supra X 125 Karbu | PE24     | 2006-14   |
| Honda   | Revo Karbu      | PZ16       | 2007-14   |
| Honda   | Tiger 2000      | Single     | 2000-05   |
| Yamaha  | Mio Sporty      | Mikuni     | 2003-08   |
| Yamaha  | Fino Karbu      | Mikuni     | 2008-14   |
| Yamaha  | Jupiter Z       | Mikuni     | 2003-08   |
| Suzuki  | Smash           | Mikuni     | 2003-14   |
| Kawasaki| Kaze            | Mikuni     | 2003-08   |

### 9.4 Image Registry

- Build schema + metadata first.
- **No mass scraping** di Phase 1.
- Image kosong → tampilkan `"gambar belum tersedia"`.
- `verified=true` WAJIB sebelum gambar ditampilkan ke user.

### 9.5 Lokasi Komponen: Manual Verification

- `verified`, `verified_by`, `verified_date`, `verification_note` (4 fields).
- Lokasi **tidak boleh** dihasilkan AI — ini pembeda Karbuin vs chatbot biasa.
- Verified=false → label eksplisit `"Lokasi model spesifik belum terverifikasi"`.

### 9.6 Harga: National Range Dulu

- Field: `part_price_min`, `part_price_max`, `labor_price_min`, `labor_price_max`.
- Region = `national_range` (single).
- Arsitektur siap untuk regional pricing nanti (field `region` polymorphic).

### 9.7 motor_filter: RETAINED

- Gejala sama → penyebab beda per model motor.
- Filter di `relasi_gejala_penyebab.motor_filter` (list motor_id atau wildcard pattern).

### 9.8 Komponen Wajib Punya

- `function` (fungsi)
- `common_symptoms_if_failed` (gejala umum jika rusak)
- `inspection_difficulty` (tingkat kesulitan pengecekan)
- `tools_needed` (alat yang dibutuhkan)

### 9.9 Display Rules (FINAL)

- ✅ Tampilkan gambar komponen (jika verified)
- ✅ Tampilkan gambar lokasi pada model motor terkait (jika verified + motor match)
- ✅ Tampilkan langkah pengecekan sederhana
- ❌ JANGAN tampilkan lokasi tidak terverifikasi
- ❌ JANGAN tampilkan gambar lokasi yang tidak sesuai model motor
- ❌ JANGAN ngarang/estimasi harga kosong

### 9.10 Priority Order

**Akurasi > Validitas data > UX > Tampilan**

### 9.11 Checkpoint Sebelum UI

Setelah schema + seed + engine selesai, tampilkan:
- ERD final
- Sample diagnosis (3 skenario)
- Coverage report
- Baru lanjut ke UI Karbuin

---

## 10. Original Open Questions (closed)

| # | Question | Decision |
|---|----------|----------|
| 1 | Schema cukup? | ✅ Cukup, jangan over-engineering dulu |
| 2 | Parser rule-based atau NLP? | ✅ **Rule-based** dulu |
| 3 | Confidence threshold? | ✅ 4 tiers (60/75/90) |
| 4 | Seed 5 atau 8 motor? | ✅ **8 motor** |
| 5 | Image source? | ✅ Registry dulu, no scraping |
| 6 | Lokasi verified workflow? | ✅ **Manual**, 4 field wajib |
| 7 | Harga regional? | ✅ National_range dulu |
| 8 | motor_filter perlu? | ✅ **Retained** |