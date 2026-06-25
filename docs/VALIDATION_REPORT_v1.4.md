# 🔬 Karbuin v1.4 — Real-World Validation Report

**Generated**: 2026-06-25
**Methodology**: Engine FROZEN — KB and inference unchanged. Real cases scored against v1.3.8 engine.

---

## 📊 Executive Summary

- **Total cases scored**: 24
- **Top-1 accuracy** (TP@1): 20.8% (5/24)
- **Top-3 accuracy** (TP@3): 37.5% (9/24)
- **Precision @1**: 20.8% (correct / (correct + FP))
- **Recall @1**: 20.8% (correct / total expected)
- **Precision @3**: 37.5%
- **Recall @3**: 37.5%
- **False Positives @1** (wrong predictions): 19
- **False Negatives @3** (expected missed entirely): 15
- **Rejected rate** (no prediction): 0.0% (0/24)
- **Confidence calibration gap**: +0.023

- **Avg confidence (correct)**: 0.901
- **Avg confidence (wrong)**: 0.878

> ℹ️ **Metric definitions** (binary ranking context):
> - **TP@1**: top-1 prediction matches ground truth
> - **FP@1**: top-1 prediction is wrong (model said something ≠ expected)
> - **FN@3**: expected cause NOT in top-3 (model missed it entirely)
> - **Precision@K**: TP@K / (TP@K + FP@K)
> - **Recall@K**: TP@K / total cases with expected cause
> - **Rejected**: engine returned `no_match` / `no_symptom_match` / `no_parse`

**Gap distribution (19 failures):**

  - 🔍 **parser**: 1 cases (5%)
  - 📚 **kb**: 7 cases (37%)
  - 📊 **ranking**: 4 cases (21%)
  - 🔗 **relasi**: 7 cases (37%)

---

## 📂 Dataset Composition

### By source

| Source | Count |
|---|---:|
| `bengkel_jakarta` | 8 |
| `bengkel_bandung` | 5 |
| `user_submitted` | 4 |
| `bengkel_depok` | 2 |
| `bengkel_surabaya` | 2 |
| `synthetic_workshop_2024` | 2 |
| `bengkel_yogya` | 1 |

### By motor

| Motor | Count |
|---|---:|
| yamaha_mio_sporty (Mio Sporty) | 3 |
| honda_supra_x125_karbu (Supra X 125 Karbu) | 2 |
| honda_tiger_2000 (Tiger 2000) | 2 |
| kawasaki_ninja_150 (Ninja 150) | 2 |
| yamaha_jupiter_z (Jupiter Z) | 1 |
| honda_revo_karbu (Revo Karbu) | 1 |
| yamaha_fino_karbu (Fino Karbu) | 1 |
| kawasaki_kaze (Kaze) | 1 |
| honda_megapro_karbu (MegaPro) | 1 |
| yamaha_vixion_karbu (Vixion) | 1 |
| suzuki_smash (Smash) | 1 |
| yamaha_rx_king_karbu (RX-King) | 1 |
| honda_grand_karbu (Grand) | 1 |
| honda_legenda_karbu (Legenda) | 1 |
| yamaha_jupiter_karbu (Jupiter) | 1 |
| honda_blade_karbu (Blade) | 1 |
| yamaha_f1zr_karbu (F1ZR) | 1 |
| honda_verza_karbu (Verza 150) | 1 |
| yamaha_byson_karbu (Byson) | 1 |

---

## 🏍 Per-Motor Performance

| Motor | Cases | Top-1 Acc | Top-3 Acc | Rejected |
|---|---:|---:|---:|---:|
| `yamaha_mio_sporty` | 3 | 33.3% | 66.7% | 0.0% |
| `honda_supra_x125_karbu` | 2 | 0.0% | 0.0% | 0.0% |
| `honda_tiger_2000` | 2 | 50.0% | 50.0% | 0.0% |
| `kawasaki_ninja_150` | 2 | 0.0% | 50.0% | 0.0% |
| `yamaha_jupiter_z` | 1 | 0.0% | 0.0% | 0.0% |
| `honda_revo_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `yamaha_fino_karbu` | 1 | 100.0% | 100.0% | 0.0% |
| `kawasaki_kaze` | 1 | 0.0% | 0.0% | 0.0% |
| `honda_megapro_karbu` | 1 | 0.0% | 100.0% | 0.0% |
| `yamaha_vixion_karbu` | 1 | 100.0% | 100.0% | 0.0% |
| `suzuki_smash` | 1 | 0.0% | 0.0% | 0.0% |
| `yamaha_rx_king_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `honda_grand_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `honda_legenda_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `yamaha_jupiter_karbu` | 1 | 0.0% | 100.0% | 0.0% |
| `honda_blade_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `yamaha_f1zr_karbu` | 1 | 100.0% | 100.0% | 0.0% |
| `honda_verza_karbu` | 1 | 0.0% | 0.0% | 0.0% |
| `yamaha_byson_karbu` | 1 | 0.0% | 0.0% | 0.0% |

---

## 🔍 Gap Analysis (Failures)

### 🔍 PARSER GAPS (1 cases)

**Description**: Engine could not extract symptoms from user input. Parser gaps indicate missing aliases or out-of-vocabulary input (typos, slang, regional terms).


#### RC013 — honda_grand_karbu

- **User input**: `motor gak mau hidup sama sekali, gak ada ledakan`
- **Expected cause**: `cdi_honda_lemah`
- **Predicted top-1**: `busi_rusak` (conf=0.632, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: high
- **Evidence**: No symptom matched from input 'motor gak mau hidup sama sekali, gak ada ledakan'. Parser returned 0 symptoms.
- **Recommendation**: Add aliases for keywords in 'motor gak mau hidup sama sekali, gak ada ledakan' to KB gejala aliases. Or check if user_input contains typos/unknown jargon.


### 📚 KB GAPS (7 cases)

**Description**: Knowledge base missing data for the matched symptom × cause × motor combination. Could be missing cause entry, missing motor-specific entry, or over-restrictive filter.


#### RC003 — yamaha_jupiter_z

- **User input**: `susah hidup pagi, harus diengkol berkali-kali`
- **Expected cause**: `busi_aus`
- **Predicted top-1**: `pilot_jet_clogged` (conf=0.777, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: medium
- **Evidence**: Expected cause 'busi_aus' not in result list (top causes were []). Parser matched ['susah_hidup_pagi'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'busi_aus' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC004 — honda_revo_karbu

- **User input**: `motor ngelitik pas rpm atas, suara kayak ketukan logam`
- **Expected cause**: `klep_renggang`
- **Predicted top-1**: `overheat_cooling` (conf=0.689, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: medium
- **Evidence**: Expected cause 'klep_renggang' not in result list (top causes were []). Parser matched ['mesin_ngelitik'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'klep_renggang' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC009 — suzuki_smash

- **User input**: `langsam tinggi sendiri, gas gak turun-turun`
- **Expected cause**: `setelan_angin_salah`
- **Predicted top-1**: `intake_leak` (conf=0.777, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: medium
- **Evidence**: Expected cause 'setelan_angin_salah' not in result list (top causes were []). Parser matched ['langsam_tinggi'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'setelan_angin_salah' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC014 — yamaha_mio_sporty

- **User input**: `tarikan ngempos di rpm atas, kayak kehabisan bensin padahal full`
- **Expected cause**: `kran_bensin_mampet`
- **Predicted top-1**: `main_jet_clogged` (conf=0.993, in_top3=False)
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'kran_bensin_mampet' not in result list (top causes were ['main_jet_clogged', 'bensin_kotor', 'filter_udara_kotor']). Parser matched ['ngempos', 'mesin_ngempos', 'tarikan_ngempos_verza', 'brebet'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'kran_bensin_mampet' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC015 — honda_supra_x125_karbu

- **User input**: `brebet parah pas di tanjakan, kayak mau mati`
- **Expected cause**: `busi_aus`
- **Predicted top-1**: `bensin_kotor` (conf=0.736, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: medium
- **Evidence**: Expected cause 'busi_aus' not in result list (top causes were []). Parser matched ['brebet', 'brebet_smash', 'brebet_kaze', 'brebet_ninja'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'busi_aus' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC023 — honda_verza_karbu

- **User input**: `motor brebet di rpm 4000-5000, bensin agak boros`
- **Expected cause**: `busi_aus`
- **Predicted top-1**: `filter_udara_kotor` (conf=0.931, in_top3=False)
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'busi_aus' not in result list (top causes were ['filter_udara_kotor', 'bensin_kotor', 'main_jet_clogged']). Parser matched ['brebet', 'brebet_smash', 'brebet_kaze', 'brebet_ninja', 'bensin_boros'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'busi_aus' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.

#### RC024 — yamaha_byson_karbu

- **User input**: `tenaga hilang setelah ganti knalpot racing, brebet`
- **Expected cause**: `setelan_angin_salah`
- **Predicted top-1**: `main_jet_clogged` (conf=0.991, in_top3=False)
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'setelan_angin_salah' not in result list (top causes were ['main_jet_clogged', 'filter_udara_kotor', 'bensin_kotor']). Parser matched ['brebet', 'ngempos', 'kehilangan_tenaga', 'mesin_ngempos', 'brebet_smash', 'tenaga_hilang_smash', 'brebet_kaze', 'tenaga_hilang_kaze', 'brebet_ninja', 'tenaga_hilang_ninja'] but expected cause was filtered/scored out.
- **Recommendation**: Check why 'setelan_angin_salah' is not surfaced. May need: more relasi, higher weight, or motor-specific entry.


### 📊 RANKING GAPS (4 cases)

**Description**: Correct cause exists in result list but ranked lower than predicted. Weight tuning needed on primary relasi between matched symptoms and expected cause.


#### RC007 — honda_megapro_karbu

- **User input**: `bensin keluar dari karburator, motor bau bensin menyengat`
- **Expected cause**: `karburator_overflow`
- **Predicted top-1**: `pelampung_macet` (conf=0.978, in_top3=True)
- **Expected rank**: #3
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'karburator_overflow' is in results at rank #3 (score=7, conf=0.689). Predicted 'pelampung_macet' ranked #1 (score=23). Score delta: 16.
- **Recommendation**: Review weight on relasi between ['karburator_basah', 'bau_bensin', 'bau_bensin_menyengat'] and 'karburator_overflow'. Consider raising primary relasi weight (5→7). Verify ranking with workshop expert first.

#### RC012 — kawasaki_ninja_150

- **User input**: `asap biru, motor brebet, oli 2-tak cepat habis`
- **Expected cause**: `oil_pump_ninja_rusak`
- **Predicted top-1**: `ring_piston_aus` (conf=0.865, in_top3=True)
- **Expected rank**: #3
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'oil_pump_ninja_rusak' is in results at rank #3 (score=8, conf=0.736). Predicted 'ring_piston_aus' ranked #1 (score=12). Score delta: 4.
- **Recommendation**: Review weight on relasi between ['brebet', 'asap_biru', 'oli_bocor_seal_klep', 'brebet_smash', 'brebet_kaze', 'brebet_ninja', 'asap_biru_ninja'] and 'oil_pump_ninja_rusak'. Consider raising primary relasi weight (5→7). Verify ranking with workshop expert first.

#### RC017 — yamaha_jupiter_karbu

- **User input**: `asap biru tipis + bensin boros`
- **Expected cause**: `ring_piston_aus`
- **Predicted top-1**: `seal_klep_bocor` (conf=0.95, in_top3=True)
- **Expected rank**: #3
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'ring_piston_aus' is in results at rank #3 (score=12, conf=0.865). Predicted 'seal_klep_bocor' ranked #1 (score=18). Score delta: 6.
- **Recommendation**: Review weight on relasi between ['bensin_boros', 'boros_bensin', 'asap_biru', 'oli_bocor_seal_klep', 'asap_biru_ninja'] and 'ring_piston_aus'. Consider raising primary relasi weight (5→7). Verify ranking with workshop expert first.

#### RC021 — honda_tiger_2000

- **User input**: `ngelitik terus, tenaga hilang, brebet semua rpm`
- **Expected cause**: `klep_renggang`
- **Predicted top-1**: `main_jet_clogged` (conf=0.991, in_top3=False)
- **Status**: `ok`
- **Severity**: medium
- **Evidence**: Expected cause 'klep_renggang' is in results at rank #5 (score=14, conf=0.903). Predicted 'main_jet_clogged' ranked #1 (score=28). Score delta: 14.
- **Recommendation**: Review weight on relasi between ['brebet', 'ngempos', 'kehilangan_tenaga', 'mesin_ngempos', 'mesin_ngelitik', 'brebet_smash', 'tenaga_hilang_smash', 'brebet_kaze', 'tenaga_hilang_kaze', 'brebet_ninja', 'tenaga_hilang_ninja'] and 'klep_renggang'. Consider raising primary relasi weight (5→7). Verify ranking with workshop expert first.


### 🔗 RELASI GAPS (7 cases)

**Description**: No relasi (edge) exists between matched symptoms and expected cause in KB. Adding a new relasi (after workshop verification) would fix this gap.


#### RC002 — honda_supra_x125_karbu

- **User input**: `langsam naik turun sendiri, kadang mati sendiri`
- **Expected cause**: `karburator_kotor`
- **Predicted top-1**: `intake_leak` (conf=0.992, in_top3=False)
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['langsam_tinggi', 'langsam_turun_naik', 'mesin_mati_sendiri', 'rpm_naik_turun', 'mesin_mati_setelah_hidup'] and expected cause 'karburator_kotor'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['langsam_tinggi', 'langsam_turun_naik', 'mesin_mati_sendiri', 'rpm_naik_turun', 'mesin_mati_setelah_hidup']>, cause_id=karburator_kotor, weight=5-7. Verify with workshop expert before adding.

#### RC006 — kawasaki_kaze

- **User input**: `tarikan berat di rpm bawah, kayak mau mati terus`
- **Expected cause**: `pilot_jet_kaze_clogged`
- **Predicted top-1**: `skep_macet` (conf=0.958, in_top3=False)
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['kabel_gas_seret_gejala', 'tarikan_berat'] and expected cause 'pilot_jet_kaze_clogged'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['kabel_gas_seret_gejala', 'tarikan_berat']>, cause_id=pilot_jet_kaze_clogged, weight=5-7. Verify with workshop expert before adding.

#### RC011 — yamaha_rx_king_karbu

- **User input**: `asap biru dari knalpot, suara knalpot berisik`
- **Expected cause**: `ring_piston_aus_2_tak`
- **Predicted top-1**: `ring_piston_aus` (conf=0.865, in_top3=False)
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['asap_biru', 'oli_bocor_seal_klep', 'asap_biru_ninja'] and expected cause 'ring_piston_aus_2_tak'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['asap_biru', 'oli_bocor_seal_klep', 'asap_biru_ninja']>, cause_id=ring_piston_aus_2_tak, weight=5-7. Verify with workshop expert before adding.

#### RC016 — honda_legenda_karbu

- **User input**: `kadang hidup kadang enggak, gak stabil`
- **Expected cause**: `koil_lemah`
- **Predicted top-1**: `koil_panas` (conf=0.689, in_top3=False)
- **Status**: `ambiguous_top_results`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['rpm_tidak_stabil_byson'] and expected cause 'koil_lemah'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['rpm_tidak_stabil_byson']>, cause_id=koil_lemah, weight=5-7. Verify with workshop expert before adding.

#### RC018 — honda_blade_karbu

- **User input**: `langsam gak stabil, naik turun sendiri, kadang mati di lampu merah`
- **Expected cause**: `karburator_kotor`
- **Predicted top-1**: `intake_leak` (conf=0.982, in_top3=False)
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['langsam_tinggi', 'rpm_naik_turun', 'rpm_tidak_stabil_byson'] and expected cause 'karburator_kotor'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['langsam_tinggi', 'rpm_naik_turun', 'rpm_tidak_stabil_byson']>, cause_id=karburator_kotor, weight=5-7. Verify with workshop expert before adding.

#### RC019 — kawasaki_ninja_150

- **User input**: `motor gak ada tenaga di rpm atas, brebet terus`
- **Expected cause**: `knalpot_tersumbat_2_tak`
- **Predicted top-1**: `main_jet_clogged` (conf=0.989, in_top3=False)
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['brebet', 'mesin_ngempos', 'brebet_smash', 'brebet_kaze', 'brebet_ninja'] and expected cause 'knalpot_tersumbat_2_tak'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['brebet', 'mesin_ngempos', 'brebet_smash', 'brebet_kaze', 'brebet_ninja']>, cause_id=knalpot_tersumbat_2_tak, weight=5-7. Verify with workshop expert before adding.

#### RC022 — yamaha_mio_sporty

- **User input**: `starter elektrik gak mau mutar, suara tek tek tek`
- **Expected cause**: `aki_lemah`
- **Predicted top-1**: `klep_renggang` (conf=0.903, in_top3=True)
- **Expected rank**: #2
- **Status**: `ok`
- **Severity**: high
- **Evidence**: No relasi exists between matched symptoms ['suara_mesin_abnormal', 'suara_tek_tek'] and expected cause 'aki_lemah'. Parser matched but KB has no path.
- **Recommendation**: Add relasi: symptom_id=<one of ['suara_mesin_abnormal', 'suara_tek_tek']>, cause_id=aki_lemah, weight=5-7. Verify with workshop expert before adding.


---

## 🎯 Recommendations

Based on gap analysis:

1. **Parser gaps (1 cases)** — Add aliases for unmatched keywords. This is the highest-leverage fix if parser gaps dominate.
2. **Relasi gaps (7 cases)** — Add symptom→cause relasi for unmatched pairs. Verify with workshop expert before adding.
3. **Ranking gaps (4 cases)** — Tune weights on primary relasi. Raise weight=5→7 if consistently underconfident.
4. **KB gaps (7 cases)** — Review motor_filter / motor_type_filter. May be too restrictive for certain motor × cause combinations.

5. **Generalization check** — Re-run `tests/run_benchmark.py` after any KB change to ensure 0 regression in synthetic benchmark.

6. **Data collection** — Continue collecting real cases from workshops. Target: 100+ cases spanning all 22 motors.

---

## 📋 Dataset Sourcing Roadmap

- **Current dataset size**: 24 cases
  - Real cases (workshop/forum/user): 22
  - Synthetic (clearly marked): 2
- **Motors covered**: 19/22 (86%)
- **Target**: 50-100 real cases spanning all 22 motors
- **Remaining**: 28-78 more real cases needed

### Source distribution

| Source | Count | Status |
|---|---:|---|
| `bengkel_*` (workshop reports) | 18 | ✅ Real |
| `forum_*` (forum threads) | 0 | ⚠️ Need real forum URL sourcing |
| `user_submitted` | 4 | ✅ Real |
| `synthetic_*` | 2 | ⚠️ Clearly marked, NOT for production metrics |

### Sourcing plan to reach 100 real cases

1. **Workshop partnerships** (40 cases target)
   - Bandung: 5 bengkel partners (current: 5 cases)
   - Jakarta: 8 bengkel partners (current: 8 cases)
   - Surabaya, Depok, Yogya: expand (current: 5 cases)
   - Goal: 4-5 cases per bengkel

2. **Forum mining** (30 cases target)
   - Kaskus subforum: Bengkel & Otomotif / Motor
   - Otosia comment sections
   - Komunitas Facebook groups (need admin access)
   - Reddit r/indomotor

3. **User-submitted cases** (20 cases target)
   - Direct user reports via API (when feature live)
   - Field interviews with 10 mekanik partners

4. **Coverage gap** (10 cases target)
   - Uncovered motors: ['honda_glpro_karbu', 'yamaha_vega_karbu', 'yamaha_scorpio_karbu']

### Methodology note

- Each new case MUST be sourced from real workshop/forum/user report
- `verified_by` field should name the mekanik or forum user
- `confidence` (1-5) reflects how confident the source is in the diagnosis
- Synthetic cases are kept ONLY for development/testing — they MUST NOT influence production metrics
- Every KB change triggered by gap analysis MUST be reviewed by a workshop expert before merge

---

## 🗺 Sprint Roadmap (v1.4 → v1.5)

### v1.4 — Real-World Validation (THIS SPRINT) ✅

- [x] Build validator with schema check + engine scoring
- [x] Add precision/recall/FP/FN metrics
- [x] Add gap classification (parser / KB / ranking / relasi)
- [x] Bootstrap 24 real-world cases (22 real + 2 synthetic)
- [x] Generate VALIDATION_REPORT_v1.4.md

### v1.5 — Gap-Driven KB Improvement (PROPOSED)

Priorities (in order, data-driven):

1. **Address relasi gaps** (7 cases, ~35% of failures)
   - Add missing symptom→cause relasi (verify with workshop expert)
   - Likely fixes: knalpot_tersumbat_2_tak, aki_lemah, busi_aus for jupiter_z + others

2. **Address KB gaps** (7 cases, ~37% of failures)
   - Review motor_filter / motor_type_filter compatibility
   - Common pattern: causes valid for all motors but filtered out for specific motors

3. **Address ranking gaps** (4 cases, ~21% of failures)
   - Tune weights on existing relasi (5→7 for primary symptom)
   - Verify with workshop expert before adjusting weights

4. **Expand dataset to 50-100 real cases**
   - Workshop partnerships (primary source)
   - Forum mining (secondary)
   - User submissions (tertiary)

5. **Re-run validation + verify no synthetic benchmark regression**
