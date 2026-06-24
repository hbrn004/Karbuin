# 🚀 Render.com Free Tier — Karbuin v1.1.2

**Goal**: Deploy Karbuin ke Render.com Free Tier dengan **0 dollar / bulan** dan disk persistent untuk telemetry.

**Engine FROZEN**: deployment ini TIDAK mengubah logika diagnosis. Hanya konfigurasi Render.

---

## ⚠️ Free Tier Caveats (PENTING — baca dulu)

| Caveat | Impact | Mitigation |
|---|---|---|
| **Spin down after 15 min idle** | First request setelah idle = 30-60 detik | Acceptable untuk MVP, akan improve dengan cron keep-alive (lihat bawah) |
| **750 jam/bulan** | Cukup untuk 1 service 24/7 | OK untuk 1 bulan penuh |
| **No custom domain di free tier** | Dapat `https://karbuin.onrender.com` | OK untuk MVP. Custom domain = Starter plan $7/mo |
| **Disk max 1 GB** | Cukup untuk telemetry 1-2 tahun | Acceptable |
| **RAM 512 MB** | Cukup untuk stdlib HTTP server | OK, tidak pakai gunicorn |
| **CPU shared** | OK untuk traffic rendah | OK untuk MVP validation |
| **Free Postgres hanya 90 hari** | Tidak dipakai Karbuin | — |

**Bottom line**: Free tier **cukup** untuk MVP validation. Upgrade ke Starter ($7/mo) kalau perlu custom domain + always-on.

---

## 📋 Step-by-Step Setup

### Step 1: Akun Render

1. Buka https://render.com/register
2. Sign up via GitHub (recommended — auto-link ke repo)
3. Pilih plan: **Individual** (free)
4. Verify email

### Step 2: Push Karbuin ke GitHub (PREREQUISITE)

PUSH HARUS DULU. Lihat `docs/PUSH_TO_GITHUB.md` atau gunakan bundle di `/tmp/karbuin-v1.1.2-bundle.tar.gz`.

Verify: https://github.com/USERNAME/karbuin visible dengan 12 commits.

### Step 3: Create Web Service

1. Login ke https://dashboard.render.com
2. Klik **"New +"** → **"Web Service"**
3. Pilih **"Build and deploy from a Git repository"** → klik **"Next"**
4. Klik **"Connect account"** di GitHub (jika belum) → authorize Render
5. Pilih repo **USERNAME/karbuin** → klik **"Connect"**

### Step 4: Configure Web Service

| Field | Value | Notes |
|---|---|---|
| **Name** | `karbuin` | subdomain: `karbuin.onrender.com` |
| **Region** | `Singapore` | Lowest latency ke Indonesia (~30ms) |
| **Branch** | `main` | |
| **Root Directory** | (kosong) | Repo root |
| **Runtime** | `Python 3` | |
| **Build Command** | `pip install --upgrade pip` | Kosongkan kalau tidak ada deps (current state) |
| **Start Command** | `python3 server.py --host 0.0.0.0 --port $PORT` | **WAJIB pakai $PORT** |
| **Plan** | `Free` | $0/mo |

### Step 5: Environment Variables

Klik **"Advanced"** → **"Add Environment Variable"**:

| Key | Value | Purpose |
|---|---|---|
| `PYTHON_VERSION` | `3.11.9` | Pin Python version (sesuai runtime.txt) |
| `KARBUIN_VERSION` | `1.1.2` | Display version di header |
| `KARBUIN_ENV` | `production` | Mode flag |
| `PORT` | `8000` | (auto-set oleh Render) |

### Step 6: Add Disk (PENTING untuk telemetry persistence)

⚠️ **TANPA disk, telemetry akan HILANG setiap deploy!**

1. Scroll ke bawah → **"Disks"** section
2. Klik **"Add Disk"**
3. Isi:

| Field | Value |
|---|---|
| **Name** | `karbuin-data` |
| **Mount Path** | `/opt/render/project/src/data` |
| **Size** | `1 GB` (max untuk free tier) |

⚠️ **Mount path HARUS benar**. Kalau salah, Karbuin akan tulis ke ephemeral storage dan hilang.

### Step 7: Health Check

| Field | Value |
|---|---|
| **Health Check Path** | `/api/motors` |

Render akan ping endpoint ini setiap 30 detik. Kalau 3x gagal = unhealthy.

### Step 8: Auto-Deploy

| Field | Value |
|---|---|
| **Auto-Deploy** | `Yes` (default) |

Setiap push ke `main` → auto-rebuild + redeploy.

### Step 9: Create

1. Klik **"Create Web Service"**
2. Render akan mulai clone + build + deploy
3. Tunggu 5-10 menit untuk first deploy
4. Logs bisa dilihat di **"Logs"** tab

### Step 10: Verify

```bash
# Replace YOUR-SUBDOMAIN dengan subdomain Render kamu
URL="https://karbuin.onrender.com"

# Basic
curl -s -o /dev/null -w "/: %{http_code}\n" "$URL/"
curl -s -o /dev/null -w "/diagnose: %{http_code}\n" "$URL/diagnose"
curl -s -o /dev/null -w "/api/motors: %{http_code}\n" "$URL/api/motors"

# Diagnose flow
curl -s -X POST "$URL/api/diagnose" \
  -H "Content-Type: application/json" \
  -d '{"motor_id":"yamaha_mio_sporty","user_input":"brebet di tanjakan"}' \
  | python3 -m json.tool | head -10

# Telemetry
curl -s "$URL/api/telemetry?days=7" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print('Diagnose:', d['totals']['diagnose'])
print('Avg conf:', d['avg_top_confidence'])
"

# CSV export
curl -s -o /dev/null -w "CSV: %{http_code} | %{content_type} | %{size_download} bytes\n" \
  "$URL/api/telemetry/csv?days=7"
```

Expected output:
```
/: 200
/diagnose: 200
/api/motors: 200
{ ... diagnosis result ... }
Diagnose: 0
Avg conf: 0.0
CSV: 200 | text/csv | 80 bytes
```

(Catatan: `Diagnose: 0` karena telemetry masih kosong di Render. Setelah ada traffic, count naik.)

---

## 🔧 Custom Configuration (Optional)

### Custom Domain (perlu Starter $7/mo)

Skip di free tier. Pakai `karbuin.onrender.com` dulu.

### Keep-Alive Cron (anti spin-down)

Render free tier spin down setelah 15 menit tanpa traffic. Untuk MVP validation ini OK, tapi kalau mau always-on:

1. Setup cron job (cron-job.org free) hit `https://karbuin.onrender.com/api/motors` every 14 minutes
2. Atau upgrade ke Starter $7/mo (always-on)

### Environment-specific Config

`.env.example` sudah ada di repo. Copy ke `.env` lokal untuk development. Production tetap pakai environment variables di Render dashboard.

---

## 📊 Monitoring

### Built-in (Render Dashboard)
- Logs: tab **"Logs"** (real-time stdout/stderr)
- Metrics: tab **"Metrics"** (CPU, RAM, request count, response time)
- Events: tab **"Events"** (deploys, restarts, errors)

### External (optional)
- UptimeRobot: ping `/api/motors` every 5 min, email alert on downtime
- Better Stack (free tier): 5 monitors

---

## 🔄 Update Workflow

### Push code update
```bash
cd /home/hebryn/projects/motorcycle-karbu-expert
# ... make changes ...
git add -A
git commit -m "v1.1.4: ..."
git push origin main
# Render auto-detects, rebuilds, redeploys (3-5 min)
```

### Rollback
1. Dashboard → Service → tab **"Events"**
2. Cari deploy yang mau di-rollback
3. Klik **"Rollback to this deploy"**

### Manual deploy (jika auto-deploy off)
1. Dashboard → Service → tab **"Manual Deploy"**
2. Pilih commit → **"Deploy"**

---

## 🐛 Troubleshooting

### Service won't start
- Check **Logs** tab untuk error
- Common: missing dependency → tambahkan ke `requirements.txt`
- Common: wrong Start Command → pastikan `--port $PORT`

### Telemetry hilang setelah deploy
- Disk belum di-setup → tambahkan disk (Step 6)
- Mount path salah → harus `/opt/render/project/src/data`
- Service restart otomatis clear ephemeral storage

### 502 Bad Gateway
- App crash → check logs
- Cold start (free tier) → tunggu 30-60 detik, refresh
- Port mismatch → Start Command HARUS pakai `$PORT`

### Disk full
- Free tier max 1 GB
- Cleanup old telemetry: `rm data/telemetry/2026-06-*.jsonl` (manual via Shell tab)

### Build timeout
- Free tier build timeout: 15 menit
- Karbuin tidak punya deps → build cepat (< 30 detik)
- Kalau timeout: cek Build Command, simplify

---

## 💰 Cost Analysis

| Tier | Cost/mo | Karbuin Use Case |
|---|---|---|
| **Free** | $0 | MVP validation, low traffic, spin down OK |
| **Starter** | $7 | Always-on, custom domain, lebih stabil |
| **Standard** | $25 | Production traffic, multiple instances |

**Rekomendasi MVP**: Free tier cukup. Upgrade ke Starter kalau:
- Custom domain mau pakai
- Traffic > 100 req/day
- Spin-down delay tidak acceptable

---

## ✅ Final Checklist

- [ ] Repo pushed ke GitHub
- [ ] Render akun created
- [ ] Web Service created dengan config benar
- [ ] Environment variables set
- [ ] Disk mounted di `/opt/render/project/src/data`
- [ ] Health check `/api/motors`
- [ ] First deploy SUCCESS (logs shows "Server started on port XXXX")
- [ ] Smoke test semua endpoint (10/10 = 200)
- [ ] Mobile diagnose flow test dari HP
- [ ] Telemetry recording verified

---

## 🔗 Reference

- Render Web Service docs: https://render.com/docs/web-services
- Render Disk docs: https://render.com/docs/disks
- Render Environment: https://render.com/docs/environment-variables
- Free tier limits: https://render.com/docs/free

---

**Status saat ini (2026-06-24)**:
- Repo: 12 commits, ready to push
- Bundle: `/tmp/karbuin-v1.1.2-bundle.tar.gz` (63 files, 123 KB)
- Public URL (temporary, trycloudflare): https://ratios-marking-yards-slip.trycloudflare.com

Setelah push + Render deploy sukses, public URL akan jadi `https://karbuin.onrender.com` (permanent).