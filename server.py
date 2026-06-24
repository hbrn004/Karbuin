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
  POST /api/diagnose              → run diagnosis (body: {motor_id, user_input, explicit_symptoms})
  POST /api/diagnose/followup     → re-run with follow-up (body: {motor_id, user_input, explicit_symptoms, confirmed_causes, answer_adjustments})

Usage: python3 server.py [--port 8000]
"""
from __future__ import annotations

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

KB = KnowledgeBase(DATA_DIR)
DIAGNOSER = Diagnoser(KB)


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

        # ── Static HTML pages ───────────────────────────────
        page_map = {
            "/": "index.html",
            "/diagnose": "diagnose.html",
            "/result": "result.html",
            "/library": "library.html",
            "/method": "method.html",
        }
        if path in page_map:
            return self.serve_file(UI_DIR / page_map[path], "text/html; charset=utf-8")
        if path == "/favicon.ico":
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
            result = DIAGNOSER.diagnose(
                user_input=body.get("user_input", ""),
                motor_id=body.get("motor_id"),
                explicit_symptoms=body.get("explicit_symptoms"),
            )
            return json_response(self, 200, result)

        if path == "/api/diagnose/followup":
            result = DIAGNOSER.diagnose(
                user_input=body.get("user_input", ""),
                motor_id=body.get("motor_id"),
                explicit_symptoms=body.get("explicit_symptoms"),
                confirmed_causes=body.get("confirmed_causes"),
                answer_adjustments=body.get("answer_adjustments"),
            )
            return json_response(self, 200, result)

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
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), KarbuinHandler)
    print(f"🏍 Karbuin v0.1.0 running at http://localhost:{args.port}")
    print(f"   Data: {len(KB.motor)} motor | {len(KB.komponen)} komponen | {len(KB.gejala)} gejala | {len(KB.penyebab)} penyebab | {len(KB.relasi)} relasi")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":
    main()
