"""Karbuin Telemetry — append-only JSON Lines logger.

Privacy-by-default:
- NO PII stored
- IP is hashed (SHA256, first 16 chars)
- No cookies, no sessions
- User input stored in full (it's the diagnostic content, needed for analysis)
- User-Agent stored (helps identify Android vs PC for UX)

Events:
- diagnose: initial call
- followup: follow-up answer
- error: server error

Storage: data/telemetry/YYYY-MM-DD.jsonl
Rotation: new file per day, 30 days retention
"""
from __future__ import annotations
import json
import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

DATA_DIR = Path(__file__).parent.parent / "data" / "telemetry"
DATA_DIR.mkdir(parents=True, exist_ok=True)

_lock = Lock()
_today = None
_fh = None


def _get_file():
    global _today, _fh
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if _today != today:
        if _fh:
            _fh.close()
        _today = today
        path = DATA_DIR / f"{today}.jsonl"
        _fh = path.open("a", encoding="utf-8", buffering=1)  # line-buffered
    return _fh


def _hash_ip(ip: str) -> str:
    if not ip:
        return "unknown"
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def log_diagnose(
    *,
    user_input: str,
    motor_id: str,
    explicit_symptoms: list | None,
    result: dict,
    user_agent: str,
    ip: str,
) -> None:
    """Log a diagnose call. Result is the full API response."""
    top = result.get("results", [{}])[0] if result.get("results") else {}
    top_cause = top.get("cause", {})
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "diagnose",
        "ip_hash": _hash_ip(ip),
        "ua": user_agent[:200],
        "user_input": user_input[:500],
        "motor_id": motor_id or "",
        "explicit_symptoms": explicit_symptoms or [],
        "parsed_symptoms": result.get("parsed_symptoms", []),
        "result_status": result.get("status", "unknown"),
        "result_count": len(result.get("results", [])),
        "top_cause_id": top_cause.get("id", ""),
        "top_cause_name": top_cause.get("name", ""),
        "top_confidence": top.get("confidence", 0),
        "top_tier": top.get("confidence_tier", ""),
        "all_causes": [
            {
                "id": r.get("cause", {}).get("id", ""),
                "name": r.get("cause", {}).get("name", ""),
                "confidence": r.get("confidence", 0),
            }
            for r in result.get("results", [])[:5]
        ],
    }
    _write(event)


def log_followup(
    *,
    user_input: str,
    motor_id: str,
    explicit_symptoms: list | None,
    answers: dict,
    adjustments: dict,
    result: dict,
    user_agent: str,
    ip: str,
) -> None:
    """Log a follow-up answer."""
    top = result.get("results", [{}])[0] if result.get("results") else {}
    top_cause = top.get("cause", {})
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "followup",
        "ip_hash": _hash_ip(ip),
        "ua": user_agent[:200],
        "user_input": user_input[:500],
        "motor_id": motor_id or "",
        "explicit_symptoms": explicit_symptoms or [],
        "answers": answers,
        "adjustments": adjustments,
        "top_cause_id": top_cause.get("id", ""),
        "top_cause_name": top_cause.get("name", ""),
        "top_confidence": top.get("confidence", 0),
        "all_causes": [
            {
                "id": r.get("cause", {}).get("id", ""),
                "confidence": r.get("confidence", 0),
            }
            for r in result.get("results", [])[:5]
        ],
    }
    _write(event)


def log_error(*, endpoint: str, error: str, user_input: str, user_agent: str, ip: str) -> None:
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": "error",
        "ip_hash": _hash_ip(ip),
        "ua": user_agent[:200],
        "endpoint": endpoint,
        "error": error[:200],
        "user_input": user_input[:200],
    }
    _write(event)


def _write(event: dict) -> None:
    try:
        with _lock:
            fh = _get_file()
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        # Never let logging crash the request
        print(f"[telemetry] write failed: {e}", flush=True)


# ── Analytics ────────────────────────────────────────────────────────

import csv
import io


def _iter_events(days: int = 7, event_type: str | None = None):
    """Yield parsed JSONL events from last N days (newest first).

    event_type: filter by 'diagnose', 'followup', 'error' (None = all)
    """
    files = sorted(DATA_DIR.glob("*.jsonl"), reverse=True)[:days]
    for path in files:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event_type and ev.get("event") != event_type:
                    continue
                yield ev


def stats(days: int = 7) -> dict:
    """Aggregate stats from the last N days of log files."""
    counts = {
        "diagnose": 0,
        "followup": 0,
        "error": 0,
    }
    top_causes = {}
    motors = {}
    inputs_sample = []
    confidence_sum = 0
    confidence_n = 0
    ua_buckets = {"mobile": 0, "desktop": 0, "bot": 0, "other": 0}
    daily = {}

    for ev in _iter_events(days=days):
        ev_type = ev.get("event", "unknown")
        counts[ev_type] = counts.get(ev_type, 0) + 1
        # Daily breakdown
        ts = ev.get("ts", "")[:10]  # YYYY-MM-DD
        if ts:
            daily.setdefault(ts, {"diagnose": 0, "followup": 0, "error": 0})
            if ev_type in daily[ts]:
                daily[ts][ev_type] += 1
        # UA classification
        ua = (ev.get("ua") or "").lower()
        if "bot" in ua or "spider" in ua or "crawler" in ua:
            ua_buckets["bot"] += 1
        elif "mobile" in ua or "android" in ua or "iphone" in ua or "ipad" in ua:
            ua_buckets["mobile"] += 1
        elif "mozilla" in ua or "chrome" in ua or "safari" in ua:
            ua_buckets["desktop"] += 1
        else:
            ua_buckets["other"] += 1
        # Diagnose-specific stats
        if ev_type == "diagnose":
            mid = ev.get("motor_id", "unknown")
            motors[mid] = motors.get(mid, 0) + 1
            cid = ev.get("top_cause_id", "unknown")
            if cid and cid != "rejected":
                top_causes[cid] = top_causes.get(cid, 0) + 1
            conf = ev.get("top_confidence", 0)
            if conf:
                confidence_sum += conf
                confidence_n += 1
            ui = ev.get("user_input", "")
            if ui and len(inputs_sample) < 50:
                inputs_sample.append(ui)

    avg_conf = confidence_sum / confidence_n if confidence_n else 0
    return {
        "days": days,
        "totals": counts,
        "total_events": sum(counts.values()),
        "avg_top_confidence": round(avg_conf, 4),
        "top_causes_top10": sorted(top_causes.items(), key=lambda x: -x[1])[:10],
        "motors_breakdown": sorted(motors.items(), key=lambda x: -x[1]),
        "ua_breakdown": ua_buckets,
        "daily_breakdown": sorted(daily.items(), reverse=True),
        "input_samples": inputs_sample,
    }


def export_csv(days: int = 7, event_type: str | None = None) -> str:
    """Export telemetry events to CSV string.

    Columns (always present):
      ts, event, ip_hash, ua, motor_id, user_input, parsed_symptoms,
      explicit_symptoms, top_cause_id, top_cause_name, top_confidence,
      top_tier, result_status

    Optional columns (when present in event):
      answers, adjustments, result_count, all_causes, endpoint, error
    """
    buf = io.StringIO()
    fieldnames = [
        "ts", "event", "ip_hash", "ua", "motor_id", "user_input",
        "parsed_symptoms", "explicit_symptoms",
        "top_cause_id", "top_cause_name", "top_confidence", "top_tier",
        "result_status", "result_count",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for ev in _iter_events(days=days, event_type=event_type):
        row = {
            "ts": ev.get("ts", ""),
            "event": ev.get("event", ""),
            "ip_hash": ev.get("ip_hash", ""),
            "ua": ev.get("ua", ""),
            "motor_id": ev.get("motor_id", ""),
            "user_input": ev.get("user_input", ""),
            "parsed_symptoms": json.dumps(ev.get("parsed_symptoms", []), ensure_ascii=False),
            "explicit_symptoms": json.dumps(ev.get("explicit_symptoms", []), ensure_ascii=False),
            "top_cause_id": ev.get("top_cause_id", ""),
            "top_cause_name": ev.get("top_cause_name", ""),
            "top_confidence": ev.get("top_confidence", ""),
            "top_tier": ev.get("top_tier", ""),
            "result_status": ev.get("result_status", ""),
            "result_count": ev.get("result_count", ""),
        }
        writer.writerow(row)
    return buf.getvalue()


def query_recent(limit: int = 50, event_type: str | None = None) -> list:
    """Return the most recent N events (newest first)."""
    events = list(_iter_events(days=30, event_type=event_type))
    events.reverse()  # newest first
    return events[:limit]


if __name__ == "__main__":
    # Test
    log_diagnose(
        user_input="brebet saat tanjakan",
        motor_id="yamaha_mio_sporty",
        explicit_symptoms=None,
        result={
            "status": "ok",
            "parsed_symptoms": [{"id": "brebet", "name": "Brebet"}],
            "results": [{"cause": {"id": "bensin_kotor", "name": "Bensin Kotor"}, "confidence": 0.85}],
        },
        user_agent="test",
        ip="127.0.0.1",
    )
    print("Test event logged.")
    s = stats(days=1)
    print(f"Stats: {s}")
