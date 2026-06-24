# 🚀 PUSH COMMAND — Karbuin v1.1.2 ke GitHub

**Status**: Repo LOKAL SIAP. Tinggal push.

**Engine FROZEN**: push ini TIDAK mengubah logika. Hanya upload ke remote.

---

## 📋 Apa yang akan terjadi saat user kirim URL

User akan kirim URL seperti:
```
https://github.com/USERNAME/karbuin.git
```

Saya akan jalankan (SATU BARIS):
```bash
git remote add origin <URL> && git push -u origin main
```

Output sukses:
```
Enumerating objects: 75, done.
Counting objects: 100% (75/75), done.
Delta compression using up to 8 threads
Compressing objects: 100% (65/65), done.
Writing objects: 100% (75/75), 124 KB | 6.2 MB/s, done.
Total 75 (delta 32), reused 0 (delta 0)
remote: Resolving deltas: 100% (32/32), done.
To https://github.com/USERNAME/karbuin.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

---

## ⚠️ Pre-conditions (sudah verified)

- [x] Working tree clean (`git status` = empty)
- [x] 12 commits on `main`
- [x] Branch `main` (default)
- [x] Bundle ready di `/tmp/karbuin-v1.1.2-bundle.tar.gz` (jika push gagal)
- [x] gh CLI installed di `~/bin/gh` v2.62.0 (alternative method)

---

## 📊 Apa yang akan ter-upload

```
12 commits (12 karena termasuk audit + bug fix + v1.1.0/1/2/3 deployment work)
~63 files, ~123 KB
Branch: main
```

### File yang ter-include (ringkasan)

**Source code**:
- `karbuin/` — engine package (diagnose, kb, telemetry)
- `server.py` — HTTP server (15,246 bytes)
- `data/seed/` — KB seed files (motor, komponen, gejala, penyebab, solusi, harga, dll)

**UI**:
- `ui/index.html` (landing)
- `ui/diagnose.html`, `ui/result.html`, `ui/library.html`, `ui/method.html`
- `ui/dashboard.html` (telemetry dashboard)
- `ui/qa-harness.html` (mobile QA tool)
- `ui/css/` (components, pages)
- `ui/js/` (parser, diagnose, result, share, library)

**Deployment**:
- `Procfile`, `runtime.txt`, `requirements.txt`
- `Dockerfile`, `render.yaml`, `.env.example`

**Docs**:
- `README.md`, `CHANGELOG.md`
- `docs/DEPLOYMENT.md`, `docs/RENDER_DEPLOYMENT.md`
- `docs/DEPLOYMENT_CHECKLIST.md`
- `docs/PUBLIC_URLS.md`, `docs/PUSH_TO_GITHUB.md`
- `docs/REAL_CASE_COLLECTION.md`, `docs/VALIDATION_DATASET_FORMAT.md`
- `docs/REAL_VALIDATION_100_PLAN.md`

**Scripts**:
- `scripts/validate_real_cases.py` — validator + engine scorer

**Other**:
- `tests/` (test pack)
- `data/real_cases.jsonl` (empty placeholder)

### File yang EXCLUDED (via .gitignore)

- `__pycache__/`, `*.pyc`
- `.env`
- `data/cache/`, `data/derived/`
- `data/telemetry/` (telemetry logs — TIDAK boleh di-push ke public repo, privacy)
- `.git/`

---

## 🔄 Fallback: Push via bundle (kalau git push gagal)

Jika push via `git push` gagal (misal karena auth issue), user bisa upload bundle manual:

```bash
# Di WSL saya:
/tmp/bundle-for-github.sh
# Output: /tmp/karbuin-v1.1.2-bundle.tar.gz (123 KB, 63 files)

# User copy ke Windows:
cp /tmp/karbuin-v1.1.2-bundle.tar.gz /mnt/c/Users/<USER>/Downloads/

# User extract + push via GitHub Desktop, atau:
# Upload manual via https://github.com/USERNAME/karbuin/upload/main
```

---

## 📝 Post-Push Verification

Setelah push sukses, verify di GitHub:

```bash
git log --oneline
# Harus muncul 12 commits, sama persis dengan lokal

git remote -v
# origin  https://github.com/USERNAME/karbuin.git (fetch)
# origin  https://github.com/USERNAME/karbuin.git (push)
```

Di GitHub.com:
1. Buka https://github.com/USERNAME/karbuin
2. Verify 12 commits visible di tab **"Commits"**
3. Verify file tree visible di tab **"<> Code"**
4. (Optional) Add topics: `motorcycle`, `carburetor`, `diagnostic`, `indonesia`, `expert-system`
5. (Optional) Add description: "Karbuin — Motorcycle Carburetor Diagnostic Expert System"

---

## ⏭️ Next Steps (setelah push sukses)

1. **Render deploy** — pakai repo `USERNAME/karbuin` (lihat `docs/RENDER_DEPLOYMENT.md`)
2. **Verify Render URL** — smoke test semua endpoint
3. **Share URL** — `https://karbuin.onrender.com` ke user
4. **Real-case collection start** — 20 kasus pertama
5. **Telemetry review** — audit existing events

**Status saat ini (2026-06-24)**:
- ⏳ Menunggu URL remote dari user
- 📦 Bundle siap sebagai fallback
- 🚀 Push script siap (1 baris)