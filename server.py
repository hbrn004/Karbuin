"""Karbuin — Minimal HTTP server (stdlib only).

Routes:
  GET  /                          → ui/index.html
  GET  /diagnose                  → ui/diagnose.html
  GET  /result                    → ui/result.html
  GET  /library                   → ui/library.html
  GET  /method                    → ui/method.html
  GET  /static/...                → ui/assets/...
  GET  /api/motors                → list of all motors
  GET  /api/motors/search?q=...   → search motors
  GET  /api/motors/<id>           → motor detail
  GET  /api/komponen              → list of all components
  GET  /api/komponen/<id>         → component detail
  GET  /api/gejala                → list of all gejala (for quick chips)
  GET  /api/penyebab/<id>         → cause detail
  GET  /api/health                → server liveness + KB stats
  GET  /api/version               → server + engine version
  POST /api/diagnose              → run diagnosis (body: {motor_id, user_input, explicit_symptoms})
                                     Response includes `presentation` wrapper: top_3, checklist, summary_card
  POST /api/diagnose/followup     → re-run with follow-up (body: {motor_id, user_input, explicit_symptoms, confirmed_causes, answer_adjustments})
  POST /api/parser/preview        → preview parser matches for free text

Usage: python3 server.py [--port 8000]
"""
from __future__ import annotations
import os  # noqa: E402 — used for env vars (PORT, HOST, KARBUIN_VERSION)

import argparse
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).parent.resolve()
UI_DIR = ROOT / "ui"
DATA_DIR = ROOT / "data" / "seed"

# Lazy import karbuin (only when needed)
sys.path.insert(0, str(ROOT))
from karbuin import KnowledgeBase, Diagnoser  # noqa: E402
from karbuin import telemetry  # noqa: E402
from karbuin.presentation import build_presentation  # noqa: E402

KB = KnowledgeBase(DATA_DIR)
DIAGNOSER = Diagnoser(KB)
SERVER_START_TIME = os.environ.get("KARBUIN_SERVER_START", "unknown")
APP_VERSION = "1.3.7"
KB_VERSION = "v1.3.7 (22 motor / 192 gejala / 668 relasi)"


# ─── API helpers ────────────────────────────────────────────────────────────


def json_response(handler, status: int, body: dict | list):
    payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    handler.wfile.write(payload)


def search_motors(q: str) -> list[dict]:
    """Fuzzy search motors by brand/model/alias."""
    if not q:
        return [
            {
                "id": m["id"],
                "brand": m["brand"],
                "model": m["model"],
                "year_range": m.get("year_range", ""),
                "carb_type": m.get("carb_type", ""),
            }
            for m in KB.motor
        ]
    q_lower = q.lower().strip()
    results = []
    for m in KB.motor:
        haystack = " ".join([
            m.get("brand", ""),
            m.get("model", ""),
            m.get("year_range", ""),
            " ".join(m.get("aliases", [])),
        ]).lower()
        if q_lower in haystack:
            results.append({
                "id": m["id"],
                "brand": m["brand"],
                "model": m["model"],
                "year_range": m.get("year_range", ""),
                "carb_type": m.get("carb_type", ""),
                "match_score": sum(1 for word in q_lower.split() if word in haystack),
            })
    results.sort(key=lambda r: r.get("match_score", 0), reverse=True)
    return results


def list_quick_chips() -> list[dict]:
    """Return top gejala as quick chips for the input form."""
    out = []
    for g in KB.gejala[:15]:
        out.append({
            "id": g["id"],
            "label": g["name"],
            "aliases_sample": g.get("aliases", [])[:2],
        })
    return out


def list_komponen_with_meta() -> list[dict]:
    """List all components with relevant metadata for the library page."""
    out = []
    for k in KB.komponen:
        # count related causes
        cause_count = sum(1 for p in KB.penyebab if k["id"] in p.get("related_components", []))
        out.append({
            **k,
            "cause_count": cause_count,
        })
    return out


def get_komponen_detail(komp_id: str) -> dict | None:
    """Component detail with related causes + gejala if rusak."""
    k = KB.get_komponen(komp_id)
    if not k:
        return None
    related_causes = []
    for p in KB.penyebab:
        if komp_id in p.get("related_components", []):
            related_causes.append({
                "id": p["id"],
                "name": p["name"],
                "description": p.get("description", ""),
                "severity": p.get("severity", "low"),
                "risk_level": p.get("risk_level", "low"),
                "diy_level": p.get("diy_level", "menengah"),
            })
    related_gejala = []
    for gid in k.get("common_symptoms_if_failed", []):
        g = KB.get_gejala(gid)
        if g:
            related_gejala.append({"id": g["id"], "name": g["name"]})
    return {
        **k,
        "related_causes": related_causes,
        "related_gejala": related_gejala,
    }


# ─── Request handler ────────────────────────────────────────────────────────


class KarbuinHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # Quieter logs
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")

    def do_GET(self):
        path = urlparse(self.path).path
        query = parse_qs(urlparse(self.path).query)

        # ── API ──────────────────────────────────────────────
        if path == "/api/motors":
            return json_response(self, 200, KB.motor)
        if path == "/api/motors/search":
            q = (query.get("q") or [""])[0]
            return json_response(self, 200, search_motors(q))
        if path.startswith("/api/motors/"):
            mid = path.split("/api/motors/")[1]
            m = KB.get_motor(mid)
            if not m:
                return json_response(self, 404, {"error": "motor_not_found"})
            return json_response(self, 200, m)

        if path == "/api/komponen":
            return json_response(self, 200, list_komponen_with_meta())
        if path.startswith("/api/komponen/"):
            kid = path.split("/api/komponen/")[1]
            k = get_komponen_detail(kid)
            if not k:
                return json_response(self, 404, {"error": "komponen_not_found"})
            return json_response(self, 200, k)

        if path == "/api/gejala":
            return json_response(self, 200, KB.gejala)
        if path == "/api/quick-chips":
            return json_response(self, 200, list_quick_chips())

        if path.startswith("/api/penyebab/"):
            pid = path.split("/api/penyebab/")[1]
            p = KB.get_penyebab(pid)
            if not p:
                return json_response(self, 404, {"error": "penyebab_not_found"})
            return json_response(self, 200, p)

        if path == "/api/stats":
            return json_response(self, 200, KB.coverage_stats())
        if path == "/api/health":
            import time
            try:
                stats = KB.coverage_stats()
                kb_ok = stats.get("motor", 0) > 0
                return json_response(self, 200, {
                    "status": "ok" if kb_ok else "degraded",
                    "version": APP_VERSION,
                    "kb_version": KB_VERSION,
                    "kb_loaded": kb_ok,
                    "kb_stats": {
                        "motor": stats.get("motor", 0),
                        "gejala": stats.get("gejala", 0),
                        "komponen": stats.get("komponen", 0),
                        "penyebab": stats.get("penyebab", 0),
                        "relasi": stats.get("relasi", 0),
                    },
                    "endpoints_count": 14,
                    "timestamp": int(time.time()),
                })
            except Exception as e:
                return json_response(self, 500, {
                    "status": "error",
                    "version": APP_VERSION,
                    "error": str(e),
                })
        if path == "/api/version":
            return json_response(self, 200, {
                "app": APP_VERSION,
                "kb": KB_VERSION,
                "engine": "karbuin.diagnose.Diagnoser",
                "server": "stdlib http.server (no external deps)",
            })
        if path == "/api/telemetry":
            days = int(query.get("days", ["7"])[0])
            return json_response(self, 200, telemetry.stats(days=days))
        if path == "/api/telemetry/csv":
            days = int(query.get("days", ["7"])[0])
            event_type = query.get("event", [None])[0]
            csv = telemetry.export_csv(days=days, event_type=event_type)
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", f'attachment; filename="karbuin-telemetry-{days}d.csv"')
            self.send_header("Content-Length", str(len(csv.encode("utf-8"))))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(csv.encode("utf-8"))
            return
        if path == "/api/telemetry/recent":
            limit = int(query.get("limit", ["50"])[0])
            event_type = query.get("event", [None])[0]
            return json_response(self, 200, telemetry.query_recent(limit=limit, event_type=event_type))

        # ── Static HTML pages ───────────────────────────────
        page_map = {
            "/": "index.html",
            "/diagnose": "diagnose.html",
            "/result": "result.html",
            "/library": "library.html",
            "/method": "method.html",
            "/dashboard": "dashboard.html",
            "/qa-harness": "qa-harness.html",
        }
        if path in page_map:
            return self.serve_file(UI_DIR / page_map[path], "text/html; charset=utf-8")
        if path == "/favicon.ico":
            # v1.2: serve the real favicon.ico from assets/
            ico = UI_DIR / "assets" / "favicon.ico"
            if ico.is_file():
                return self.serve_file(ico, "image/x-icon")
            return self.send_error(404)

        # ── Static assets ────────────────────────────────────
        if path.startswith("/assets/") or path.startswith("/css/") or path.startswith("/js/"):
            rel = path.lstrip("/")
            file_path = UI_DIR / rel
            if file_path.is_file() and file_path.is_relative_to(UI_DIR):
                mime = "text/css; charset=utf-8" if rel.endswith(".css") else \
                       "application/javascript; charset=utf-8" if rel.endswith(".js") else \
                       "image/svg+xml" if rel.endswith(".svg") else \
                       "image/png" if rel.endswith(".png") else \
                       "image/webp" if rel.endswith(".webp") else \
                       "text/html; charset=utf-8"
                return self.serve_file(file_path, mime)

        return self.send_error(404, f"Path not found: {path}")

    def do_POST(self):
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", 0))
        body_raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(body_raw.decode("utf-8"))
        except json.JSONDecodeError:
            return json_response(self, 400, {"error": "invalid_json"})

        if path == "/api/diagnose":
            try:
                result = DIAGNOSER.diagnose(
                    user_input=body.get("user_input", ""),
                    motor_id=body.get("motor_id"),
                    explicit_symptoms=body.get("explicit_symptoms"),
                )
            except Exception as e:
                telemetry.log_error(
                    endpoint="/api/diagnose",
                    error=str(e),
                    user_input=body.get("user_input", ""),
                    user_agent=self.headers.get("User-Agent", ""),
                    ip=self.client_address[0],
                )
                return json_response(self, 500, {"error": "internal_error", "message": str(e)})
            # Wrap with user-facing presentation (top_3, checklist, summary_card)
            try:
                result["presentation"] = build_presentation(
                    result,
                    motor_id=body.get("motor_id"),
                    cause_lookup=KB.get_penyebab if hasattr(KB, "get_penyebab") else None,
                )
            except Exception as e:
                # Presentation is additive — never break the diagnose response
                result["presentation_error"] = str(e)
            try:
                telemetry.log_diagnose(
                    user_input=body.get("user_input", ""),
                    motor_id=body.get("motor_id"),
                    explicit_symptoms=body.get("explicit_symptoms"),
                    result=result,
                    user_agent=self.headers.get("User-Agent", ""),
                    ip=self.client_address[0],
                )
            except Exception as e:
                print(f"[telemetry] diagnose log failed: {e}", flush=True)
            return json_response(self, 200, result)

        if path == "/api/diagnose/followup":
            try:
                result = DIAGNOSER.diagnose(
                    user_input=body.get("user_input", ""),
                    motor_id=body.get("motor_id"),
                    explicit_symptoms=body.get("explicit_symptoms"),
                    confirmed_causes=body.get("confirmed_causes"),
                    answer_adjustments=body.get("answer_adjustments"),
                )
            except Exception as e:
                telemetry.log_error(
                    endpoint="/api/diagnose/followup",
                    error=str(e),
                    user_input=body.get("user_input", ""),
                    user_agent=self.headers.get("User-Agent", ""),
                    ip=self.client_address[0],
                )
                return json_response(self, 500, {"error": "internal_error", "message": str(e)})
            try:
                telemetry.log_followup(
                    user_input=body.get("user_input", ""),
                    motor_id=body.get("motor_id"),
                    explicit_symptoms=body.get("explicit_symptoms"),
                    answers=body.get("answers", {}),
                    adjustments=body.get("answer_adjustments", {}),
                    result=result,
                    user_agent=self.headers.get("User-Agent", ""),
                    ip=self.client_address[0],
                )
            except Exception as e:
                print(f"[telemetry] followup log failed: {e}", flush=True)
            return json_response(self, 200, result)

        if path == "/api/telemetry":
            days = int(query.get("days", ["7"])[0])
            return json_response(self, 200, telemetry.stats(days=days))

        if path == "/api/parser/preview":
            """Preview detected symptoms from free text (for live UI)."""
            text = body.get("user_input", "")
            parsed = DIAGNOSER.parser.parse_with_details(text)
            return json_response(self, 200, {"parsed": parsed})

        return json_response(self, 404, {"error": "endpoint_not_found"})

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def serve_file(self, file_path: Path, mime: str):
        if not file_path.is_file():
            return self.send_error(404)
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"))
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), KarbuinHandler)
    print(f"🏍 Karbuin v{os.environ.get('KARBUIN_VERSION', '1.1.2')} running at http://{args.host}:{args.port}")
    print(f"   Data: {len(KB.motor)} motor | {len(KB.komponen)} komponen | {len(KB.gejala)} gejala | {len(KB.penyebab)} penyebab | {len(KB.relasi)} relasi")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
