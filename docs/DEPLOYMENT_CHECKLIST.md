# ✅ Deployment Checklist — Karbuin v1.1.2

**Target**: Production-ready public URL dengan semua observability features.

---

## Pre-Deploy

### 1. Repository Preparation
- [x] Local repo clean (`git status` no uncommitted changes)
- [x] All commits have descriptive messages
- [x] 8 commits in `main` branch (Initial → v1.0.0 → v1.1.0 → v1.1.1 → v1.1.2 → v1.1.3)
- [x] `.gitignore` excludes: `__pycache__/`, `*.pyc`, `.env`, `data/cache/`, `data/derived/`, `data/telemetry/`
- [x] `README.md` present (4,764 bytes)
- [x] `CHANGELOG.md` present (2,553 bytes)
- [x] All deployment artifacts present:
  - `Procfile`
  - `runtime.txt`
  - `requirements.txt`
  - `Dockerfile`
  - `render.yaml`
  - `.env.example`

### 2. Local Testing
- [x] `python3 server.py --port 8000` runs without errors
- [x] Health check: `GET /api/motors` returns 200
- [x] Diagnose API: `POST /api/diagnose` returns valid result
- [x] Telemetry endpoints:
  - `GET /api/telemetry?days=7` returns JSON stats
  - `GET /api/telemetry/csv?days=7` returns CSV with Content-Disposition
  - `GET /api/telemetry/recent?limit=20` returns JSON list
- [x] Dashboard: `GET /dashboard` renders (dark theme)
- [x] Mobile QA: 3 viewports (360/390/412) all PASS
- [x] Mobile CSS fixes: v1.1.1 (Diagnosa button) + v1.1.2 (result overflow)

### 3. Knowledge Base Validation
- [x] 8 motor karbu seeded
- [x] 30 komponen seeded
- [x] 25 gejala seeded
- [x] 32 penyebab seeded
- [x] 124 relasi seeded
- [x] 96 solusi loaded (Phase 1.7A.1)
- [x] 24 harga loaded (Phase 1.7A.2)
- [x] All test pack 50 cases pass
- [x] Hardening 40/50 PASS

---

## Push to GitHub

### 4. GitHub Repository Setup
- [ ] **DECISION**: Choose push method:
  - [ ] Option A: Manual via web UI (no gh CLI)
  - [ ] Option B: `gh auth login` + push (needs PAT)
  - [ ] Option C: Bundle upload (`/tmp/karbuin-v1.1.2-bundle.tar.gz`)

- [ ] Create empty repo at https://github.com/new
  - Name: `karbuin`
  - Description: `Motorcycle Carburetor Diagnostic Expert — Karbuin v1.1.2`
  - Public
  - ❌ NO README (we have one)
  - ❌ NO .gitignore
  - ❌ NO license

- [ ] Push to GitHub:
  ```bash
  cd /home/hebryn/projects/motorcycle-karbu-expert
  git remote add origin https://github.com/USERNAME/karbuin.git
  git push -u origin main
  ```

- [ ] Verify: 8 commits visible di https://github.com/USERNAME/karbuin

- [ ] Add topics: `motorcycle`, `carburetor`, `diagnostic`, `indonesia`, `expert-system`

- [ ] (Optional) Enable branch protection on `main`

### 5. Bundle Backup
- [x] `/tmp/karbuin-v1.1.2-bundle.tar.gz` created (61 files)
- [x] `docs/PUSH_TO_GITHUB.md` has 3 opsi push
- [x] `/tmp/bundle-for-github.sh` re-runnable for future versions

---

## Deploy to Cloud

### 6A. Render.com (RECOMMENDED for MVP)

- [ ] Sign up https://render.com (free, no card needed)
- [ ] New → Web Service → Connect `USERNAME/karbuin` repo
- [ ] Configure:
  - [ ] Name: `karbuin`
  - [ ] Region: `Singapore` (low latency ke Indonesia)
  - [ ] Branch: `main`
  - [ ] Runtime: `Python 3`
  - [ ] Build Command: `pip install -r requirements.txt` (or empty since no deps)
  - [ ] Start Command: `python3 server.py --host 0.0.0.0 --port $PORT`
  - [ ] Plan: `Free`
- [ ] Environment Variables:
  - [ ] `PYTHON_VERSION=3.11.9`
  - [ ] `KARBUIN_VERSION=1.1.2`
  - [ ] `KARBUIN_ENV=production`
- [ ] Add Disk:
  - [ ] Name: `karbuin-data`
  - [ ] Mount Path: `/opt/render/project/src/data`
  - [ ] Size: `1 GB`
- [ ] Health Check Path: `/api/motors`
- [ ] Click "Create Web Service"
- [ ] Wait 5-10 min for first deploy
- [ ] Verify URL: `https://karbuin.onrender.com`
  - [ ] `curl https://karbuin.onrender.com/api/motors` → 200
  - [ ] Browser: landing renders
  - [ ] `/dashboard` renders
  - [ ] Mobile diagnose flow works
- [ ] (Optional) Custom domain: Settings → Custom Domain → `karbuin.id`

### 6B. Railway.app (Alternative)

- [ ] Sign up https://railway.app ($5 credit, need card)
- [ ] New Project → Deploy from GitHub → `USERNAME/karbuin`
- [ ] Add Volume: `/app/data`, 1 GB
- [ ] Settings:
  - [ ] Start Command: `python3 server.py --host 0.0.0.0 --port $PORT`
  - [ ] Healthcheck: `/api/motors`
- [ ] Generate Domain: `karbuin-production.up.railway.app`
- [ ] Verify URL works

### 6C. Cloudflare Named Tunnel (Permanent free, custom domain)

- [ ] Sign up https://dash.cloudflare.com (free)
- [ ] Install cloudflared on server (VPS): `brew install cloudflared` atau download
- [ ] Login: `cloudflared tunnel login`
- [ ] Create: `cloudflared tunnel create karbuin`
- [ ] Route DNS: `cloudflared tunnel route dns karbuin karbuin.id` (kalau punya domain)
- [ ] Config `~/.cloudflared/config.yml`:
  ```yaml
  tunnel: <TUNNEL_ID>
  credentials-file: /path/to/<TUNNEL_ID>.json
  ingress:
    - hostname: karbuin.id
      service: http://localhost:8000
    - service: http_status:404
  ```
- [ ] Run: `cloudflared tunnel run karbuin`
- [ ] Verify: `https://karbuin.id`

---

## Post-Deploy Verification

### 7. Smoke Test dari External IP
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/diagnose` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/api/motors` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/api/telemetry?days=7` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/api/telemetry/csv?days=7` → 200
- [ ] `curl -s -o /dev/null -w "%{http_code}\n" https://YOUR-DOMAIN/dashboard` → 200
- [ ] Browser: `https://YOUR-DOMAIN/` renders correctly

### 8. End-to-End Flow dari Mobile
- [ ] Open `https://YOUR-DOMAIN/` from Android
- [ ] Click "Mulai Diagnosa"
- [ ] Select motor (search "mio")
- [ ] Type symptoms: "brebet di tanjakan, bensin boros"
- [ ] Verify 2+ detected chips appear
- [ ] Click "🔍 Diagnosa" button — MUST BE VISIBLE (not hidden)
- [ ] Verify redirect to /result with cause
- [ ] Click "Share WhatsApp" — opens wa.me
- [ ] Test from iPhone too (jika ada)
- [ ] No horizontal scroll at 360/390/412

### 9. Performance Check
- [ ] First page load < 3 seconds
- [ ] API response < 200ms
- [ ] No console errors in browser DevTools
- [ ] No 404s on assets (CSS/JS/images)

---

## Telemetry Setup

### 10. Verify Telemetry Persistence
- [ ] Diagnose API call → check `data/telemetry/YYYY-MM-DD.jsonl` has new entry
- [ ] `/dashboard` shows updated counts
- [ ] `/api/telemetry/csv?days=7` download works
- [ ] (Production) Disk volume mounted correctly (persistent across deploys)

### 11. Privacy Verification
- [ ] Check telemetry JSONL: NO PII (no name, no IP raw, no email)
- [ ] IP is SHA256 first 16 chars
- [ ] User input stored verbatim (allowed, it's diagnostic content)
- [ ] No cookies set
- [ ] No session storage

---

## Monitoring

### 12. Health Monitoring (Optional)
- [ ] Setup uptime monitor (UptimeRobot free): ping `/api/motors` every 5 min
- [ ] Email alerts on downtime
- [ ] Slack/Discord webhook on errors
- [ ] (Render) Built-in monitoring di dashboard

### 13. Log Monitoring
- [ ] Check server logs daily for errors
- [ ] Set log retention to 30 days
- [ ] (Render) View logs di Dashboard → Logs

---

## Real-World Validation

### 14. Real Case Collection (v1.1.4+)
- [ ] Create `data/real_cases.jsonl` with first 5-10 cases
- [ ] Run `python3 scripts/validate_real_cases.py --score`
- [ ] Document Top-1 accuracy, Top-3 accuracy, calibration gap
- [ ] Iterate until ≥ 80% Top-1 accuracy on real cases

### 15. Share with Users
- [ ] Add sharing link to README
- [ ] (Optional) Post ke forum motor Indonesia
- [ ] (Optional) Add Google Analytics (privacy-friendly alternative: Plausible)
- [ ] Collect user feedback → masukkan `data/real_cases.jsonl`

---

## Rollback Plan

### 16. If Something Breaks
- [ ] (Render) Dashboard → Manual Deploy → pilih commit sebelumnya
- [ ] (Railway) Deployments → klik previous deployment → "Redeploy"
- [ ] (Cloudflare Tunnel) Edit config → `tunnel: <OLD_TUNNEL_ID>`
- [ ] Local fallback: `python3 server.py --port 8000` di WSL + localtunnel

### 17. If DB Corrupted
- [ ] SQLite di `data/derived/` — backup sebelum deploy
- [ ] If corrupted: `rm data/derived/*.db` — akan rebuild otomatis
- [ ] Telemetry: `rm data/telemetry/*.jsonl` — start fresh (data historis hilang)

---

## Done!

- [ ] All checkboxes filled
- [ ] Public URL accessible dari mobile
- [ ] Telemetry recording
- [ ] Dashboard live
- [ ] Real case collection started

**Next milestone**: First 50 real cases → Top-1 accuracy ≥ 80% → release v1.2.0

---

## Reference Links

- Render setup: https://render.com/docs/deploy-flask
- Railway setup: https://docs.railway.app/deploy/deployments
- Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks
- gh CLI auth: https://cli.github.com/manual/gh_auth_login
- Karbuin docs: `docs/DEPLOYMENT.md`, `docs/PUBLIC_URLS.md`, `docs/PUSH_TO_GITHUB.md`

---

**Last updated**: 2026-06-24 (v1.1.2 ready to deploy)