# Changelog

All notable changes to Karbuin documented here. Format: [Semantic Versioning](https://semver.org/).

---

## [1.0.0-mvp] — 2026-06-25

**First public MVP release. Engine v1 FROZEN. Audit passed.**

### Knowledge Base
- 8 motor: Honda Supra X125, Revo X, Tiger 2000 · Yamaha Mio Sporty, Jupiter Z, Fino · Suzuki Smash · Kawasaki Kaze R
- 30 komponen karburator
- 25 gejala dengan 169+ alias bengkel
- 32 penyebab
- 124 relasi gejala→penyebab (semua populated, motor-filter aktif)
- 96 solusi bertingkat (4 tier per penyebab: gratis, hemat, mid, full)
- 24 harga part + jasa (verified by marketplace_survey_2024)
- 163 lokasi komponen per motor (verified by kurator phase 1.7A)
- 108 image registry entry (placeholder; file asli menyusul)

### Engine
- K=6 confidence formula FROZEN (`1 - exp(-score/6)`)
- Karbu-only guard aktif
- Motor filter (kipas_rusak hanya untuk Tiger 2000)
- Parser: substring matching + alias bengkel
- Disambiguation follow-up (yes/no weight bonus/penalty)

### UI
- 5 halaman: index, diagnose, result, library, method
- 8 vanilla JS modules, 5 stylesheets
- Badge: Risk, DIY, Waktu, VERIFIED, POPULATED, NEEDS CONFIRM
- Confirmation block untuk cause `requires_confirmation=true`
- Share via WhatsApp / clipboard

### Test
- UAT 5/5 PASS
- Test Pack 50: 40/50 PASS direct, 44/50 effective, 0 FAIL
- Ambiguous rate: 10%

### Audit
- All 5 UI pages HTTP 200
- All static assets serving
- Diagnose API returns 5 candidates dengan confidence + tier + badges
- Follow-up questions render + cause_id wired correctly
- Git initialized, 1 commit, branch `main`

---

## [0.x.x] — internal phases (pre-MVP)

### Phase 1.7B — Follow-up intelligence
- 10 disambiguation follow-up questions added
- API: `/api/diagnose/followup` with `answer_adjustments`
- Ambiguous rate: 18% → 10%

### Phase 1.7A — Knowledge completion
- 46 solusi baru (12 cause × 4 tier)
- 9 harga baru
- 75 lokasi baru
- 9 image registry placeholder

### Phase 1.6 — Schema enhancement
- 12 penyebab baru (overflow breakdown + common karbu)
- 38 relasi baru
- 5 gejala baru (3 new + 2 missing fix)
- 11 komponen baru
- `requires_confirmation` field
- `motor_filter` + `cooling_type` per motor
- `source_type`, `verified`, `populated` per relasi

### Phase 1.5 — Karbu guard
- Frontend: 9 keywords karbu-incompatible
- Backend: regex filter
- "Mio M3" CV test (Mio Sporty tetap jalan) — PASS

### Phase 1 — Initial engine
- K=4 default → K=6 (saturating)
- 5/5 UAT pass
- Karbuin v1: 8 motor, 19 komponen, 20 penyebab, 60 relasi
