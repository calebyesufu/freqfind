# Deploy FreqFind (GitHub + Render + Vercel)

| Platform | Role | URL (after deploy) |
|----------|------|-------------------|
| **GitHub** | Source code | https://github.com/calebyesufu/freqfind |
| **Render** | FastAPI backend + fingerprint DB | https://freqfind-api.onrender.com |
| **Vercel** | Static frontend | https://freqfind.vercel.app (or your assigned URL) |

---

## 1. GitHub

```powershell
cd c:\Users\USER\Desktop\freqfind
gh auth login
git push -u origin main
```

If the repo does not exist yet:

```powershell
gh repo create freqfind --public --source . --remote origin --push
```

---

## 2. Render (backend)

1. Go to https://dashboard.render.com/select-repo?type=blueprint
2. Connect GitHub account and select **calebyesufu/freqfind**
3. Render reads `render.yaml` and creates **freqfind-api**
4. Wait for the first deploy (build + seed can take several minutes on free tier)

**Health check:** https://freqfind-api.onrender.com/health

**Note:** Free tier sleeps after inactivity; first request may take ~30s.

On the free plan the database is re-seeded from `sample_songs/` when empty after each cold start (ephemeral disk).

---

## 3. Vercel (frontend)

### Option A — Dashboard

1. https://vercel.com/new → Import **calebyesufu/freqfind**
2. Framework: **Other** (uses `vercel.json`)
3. Environment variable (after Render is live):

   | Name | Value |
   |------|--------|
   | `RENDER_API_URL` | `https://freqfind-api.onrender.com` |

4. Deploy

### Option B — CLI

```powershell
npm i -g vercel
cd c:\Users\USER\Desktop\freqfind
vercel login
$env:RENDER_API_URL="https://freqfind-api.onrender.com"
vercel --prod
```

The build runs `scripts/write-config.js` so `config.js` points at your Render API.

---

## 4. Wire frontend → backend

If Render uses a different hostname, set in **Vercel** → Project → Settings → Environment Variables:

```
RENDER_API_URL=https://YOUR-ACTUAL-RENDER-URL.onrender.com
```

Redeploy Vercel after changing it.

Local dev still uses `http://localhost:8000` automatically.

---

## 5. Verify

1. Open your Vercel URL → **Library** tab should list 5 demo songs (after Render seeded).
2. **Identify** → upload a file from `sample_songs/`.
3. API docs: `https://freqfind-api.onrender.com/docs`

---

## Troubleshooting

### "Not Found" or "detail not found" in the app

This means the **Render backend is not running** or the URL is wrong.

1. Open https://dashboard.render.com — you must see a service named **freqfind-api** (green / live).
2. If missing, deploy the blueprint: https://dashboard.render.com/blueprint/new?repo=https://github.com/calebyesufu/freqfind
3. Copy your real Render URL (e.g. `https://freqfind-api.onrender.com`) from the Render dashboard.
4. In **Vercel** → Project → Settings → Environment Variables, set:
   - `RENDER_API_URL` = your Render URL (no trailing slash)
5. **Redeploy** Vercel (Deployments → … → Redeploy).

Test the API directly in a browser: `https://freqfind-api.onrender.com/health` should show `{"status":"ok","service":"FreqFind"}`.

### Other issues

| Issue | Fix |
|-------|-----|
| Vercel shows app but API errors | Set `RENDER_API_URL`; redeploy Vercel |
| Render build fails on Python 3.13 | `render.yaml` pins Python 3.11 |
| Empty library on Render | Check Render logs for `Seeding demo songs` |
| First request very slow | Render free tier cold start (~30s) — wait and retry |
