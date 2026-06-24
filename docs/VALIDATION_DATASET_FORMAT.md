# 📊 Validation Dataset Format Specification

**Versi**: 1.0
**Engine target**: Karbuin v1.1.2 (FROZEN)

---

## 📐 Skema JSON

Setiap record kasus harus mengikuti schema berikut. Field bertanda `*` wajib, sisanya opsional.

```json
{
  "case_id": "RC001",                          // * string, unique, prefix "RC"
  "ts": "2026-06-24T12:00:00Z",                // * ISO 8601 timestamp UTC
  "schema_version": 1,                         // * int, currently 1

  "motor": {                                   // * motor context
    "id": "yamaha_mio_sporty",                 // * string, must exist in KB
    "year": 2010,                              //   int, year of manufacture
    "km": 45000,                               //   int, odometer reading
  },

  "user_input": {                              // * user-described problem
    "raw": "motor brebet di tanjakan, bensin jadi boros",  // * verbatim
    "explicit_symptoms": ["brebet", "bensin_boros"],      // list of symptom_ids
    "language": "id",                          //   "id" (default) or "jv" etc
  },

  "expected": {                                // * ground truth
    "cause_id": "busi_aus",                    // * cause_id (must exist in KB)
    "fix": "ganti busi NGK CPR8EA-9",          //   action taken
    "cost_idr": 25000,                         //   actual cost in IDR
    "diy": true,                               //   true=DIY, false=mechanic
    "verified_by": "mekanik_rudi",             //   who labeled this
    "confidence": 5                            //   1-5, labeler confidence
  },

  "context": {                                 //   additional context
    "location": "Bandung",                     //   city only (NO full address)
    "year_of_incident": "2026-05",             //   YYYY-MM
    "weather": "hujan",                        //   optional
    "fuel_type": "pertamax",                   //   optional
  },

  "meta": {                                    //   data lineage
    "source": "bengkel_rudi",                  //   where this case came from
    "collector": "hybern",                     //   who collected
    "notes": "user datang setelah 3 hari brebet",
    "photo_urls": [],                          //   optional, anonymized
  }
}
```

---

## 🔍 Constraint Validation

### Field-level constraints

| Field | Type | Constraint |
|---|---|---|
| `case_id` | string | `/^RC[0-9]{3,6}$/` (e.g. RC001, RC12345) |
| `ts` | string | ISO 8601 UTC, `Z` suffix required |
| `schema_version` | int | `=1` |
| `motor.id` | string | Must be one of 8 motor IDs in `KB.motor` |
| `motor.year` | int | `1990 <= year <= 2025` |
| `user_input.raw` | string | `5 <= len <= 1000` |
| `user_input.explicit_symptoms` | list | Each element must be valid `symptom_id` in `KB.gejala` |
| `expected.cause_id` | string | Must exist in `KB.penyebab` |
| `expected.cost_idr` | int | `0 <= cost <= 5000000` (Rp 0 - 5 juta) |
| `expected.confidence` | int | `1 <= confidence <= 5` |
| `context.year_of_incident` | string | `/^\d{4}-\d{2}$/` |
| `meta.source` | string | one of: `bengkel_<name>`, `forum_<name>`, `survey`, `user_submitted`, `synthetic_<name>` |

### Cross-record constraints

- **Unique case_id**: Tidak boleh ada duplicate case_id dalam 1 file
- **No PII**: case_id tidak boleh contain nama, no HP, email, atau identifier pribadi
- **No test pack duplicates**: case_id TIDAK boleh match dengan yang ada di `data/test_pack/`
- **Motor must exist**: motor.id harus ada di KB engine (validated via `KB.motor`)

---

## ✅ Validation Script (built-in)

File: `scripts/validate_real_cases.py`

```python
"""Validate real_cases.jsonl against schema and KB."""
import json
import sys
from pathlib import Path
from karbuin import KB


VALID_SOURCES = (
    "bengkel_", "forum_", "survey",
    "user_submitted", "synthetic_",
)
MOTOR_IDS = {m["id"] for m in KB.motor}
PENYEBAB_IDS = {p["id"] for p in KB.penyebab}
GEJALA_IDS = {g["id"] for g in KB.gejala}


def validate_record(rec: dict, line_no: int) -> list[str]:
    """Return list of errors (empty if valid)."""
    errors = []
    required = ["case_id", "ts", "schema_version", "motor", "user_input", "expected"]
    for k in required:
        if k not in rec:
            errors.append(f"L{line_no}: missing required field '{k}'")

    if "case_id" in rec and not rec["case_id"].startswith("RC"):
        errors.append(f"L{line_no}: case_id must start with 'RC'")

    if "motor" in rec:
        mid = rec["motor"].get("id")
        if mid not in MOTOR_IDS:
            errors.append(f"L{line_no}: motor.id '{mid}' not in KB")

    if "user_input" in rec:
        for sid in rec["user_input"].get("explicit_symptoms", []):
            if sid not in GEJALA_IDS:
                errors.append(f"L{line_no}: symptom '{sid}' not in KB")

    if "expected" in rec:
        cid = rec["expected"].get("cause_id")
        if cid not in PENYEBAB_IDS:
            errors.append(f"L{line_no}: cause_id '{cid}' not in KB")

    if "meta" in rec:
        src = rec["meta"].get("source", "")
        if not any(src.startswith(s) for s in VALID_SOURCES):
            errors.append(f"L{line_no}: source '{src}' invalid (must start with one of {VALID_SOURCES})")

    return errors


def main():
    path = Path("data/real_cases.jsonl")
    if not path.exists():
        print(f"❌ {path} not found")
        sys.exit(1)

    total = 0
    valid = 0
    all_errors = []
    seen_ids = set()

    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            total += 1
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                all_errors.append(f"L{line_no}: invalid JSON: {e}")
                continue

            errors = validate_record(rec, line_no)
            if rec.get("case_id") in seen_ids:
                errors.append(f"L{line_no}: duplicate case_id '{rec.get('case_id')}'")
            seen_ids.add(rec.get("case_id"))

            if not errors:
                valid += 1
            else:
                all_errors.extend(errors)

    print(f"📊 Validation Report")
    print(f"   Total: {total}")
    print(f"   Valid: {valid}")
    print(f"   Invalid: {total - valid}")
    if all_errors:
        print(f"\n❌ Errors:")
        for e in all_errors[:50]:
            print(f"   {e}")
        sys.exit(1)
    else:
        print(f"\n✅ All records valid")


if __name__ == "__main__":
    main()
```

---

## 🧪 Validation Engine Output

Saat dataset di-score dengan engine Karbuin:

```json
{
  "dataset": "data/real_cases.jsonl",
  "total_cases": 100,
  "valid_cases": 98,
  "metrics": {
    "top1_accuracy": 0.84,
    "top3_accuracy": 0.96,
    "rejected_rate": 0.06,
    "avg_confidence_correct": 0.85,
    "avg_confidence_wrong": 0.62,
    "confidence_calibration_gap": 0.23
  },
  "by_motor": {
    "yamaha_mio_sporty": {"total": 25, "correct": 22, "accuracy": 0.88},
    "honda_supra_x125_karbu": {"total": 18, "correct": 14, "accuracy": 0.78},
    ...
  },
  "by_cause": {
    "busi_aus": {"total": 12, "correct": 11, "accuracy": 0.92},
    ...
  },
  "failure_cases": [
    {
      "case_id": "RC042",
      "motor_id": "honda_supra_x125_karbu",
      "user_input": "motor mati mendadak di jalan",
      "expected": "cdi_rusak",
      "predicted_top": "bensin_habis",
      "predicted_conf": 0.45,
      "predicted_in_top3": false
    }
  ]
}
```

---

## 📝 Contoh Lengkap

File: `data/real_cases.jsonl` (3 sample cases)

```jsonl
{"case_id":"RC001","ts":"2026-05-15T10:00:00Z","schema_version":1,"motor":{"id":"yamaha_mio_sporty","year":2010,"km":45000},"user_input":{"raw":"motor brebet di tanjakan, bensin jadi boros dari kemarin","explicit_symptoms":["brebet","bensin_boros"],"language":"id"},"expected":{"cause_id":"busi_aus","fix":"ganti busi NGK CPR8EA-9","cost_idr":25000,"diy":true,"verified_by":"mekanik_rudi","confidence":5},"context":{"location":"Bandung","year_of_incident":"2026-05","weather":"hujan","fuel_type":"pertamax"},"meta":{"source":"bengkel_rudi","collector":"hybern","notes":"user datang setelah 3 hari brebet, busi lama sudah hitam"}}
{"case_id":"RC002","ts":"2026-04-20T14:30:00Z","schema_version":1,"motor":{"id":"honda_supra_x125_karbu","year":2015,"km":28000},"user_input":{"raw":"langsam naik turun sendiri, kadang mati sendiri","explicit_symptoms":["langsam_turun_naik"],"language":"id"},"expected":{"cause_id":"karburator_kotor","fix":"bersihkan karburator + setel langsam baut","cost_idr":75000,"diy":false,"verified_by":"mekanik_jakarta","confidence":4},"context":{"location":"Jakarta","year_of_incident":"2026-04","fuel_type":"pertalite"},"meta":{"source":"bengkel_jakarta","collector":"hybern","notes":"setelah dibersihkan, langsam stabil di 1200 RPM"}}
{"case_id":"RC003","ts":"2026-03-10T09:15:00Z","schema_version":1,"motor":{"id":"yamaha_jupiter_z_karbu","year":2012,"km":62000},"user_input":{"raw":"susah hidup pagi, harus diengkol berkali-kali","explicit_symptoms":["susah_hidup_pagi"],"language":"id"},"expected":{"cause_id":"busi_aus","fix":"ganti busi + bersihkan karburator","cost_idr":50000,"diy":true,"verified_by":"user_sendiri","confidence":3},"context":{"location":"Surabaya","year_of_incident":"2026-03","fuel_type":"pertamax"},"meta":{"source":"user_submitted","collector":"hybern","notes":"user kerjain sendiri, hasilnya motor hidup normal pagi hari"}}
```

---

## 🚫 Anti-pattern: Schema Violations

### ❌ WRONG: PII included
```json
{"case_id": "RC_agus_123", "user_input": "..."}
```
❌ `case_id` mengandung nama

### ❌ WRONG: motor doesn't exist in KB
```json
{"motor": {"id": "honda_vario_125_injection"}}
```
❌ Karbuin HANYA support 8 motor karbu. Injeksi bukan target.

### ❌ WRONG: cause_id tidak ada di KB
```json
{"expected": {"cause_id": "mesin_overheat_jebol"}}
```
❌ Pakai cause_id yang sudah ada di `data/seed/penyebab.json` (32 entries)

### ❌ WRONG: user_input terlalu pendek
```json
{"user_input": {"raw": "brebet"}}
```
⚠️ Ini akan di-validate sebagai "too short" (< 5 chars). Minimal harus ada konteks.

### ❌ WRONG: missing required field
```json
{"case_id": "RC099", "motor": {...}}
```
❌ Missing `ts`, `schema_version`, `user_input`, `expected`

---

## 🔄 Schema Evolution

### Bump version
Kalau ada field baru atau constraint berubah:
1. Tambah `"schema_version": 2`
2. Update validator di `scripts/validate_real_cases.py`
3. Backward-compat: validator harus bisa handle schema v1 records
4. Migrate existing records via `scripts/migrate_v1_to_v2.py`

### Reserved fields (future)
- `user_input.audio`: untuk transkrip suara (future feature)
- `expected.alternative_causes`: list of other possible causes
- `meta.peer_reviewed`: bool, untuk review process

---

## 📞 Reference

- Schema inspired by: [Datasheets for Datasets](https://arxiv.org/abs/1803.01010) (Gebru et al.)
- Validation pattern: JSON Schema (informal, Python-native)
- Karbuin KB source: `data/seed/motor.json`, `data/seed/penyebab.json`, `data/seed/gejala.json`

---

**Engine FROZEN**: Format spec ini stabil untuk Karbuin v1.x. Breaking changes hanya di v2.0.