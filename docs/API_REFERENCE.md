# 📡 Karbuin API Reference

**Version**: v1.3.7
**Base URL**: `https://<your-domain>/` (or `http://localhost:8000/` for local)
**Auth**: NONE (public read-only API)
**Content-Type**: `application/json` for POST/GET responses, `text/csv` for CSV

---

## 📑 Index

- [Public Pages (HTML)](#public-pages-html)
- [Diagnose API](#diagnose-api)
- [Knowledge Base APIs](#knowledge-base-apis)
- [Parser APIs](#parser-apis)
- [Telemetry APIs](#telemetry-apis)

---

## 🌐 Public Pages (HTML)

| Route | Description | Notes |
|---|---|---|
| `GET /` | Landing page | Motor selection CTA |
| `GET /diagnose` | Diagnose form | Input symptoms, motor picker |
| `GET /result` | Result page | Causes ranked, share buttons |
| `GET /library` | Komponen library | 30 components, click for detail |
| `GET /method` | Method documentation | How engine works |
| `GET /dashboard` | Telemetry dashboard | Stats, top causes, recent events |
| `GET /qa-harness` | Mobile QA test harness | 3-iframe mobile viewports (testing only) |

**Note**: `GET /result` requires `?motor=<id>&input=<text>&explicit=<csv>` params.

---

## 🩺 Diagnose API

### POST /api/diagnose

Primary diagnosis endpoint. Takes user input + optional motor selection.

**Request**:
```http
POST /api/diagnose
Content-Type: application/json

{
  "motor_id": "yamaha_mio_sporty",
  "user_input": "motor brebet di tanjakan, bensin jadi boros",
  "explicit_symptoms": ["brebet", "bensin_boros"]
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `motor_id` | string | No | One of 22 motor IDs (or `null`) |
| `user_input` | string | Yes | Raw keluhan user, 5-1000 chars |
| `explicit_symptoms` | list | No | Array of symptom IDs (chips) |

**Response 200 OK**:
```json
{
  "status": "ok",
  "motor_id": "yamaha_mio_sporty",
  "is_followup": false,
  "parsed_symptoms": [
    {"id": "brebet", "name": "Brebet", "confidence": 0.85}
  ],
  "explicit_symptoms": ["brebet", "bensin_boros"],
  "all_symptoms": [...],
  "confirmed_causes": [],
  "results": [
    {
      "cause": {
        "id": "filter_udara_kotor",
        "name": "Filter Udara Kotor",
        "aliases": ["filter kotor", "filter udara tersumbat"],
        "description": "...",
        "diagnosis_method": "Lepas filter, periksa warna...",
        "risk_level": "kuning",
        "diy_level": "hijau"
      },
      "score": 12.5,
      "max_possible": 15.0,
      "confidence": 0.93,
      "tier_label": "sangat_tinggi",
      "matched_symptoms": [...],
      "matched_relations": [...],
      "components": [...],
      "solutions": [...],
      "prices": [...],
      "images": [...],
      "locations": [...],
      "reasoning": "...",
      "estimated_minutes": 15,
      "follow_up_questions": [...]
    }
  ],
  "location_summary": {...},
  "ringkasan": "...",
  "summary": "...",
  "follow_up_questions": [
    {
      "id": "fu_001",
      "question": "Apakah filter udara baru diganti?",
      "type": "yes_no"
    }
  ],
  "presentation": {
    "summary_card": {
      "headline": "Filter Udara Kotor — 93%",
      "subline": "Diagnosis utama berdasarkan 2 gejala cocok",
      "total_alternatives": 2
    },
    "top_3": [
      {
        "rank": 1,
        "cause_id": "filter_udara_kotor",
        "cause_name": "Filter Udara Kotor",
        "category": "fuel",
        "confidence": 0.93,
        "confidence_pct": "93%",
        "tier_label": "Sangat mungkin",
        "severity": "Aman dipakai",
        "diy": "Mudah",
        "time": "15 menit"
      }
    ],
    "checklist": [
      {
        "step": "Lepas filter udara, periksa warna. Jika hitam/gelap = kotor...",
        "component_id": "filter_udara",
        "component_name": "Filter Udara",
        "tools_needed": ["obeng plus", "kain lap"],
        "difficulty": "easy",
        "related_cause": "filter_udara_kotor",
        "cause_rank": 1
      }
    ],
    "total_results": 3
  }
}
```

**Note**: Field names are exact (e.g. `tier_label`, `max_possible`, `components` plural) — see `karbuin/diagnose.py` for full schema.

**Response 200 (no match)**:
```json
{
  "status": "no_symptom_match",
  "motor_id": "yamaha_mio_sporty",
  "parsed_symptoms": [],
  "message": "Maaf, kami tidak mengenali gejala yang Anda sebutkan."
}
```

**Status codes**:
- `200`: success (regardless of match status, check `status` field)
- `400`: invalid request (missing user_input, too long, etc.)
- `500`: server error

---

### POST /api/diagnose/followup

Submit answer to a follow-up question. Re-ranks causes based on answer.

**Request**:
```http
POST /api/diagnose/followup
Content-Type: application/json

{
  "motor_id": "yamaha_mio_sporty",
  "user_input": "motor brebet",
  "answers": {
    "fu_001": "yes"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `motor_id` | string | Yes | Same as initial diagnose |
| `user_input` | string | Yes | Same as initial diagnose |
| `answers` | dict | Yes | Map of question_id to answer value |

**Response**: Same shape as `/api/diagnose`, with re-ranked results.

---

## 📚 Knowledge Base APIs

### GET /api/motors

List all supported motors.

**Response**:
```json
{
  "motors": [
    {
      "id": "yamaha_mio_sporty",
      "name": "Yamaha Mio Sporty",
      "type": "moped",
      "engine": "115cc karburator",
      "production_years": "2003-2012"
    },
    ...
  ]
}
```

**Total**: 8 motors (all karburator type).

---

### GET /api/komponen

List all komponen (motor parts).

**Response**:
```json
{
  "komponen": [
    {
      "id": "filter_udara",
      "name": "Filter Udara",
      "category": "intake",
      "lokasi_default": ["housing filter", "sisi kiri mesin"],
      "image_id": "filter_udara_default"
    },
    ...
  ]
}
```

**Total**: 30 komponen.

---

### GET /api/gejala

List all gejala (symptoms) with parser keywords.

**Response**:
```json
{
  "gejala": [
    {
      "id": "brebet",
      "name": "Brebet",
      "keywords": ["brebet", "sebret", "nyendat", "tersendat"],
      "category": "performance"
    },
    ...
  ]
}
```

**Total**: 25 gejala.

---

### GET /api/stats

KB coverage statistics.

**Response**:
```json
{
  "motor": 22,
  "komponen": 108,
  "gejala": 192,
  "penyebab": 100,
  "relasi": 668,
  "relasi_verified": 110,
  "solusi": 96,
  "harga": 24,
  "harga_verified": 24,
  "lokasi_total": 163,
  "lokasi_verified": 163,
  "image_total": 108,
  "image_verified": 108,
  "sumber_referensi": 31,
  "motor_coverage": {...}
}
```

---

### GET /api/health

Server liveness check + KB load status. Use for monitoring/heartbeat.

**Response 200**:
```json
{
  "status": "ok",
  "version": "1.3.7",
  "kb_version": "v1.3.7 (22 motor / 192 gejala / 668 relasi)",
  "kb_loaded": true,
  "kb_stats": {
    "motor": 22,
    "gejala": 192,
    "komponen": 108,
    "penyebab": 100,
    "relasi": 668
  },
  "endpoints_count": 14,
  "timestamp": 1782341666
}
```

**Response 500** (KB load failed):
```json
{
  "status": "error",
  "version": "1.3.7",
  "error": "<error message>"
}
```

---

### GET /api/version

App + KB + engine version info. Static response, no KB access.

**Response**:
```json
{
  "app": "1.3.7",
  "kb": "v1.3.7 (22 motor / 192 gejala / 668 relasi)",
  "engine": "karbuin.diagnose.Diagnoser",
  "server": "stdlib http.server (no external deps)"
}
```

---

## 🔍 Parser APIs

### GET /api/quick-chips

Quick symptom chips shown on diagnose page load.

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `motor_id` | string | (none) | Filter chips by motor |

**Response**:
```json
{
  "chips": [
    {"id": "brebet", "label": "Brebet", "icon": "⚡"},
    {"id": "susah_hidup_pagi", "label": "Susah Hidup Pagi", "icon": "🌅"},
    ...
  ]
}
```

**Total**: 15 quick chips.

---

### POST /api/parser/preview

Parse user input into symptoms without running diagnose.

**Request**:
```http
POST /api/parser/preview
Content-Type: application/json

{
  "user_input": "motor brebet di tanjakan, bensin boros"
}
```

**Response**:
```json
{
  "parsed": [
    {"symptom_id": "brebet", "matched_phrase": "brebet", "confidence": 0.85},
    {"symptom_id": "bensin_boros", "matched_phrase": "bensin boros", "confidence": 0.85}
  ]
}
```

**Note**: Returns only `parsed` field. Use `/api/diagnose` for full ranked causes.

---

---

## 📊 Telemetry APIs

### GET /api/telemetry

Aggregate statistics for last N days.

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | 7 | Window size (1-90) |

**Response**:
```json
{
  "totals": {"diagnose": 40, "followup": 5, "error": 0},
  "avg_top_confidence": 0.836,
  "ua_breakdown": {"mobile": 0, "desktop": 36, "bot": 0, "other": 9},
  "daily_breakdown": [
    ["2026-06-24", {"diagnose": 40, "followup": 5, "error": 0}]
  ],
  "top_causes_top10": [["filter_udara_kotor", 17], ["busi_aus", 13], ...],
  "motors_breakdown": [["yamaha_mio_sporty", 22], ["honda_supra_x125_karbu", 17], ...],
  "input_samples": ["brebet di tanjakan", ...]
}
```

---

### GET /api/telemetry/csv

Download telemetry as CSV.

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `days` | int | 7 | Window size |
| `event` | string | (all) | Filter: `diagnose`, `followup`, `error` |

**Response**: `text/csv` with Content-Disposition header.
```
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="karbuin-telemetry-7d.csv"

ts,event,ip_hash,ua,motor_id,user_input,parsed_symptoms,explicit_symptoms,top_cause_id,top_cause_name,top_confidence,top_tier,result_status,result_count
2026-06-24T12:28:06.830107+00:00,diagnose,12ca17b49af22894,...
```

**Columns**: 14 (ts, event, ip_hash, ua, motor_id, user_input, parsed_symptoms, explicit_symptoms, top_cause_id, top_cause_name, top_confidence, top_tier, result_status, result_count)

---

### GET /api/telemetry/recent

Latest N events (raw JSON, newest first).

**Query params**:
| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 50 | Max 200 |
| `event` | string | (all) | Filter by event type |

**Response**:
```json
[
  {
    "ts": "2026-06-24T14:16:31.891303+00:00",
    "event": "diagnose",
    "ip_hash": "12ca17b49af22894",
    "ua": "Mozilla/5.0...",
    "user_input": "brebet",
    "motor_id": "yamaha_mio_sporty",
    "explicit_symptoms": [],
    "parsed_symptoms": [{"symptom_id": "brebet", ...}],
    "top_cause_id": "bensin_kotor",
    "top_cause_name": "Bensin Kotor / Air di Bensin",
    "top_confidence": 0.736,
    "result_status": "ok",
    "result_count": 5,
    "all_causes": [...]
  }
]
```

---

## 🔒 Privacy Notes

- **NO login system** — every request is anonymous
- **IP hashed** — SHA256 first 16 chars stored, not raw
- **User input stored verbatim** — diagnostic content, allowed
- **Cookies**: NONE
- **Session**: NONE
- **CORS**: Same-origin only

---

## ⚠️ Errors

All errors return JSON:
```json
{"error": "Bad Request", "message": "user_input required"}
```

| Status | Meaning |
|---|---|
| `400` | Bad request (missing/invalid params) |
| `404` | Endpoint not found |
| `405` | Method not allowed |
| `500` | Internal server error |

---

## 🧪 Rate Limits

**None enforced** — but please be reasonable. Target is MVP validation, not production DDoS protection.

If abused, IP-hash rate limiting can be added in v2.

---

## 📦 Versions

- **v1.1.2** (current, FROZEN): all endpoints above
- **v1.0.0-mvp**: initial release (subset)
- **v2.0.0** (planned): `/api/auth`, `/api/cases` (user-submitted real cases)

---

## 🔗 Related Files

- `server.py` — HTTP route handlers
- `karbuin/diagnose.py` — Diagnoser logic
- `karbuin/telemetry.py` — Telemetry analytics
- `ui/dashboard.html` — Telemetry dashboard UI
- `docs/TELEMETRY_AUDIT.md` — Telemetry field audit

---

**Last updated**: 2026-06-24
**Maintained by**: Karbuin Curator (karbuin@karbuin.id)