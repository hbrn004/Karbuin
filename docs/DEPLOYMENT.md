# 🚀 Deployment Guide — Karbuin

Target: deploy Karbuin v1.1.2 ke platform cloud yang support Python stdlib `http.server`, SQLite, dan give permanent public URL.

**Engine FROZEN**: tidak ada perubahan kode. Hanya deployment artifacts (Procfile, runtime.txt, gunicorn, Dockerfile).

---

## ⚙️ Persiapan Kode (SUDAH dilakukan di v1.1.2)

Untuk deploy ke platform cloud, butuh beberapa file tambahan:

| File | Fungsi |
|---|---|
| `Procfile` | Declare command: `web: gunicorn server:app` |
| `runtime.txt` | Python version (3.11.x) |
| `requirements.txt` | Dependencies (gunicorn only) |
| `gunicorn_conf.py` | Bind 0.0.0.0:$PORT, workers, timeout |
| `app.py` | Wrapper: from server import app |
| `.env.example` | Template environment variables |
| `Dockerfile` | Optional: alternative deployment via Docker |

File-file ini SUDAH ada di repo (v1.1.2). Lihat `tree -L 1`.

---

## 🌐 Opsi A: Render.com (RECOMMENDED — gratis tier cukup)

### Kelebihan
- ✅ **Free tier**: 750 jam/bulan (cukup untuk 1 app 24/7)
- ✅ **Auto-deploy dari GitHub**: setiap push ke main = auto-deploy
- ✅ **HTTPS otomatis** (Let's Encrypt)
- ✅ **Persistent disk**: data/telemetry/ dan data/cache/ survive restart
- ✅ **Custom domain** support
- ⚠️ **Sleep setelah 15 menit idle** (free tier) — first request cold start ~30 detik

### Kekurangan
- ⚠️ Sleep mode: kalau jarang diakses, next visit lambat 30 detik
- ⚠️ Free tier CPU shared, mungkin lambat saat peak
- ⚠️ Cold start: 30-50 detik untuk first request setelah sleep

### Setup Steps

#### 1. Buat akun Render
- Buka https://render.com
- Sign up via GitHub (recommended) atau email

#### 2. Connect GitHub repo
- Dashboard → **New** → **Web Service**
- Pilih repo `USERNAME/karbuin` (harus sudah dipush ke GitHub)
- Klik **Connect**

#### 3. Konfigurasi Web Service

| Field | Value |
|---|---|
| **Name** | `karbuin` |
| **Region** | Singapore (dekat Indonesia, latency rendah) |
| **Branch** | `main` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn server:app` |
| **Plan** | `Free` |

#### 4. Environment Variables (optional, tapi direkomendasikan)

| Key | Value |
|---|---|
| `PYTHON_VERSION` | `3.11.9` |
| `KARBUIN_ENV` | `production` |
| `PORT` | (auto-set oleh Render) |

#### 5. Persistent Disk (PENTING — supaya telemetry tidak hilang)

- **Advanced** → **Add Disk**
  - **Name**: `karbuin-data`
  - **Mount Path**: `/opt/render/project/src/data`
  - **Size**: `1 GB` (free tier cukup)

#### 6. Klik **Create Web Service**
- Render akan build + deploy otomatis
- Tunggu 5-10 menit untuk first deploy
- URL: `https://karbuin.onrender.com`

#### 7. Verify
```bash
curl -s https://karbuin.onrender.com/api/motors | jq '.[0:3]'
```

#### 8. (Optional) Custom Domain
- Settings → Custom Domain → Add `karbuin.id`
- Ikuti instruksi DNS

---

## 🚂 Opsi B: Railway.app

### Kelebihan
- ✅ **$5 credit gratis** saat sign up (cukup untuk ~1 bulan 24/7)
- ✅ **No sleep mode** (selama masih ada credit)
- ✅ **Faster cold start** (~5 detik vs 30 detik Render)
- ✅ **Simple pricing**: pay-as-you-use

### Kekurangan
- ⚠️ Butuh kartu kredit untuk sign up (tapi $5 gratis first month)
- ⚠️ Setelah $5 habis, app mati — harus top-up
- ⚠️ Persistent disk lebih mahal

### Setup Steps

#### 1. Buat akun Railway
- Buka https://railway.app
- Sign up via GitHub

#### 2. New Project
- Dashboard → **New Project** → **Deploy from GitHub repo**
- Pilih `USERNAME/karbuin`

#### 3. Add Variables
| Variable | Value |
|---|---|
| `PORT` | `8000` (auto-detected) |

#### 4. Configure
- Settings → **Start Command**: `gunicorn server:app`
- Settings → **Healthcheck Path**: `/api/health`

#### 5. Generate Domain
- Settings → **Networking** → **Generate Domain**
- URL: `karbuin-production.up.railway.app`

#### 6. Add Volume (persistent data)
- New → **Volume** → Mount ke `/app/data`
- Size: 1 GB ($0.25/GB/month)

---

## 🐳 Opsi C: Docker + VPS (advanced)

Untuk user yang punya VPS sendiri (DigitalOcean, Linode, Vultr).

### Step 1: Build image
```bash
cd /path/to/karbuin
docker build -t karbuin:v1.1.2 .
```

### Step 2: Run container
```bash
docker run -d \
  --name karbuin \
  -p 8000:8000 \
  -v /var/karbuin/data:/app/data \
  --restart unless-stopped \
  karbuin:v1.1.2
```

### Step 3: Reverse proxy (Nginx)
```nginx
server {
  listen 80;
  server_name karbuin.id;
  location / {
    proxy_pass http://localhost:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
  }
}
```

### Step 4: HTTPS (Certbot)
```bash
sudo certbot --nginx -d karbuin.id
```

---

## 📊 Perbandingan

| Aspek | Render Free | Railway $5 | VPS + Docker |
|---|---|---|---|
| **Biaya/bulan** | $0 | ~$5 | $5-12 (VPS) |
| **Sleep?** | Ya (15 min) | Tidak | Tidak |
| **Cold start** | 30-50s | 5s | 0s |
| **Persistent disk** | Ya (1GB free) | Ya (volume) | Ya (native) |
| **HTTPS** | Auto | Auto | Manual (Certbot) |
| **Custom domain** | Ya | Ya | Ya |
| **Auto-deploy** | Ya (GitHub) | Ya (GitHub) | Manual |
| **Recommended for** | Demo, MVP, low-traffic | Production, MVP+ | Custom infra, full control |

**Rekomendasi**: **Render Free** untuk MVP (cukup untuk 100 kasus/hari tanpa masalah). Switch ke Railway saat traffic naik atau butuh always-on.

---

## ✅ Post-Deploy Verification Checklist

Setelah deploy sukses, jalankan test ini:

```bash
# 1. Health check
curl -s https://karbuin.YOURDOMAIN.com/api/motors | head -100

# 2. Verify all endpoints
curl -s -o /dev/null -w "/diagnose: %{http_code}\n" https://karbuin.YOURDOMAIN.com/diagnose
curl -s -o /dev/null -w "/result: %{http_code}\n" https://karbuin.YOURDOMAIN.com/result
curl -s -o /dev/null -w "/library: %{http_code}\n" https://karbuin.YOURDOMAIN.com/library
curl -s -o /dev/null -w "/method: %{http_code}\n" https://karbuin.YOURDOMAIN.com/method

# 3. Test diagnose API
curl -s -X POST https://karbuin.YOURDOMAIN.com/api/diagnose \
  -H "Content-Type: application/json" \
  -d '{"motor_id":"yamaha_mio_sporty","input":"brebet di tanjakan"}' \
  | python3 -m json.tool | head -20

# 4. Test from mobile (penting!)
# Buka https://karbuin.YOURDOMAIN.com/diagnose dari HP
# - Tombol Diagnosa harus terlihat
# - Tidak boleh ada horizontal scroll
# - Quick chips harus muncul
```

---

## 🚨 Troubleshooting

### "Application failed to start"
- Cek Render logs: Dashboard → Logs
- Pastikan `requirements.txt` ada
- Pastikan `Procfile` ada
- Pastikan Python version benar (`runtime.txt`)

### "Telemetry data hilang setelah restart"
- Persistent disk belum di-mount
- Render: Settings → Disks → Add disk
- Railway: New → Volume
- Docker: `-v` flag

### "Cold start lambat"
- Free tier limitation
- Upgrade ke paid plan ($7/mo Render, $5+ Railway)
- Atau gunakan cron-job.org untuk ping setiap 10 menit (keep-alive)

### "HTTPS error"
- Render/Railway: HTTPS otomatis
- VPS: install certbot

---

## 📞 Support

- GitHub Issues: https://github.com/USERNAME/karbuin/issues
- Email: karbuin@karbuin.id
- Docs: https://karbuin.id/docs

---

**Next**: Setelah deploy sukses, lanjut ke Telemetry Dashboard + CSV Export.