# 📤 Push Karbuin ke GitHub

**Status**: Repo lokal siap di `/home/hebryn/projects/motorcycle-karbu-expert/` (6 commits, branch `main`, versi `v1.1.2`).

---

## Opsi 1 — Manual via Web (Paling mudah, no CLI needed)

### Step 1: Buat repo kosong di GitHub
1. Login ke https://github.com
2. Klik **+** (top-right) → **New repository**
3. Settings:
   - **Repository name**: `karbuin`
   - **Description**: `Karbuin — Motorcycle Carburetor Diagnostic Expert`
   - **Public** (supaya bisa di-share)
   - ❌ **JANGAN** centang "Initialize with README" (karena kita sudah punya)
   - ❌ **JANGAN** centang "Add .gitignore"
   - ❌ **JANGAN** centang "Choose a license"
4. Klik **Create repository**
5. **Copy URL remote** (HTTPS):
   ```
   https://github.com/USERNAME/karbuin.git
   ```

### Step 2: Push dari local
```bash
cd /home/hebryn/projects/motorcycle-karbu-expert
git remote add origin https://github.com/USERNAME/karbuin.git
git push -u origin main
```

### Step 3: Verify
- Buka `https://github.com/USERNAME/karbuin`
- Pastikan 6 commits muncul
- File tree terlihat

---

## Opsi 2 — Bundle + upload manual (jika tidak ada git di lokal user)

Bundle sudah disiapkan: `/tmp/karbuin-v1.1.2-bundle.tar.gz` (61 files).

Di mesin lokal user:
```bash
# Download bundle dari WSL
# (User copy file dari /tmp/karbuin-v1.1.2-bundle.tar.gz ke mesin lokal)

tar xzf karbuin-v1.1.2-bundle.tar.gz
cd karbuin-v1.1.2-bundle

# Buat repo kosong di GitHub web dulu, lalu:
git init
git add -A
git commit -m "Initial Karbuin v1.1.2 — Engine FROZEN

- 8 motor karbu, 32 penyebab, 96 solusi
- 88% effective accuracy (test pack 50)
- Mobile-validated: 360/390/412 viewports
- Telemetry + dashboard + CSV export
- README + CHANGELOG + validation plan"

git branch -M main
git remote add origin https://github.com/USERNAME/karbuin.git
git push -u origin main
```

---

## Opsi 3 — Otomatis via gh CLI (kalau user mau install)

```bash
# Install gh CLI (Mac)
brew install gh

# Login
gh auth login

# Create + push dari /home/hebryn/projects/motorcycle-karbu-expert
cd /home/hebryn/projects/motorcycle-karbu-expert
gh repo create karbuin --public --source=. --remote=origin --push
```

---

## Setelah Push: Aktifkan GitHub Pages (optional, untuk showcase)

1. Settings → Pages
2. Source: `main` branch, `/ (root)`
3. Save
4. URL: `https://USERNAME.github.io/karbuin/`

**CATATAN**: Karbuin butuh Python backend untuk API, jadi GitHub Pages TIDAK bisa menjalankan Karbuin. GitHub Pages hanya untuk static showcase (landing page saja).

Untuk runtime, gunakan **Render** atau **Railway** — lihat `docs/DEPLOYMENT.md`.

---

## Branch Protection (recommended setelah push)

Settings → Branches → Add rule:
- Branch name pattern: `main`
- ✅ Require pull request reviews before merging
- ✅ Require status checks to pass before merging
- ✅ Require linear history
- ✅ Do not allow force pushes

---

## Topics (untuk discoverability)

Settings → General → Topics:
- `motorcycle`
- `carburetor`
- `diagnostic`
- `indonesia`
- `expert-system`
- `karburator`
- `pwa` (optional, kalau mau add manifest)

---

## Done Checklist

- [ ] Repo created di GitHub
- [ ] Push 6 commits berhasil
- [ ] Branch `main` default
- [ ] README tampil di halaman utama repo
- [ ] Topics ditambahkan
- [ ] (Optional) Branch protection enabled
- [ ] (Optional) GitHub Pages enabled untuk showcase

**URL repo final**: `https://github.com/USERNAME/karbuin`