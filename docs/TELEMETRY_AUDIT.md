# 📊 Telemetry Audit Report — Karbuin v1.1.2

**Date**: 2026-06-24
**Scope**: Audit existing telemetry. **No new metrics added.**
**Source**: `data/telemetry/2026-06-24.jsonl` (45 events, 45 KB)

---

## 🎯 Pertanyaan Audit

1. Apakah event yang dilog berguna?
2. Event mana yang paling sering muncul?
3. Apakah ada metric yang hilang dari data?
4. Apakah ada field yang tidak terpakai?

---

## 📈 Event Distribution

| Event Type | Count | % | Use Case |
|---|---|---|---|
| `diagnose` | 40 | 88.9% | POST /api/diagnose — primary action |
| `followup` | 5 | 11.1% | POST /api/diagnose/followup — disambiguation answer |
| `error` | 0 | 0% | Reserved for future (currently unused) |

**Conclusion**: Event types tepat. Tidak perlu tambah event baru.

---

## 📋 Field Population (16 fields)

### Core (always populated, 100%)

| Field | Type | Use |
|---|---|---|
| `ts` | ISO 8601 | Timestamp |
| `event` | string | Event type |
| `ip_hash` | SHA256[16] | Privacy-safe client ID |
| `ua` | string | User-Agent (raw) |
| `user_input` | string | Raw keluhan user |
| `motor_id` | string | Selected motor (or None) |
| `explicit_symptoms` | list | User-selected chips |
| `top_cause_id` | string | Engine's top-1 prediction |
| `top_cause_name` | string | Display name |
| `top_confidence` | float (0-1) | Engine confidence |
| `all_causes` | list | Full result list (for top-3 analysis) |

### Diagnose-specific (89% populated)

| Field | Use |
|---|---|
| `parsed_symptoms` | List gejala yang terdeteksi dari `user_input` |
| `result_status` | ok / no_symptom_match |
| `result_count` | How many causes returned |
| `top_tier` | Confidence tier (always populated in diagnose, but empty string mostly) |

### Followup-specific (11% populated)

| Field | Use |
|---|---|
| `answers` | Dict {question_id: answer} |
| `adjustments` | Dict {cause_id: confidence_delta} |

### Error event (reserved, 0% populated)

- No `error` events yet. Field schema TBD when first error occurs.

---

## 🚗 Behavior Insights

### Engine outputs (40 diagnose events)

| Result Status | Count | % |
|---|---|---|
| `ok` | 37 | 92.5% |
| `no_symptom_match` | 3 | 7.5% |

**Confidence**: avg=0.773, range [0.000, 0.974]
- min=0.000 (probably the no_match cases)
- Range tight to high confidence → engine is confident when matches exist

### Top predicted causes

| Cause | Count | % |
|---|---|---|
| `filter_udara_kotor` | 17 | 42.5% |
| `busi_aus` | 13 | 32.5% |
| `bensin_kotor` | 3 | 7.5% |
| `aki_lemah` | 3 | 7.5% |
| `cdi_rusak` | 1 | 2.5% |
| (no_match) | 3 | 7.5% |

⚠️ **Caveat**: Sample data ini 100% dari WSL curl + browser test. **Bukan data real user**. Distribusi ini akan berubah signifikan setelah Render deploy + traffic real.

### Motor distribution

| Motor | Count |
|---|---|
| `yamaha_mio_sporty` | 22 |
| `honda_supra_x125_karbu` | 17 |
| (none) | 1 |

### User-Agent breakdown

| UA | Count | Note |
|---|---|---|
| `Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:150.0)` | 36 | Firefox di WSL (browser test) |
| `curl/8.5.0` | 8 | CLI smoke test |
| `test` | 1 | Stub event |

---

## 🚫 Yang TIDAK perlu ditambah

User rule: **"Jangan menambah metric baru tanpa bukti kebutuhan."**

Audit menunjukkan **TIDAK ada kebutuhan** untuk metric baru. Berikut alasannya:

### 1. Coverage sudah lengkap

| Kebutuhan | Field | Status |
|---|---|---|
| Hitung diagnose per hari | `ts` + `event=diagnose` | ✓ |
| Top penyebab | `top_cause_id` | ✓ |
| Confidence trend | `top_confidence` | ✓ |
| User behavior | `user_input`, `explicit_symptoms`, `motor_id` | ✓ |
| Disambiguation quality | `followup.answers` + `adjustments` | ✓ |
| Mobile vs desktop | `ua` (parsed di dashboard) | ✓ |

### 2. Metrics yang SERING diminta tapi sudah ada via existing fields

- "Rata-rata user_input length?" → derived dari `user_input` di `input_samples` (dashboard)
- "Berapa diagnose per motor?" → derived dari `motor_id` (motors_breakdown di dashboard)
- "Top tier distribution?" → `top_tier` (meskipun masih empty string — bisa diperbaiki di v2 kalau perlu)

### 3. Metrics yang TIDAK boleh ditambah (privacy)

- ❌ `ip_raw` (PII)
- ❌ `user_email` / `session_id` (no login system)
- ❌ `geo_location` (no GPS access)
- ❌ `referrer` (bisa bocor search history)

---

## 📊 Dashboard Coverage Check

Cek apakah `/dashboard` expose semua useful aggregates dari telemetry:

| Aggregate | Exposed in Dashboard? | Source |
|---|---|---|
| Total diagnose | ✓ | `totals.diagnose` |
| Total followup | ✓ | `totals.followup` |
| Total errors | ✓ | `totals.error` |
| Avg confidence | ✓ | `avg_top_confidence` |
| UA mix | ✓ | `ua_breakdown` (mobile/desktop/bot/other) |
| Daily activity | ✓ | `daily_breakdown` |
| Top 10 causes | ✓ | `top_causes_top10` |
| Motor distribution | ✓ | `motors_breakdown` |
| Latest events | ✓ | `/api/telemetry/recent` |
| Input samples | ✓ | `input_samples` |
| CSV export | ✓ | `/api/telemetry/csv` |

**Conclusion**: Dashboard 100% sufficient. **Tidak ada field baru yang perlu di-expose.**

---

## 🎯 Rekomendasi (Audit Outcome)

| Action | Reason |
|---|---|
| ❌ JANGAN tambah event type baru | Cukup dengan diagnose + followup + error (reserved) |
| ❌ JANGAN tambah field baru | 16 fields sudah mencakup semua use case |
| ❌ JANGAN tambah endpoint baru | Dashboard + CSV + recent sudah cukup |
| ❌ JANGAN ubah confidence formula | Engine FROZEN |
| ⚠️ PERHATIKAN: `top_tier` kosong | Mungkin bug di diagnoser, tapi TIDAK urgent. Investigasi di v2. |
| ⚠️ PERHATIKAN: UA parsing | `Mozilla/5.0 (X11...)` counted sebagai desktop. Correct. Tapi future mobile UA perlu diverifikasi setelah deploy. |

---

## ⏭️ Next Step

1. **Deploy ke Render** — agar ada data real-user
2. **Tunggu 50-100 events real** — agar telemetry bermakna
3. **Re-audit setelah 100 events** — apakah distribusi berubah signifikan

**Untuk saat ini**: telemetry existing SUDAH CUKUP untuk MVP. Audit selesai.

---

## 📂 File Reference

- Source: `karbuin/telemetry.py`
- Storage: `data/telemetry/YYYY-MM-DD.jsonl` (appended daily)
- API:
  - `GET /api/telemetry?days=7`
  - `GET /api/telemetry/csv?days=7`
  - `GET /api/telemetry/recent?limit=N`
- Dashboard: `GET /dashboard`

---

**Audit completed**: 2026-06-24
**Engine version**: v1.1.2 FROZEN
**Audit conclusion**: No new metrics needed. Existing telemetry is sufficient.