# 🌐 Public URLs — Karbuin

Status deployment publik yang sedang aktif.

---

## URL Aktif (Cloudflare Quick Tunnel)

**URL**: `https://ratios-marking-yards-slip.trycloudflare.com`

| Field | Value |
|---|---|
| **Provider** | Cloudflare Quick Tunnel (trycloudflare.com) |
| **Tunnel type** | Accountless (no signup needed) |
| **Uptime guarantee** | ❌ None (subject to Cloudflare ToS, can be killed) |
| **Latency** | ~50-100ms first hit, <500ms subsequent (Singapore edge) |
| **HTTPS** | ✅ Auto (Cloudflare cert) |
| **Persistent?** | No — process restart = new URL |

### How to start tunnel (server already running on :8000)
```bash
~/bin/cloudflared tunnel --url http://localhost:8000 --no-autoupdate
# Output: https://XXXX.trycloudflare.com
```

### Caveats
- ⚠️ **No uptime SLA** — Cloudflare can kill the tunnel anytime
- ⚠️ **URL changes** setiap restart
- ⚠️ Untuk production: pakai **Named Tunnel** (perlu akun Cloudflare gratis)

---

## Untuk Permanent URL

### Quick path: Cloudflare Named Tunnel (free, permanent)

1. Sign up https://dash.cloudflare.com (free)
2. Install cloudflared: `brew install cloudflared` atau download
3. Login: `cloudflared tunnel login`
4. Create: `cloudflared tunnel create karbuin`
5. Route DNS: `cloudflared tunnel route dns karbuin karbuin.id` (kalau ada domain)
6. Config di `~/.cloudflared/config.yml`:
   ```yaml
   tunnel: <TUNNEL_ID>
   credentials-file: /path/to/<TUNNEL_ID>.json
   ingress:
     - hostname: karbuin.id
       service: http://localhost:8000
     - service: http_status:404
   ```
7. Run: `cloudflared tunnel run karbuin`
8. (Optional) Daemonize via systemd atau Docker

### Recommended: Render.com (managed, auto-deploy)

Lihat `docs/DEPLOYMENT.md` untuk setup lengkap.

Setelah setup: `https://karbuin.onrender.com` (permanent, ada sleep mode free tier)

### Alternative: Railway.app

Lihat `docs/DEPLOYMENT.md`. Setelah setup: `https://karbuin-production.up.railway.app`

---

## Testing Status

| Check | Result |
|---|---|
| `/` via curl | ✅ HTTP 200, 6662 bytes |
| `/diagnose` via curl | ✅ HTTP 200 |
| `/api/motors` via curl | ✅ HTTP 200 |
| `/api/diagnose` via curl | ✅ 200, status=ok, parsed 1 symptom |
| Browser `/` | ✅ Title + h1 + nav + CTA render |
| Browser `/diagnose` | ✅ 15 quick chips loaded, motor search works |
| Mobile responsive | ✅ CSS fix v1.1.1 + v1.1.2 applied |

---

## Telemetry dari Public URL

Setiap diagnose yang dilakukan via public URL akan tercatat di:
- Local: `data/telemetry/YYYY-MM-DD.jsonl`
- Public URL: data masih lokal di WSL (telemetry tidak persist ke Render kecuali ada disk)

---

## Decision Tree

```
Q: Butuh URL publik hari ini?
├─ YES → Pakai current trycloudflare URL (sudah live)
└─ NO (nanti) → Setup Render.com atau Named Tunnel

Q: Butuh uptime guarantee?
├─ YES → Render paid ($7/mo) atau Railway
└─ NO → Free Render (sleep mode) atau trycloudflare

Q: Punya domain sendiri?
├─ YES (karbuin.id) → Cloudflare Named Tunnel + domain
└─ NO → Pakai subdomain gratis dari Render/Railway
```

---

**Update terakhir**: 2026-06-24 21:16 UTC (Cloudflare quick tunnel established)