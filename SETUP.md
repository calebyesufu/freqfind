# FreqFind — Step-by-step setup (fix “Not Found”)

Do these **in order**. Skip a step only if you already completed it.

---

## Step 1 — GitHub (source code)

**Goal:** Latest code is on GitHub.

1. Open: https://github.com/calebyesufu/freqfind  
2. You should see files like `main.py`, `index.html`, `render.yaml`.  
3. Latest commit should mention **direct Render API** (not `/api` proxy).

**On your PC (only if you change code later):**

```powershell
cd c:\Users\USER\Desktop\freqfind
git add -A
git commit -m "your message"
git push origin main
```

---

## Step 2 — Render (backend API) — REQUIRED

**Goal:** This URL must work in your browser before Vercel can work.

1. Open: https://dashboard.render.com  
2. Sign in with **GitHub**.  
3. If you **do not** see a service named **freqfind-api**:
   - Open: https://dashboard.render.com/blueprint/new?repo=https://github.com/calebyesufu/freqfind  
   - Click **Apply** / **Deploy Blueprint**.  
   - Wait until status is **Live** (5–15 minutes first time).  
4. Click **freqfind-api** → copy the URL at the top (e.g. `https://freqfind-api.onrender.com`).  
5. **Test in browser** (replace with your URL if different):

   ```
   https://freqfind-api.onrender.com/health
   ```

   **Must show:** `{"status":"ok","service":"FreqFind"}`  

   If you see 404 or an error page → Render is not ready; wait or check **Logs** on Render.

6. Also test:

   ```
   https://freqfind-api.onrender.com/songs
   ```

   **Must show:** JSON with a `"songs"` list (5 demo songs).

**Write down your Render URL:** `_________________________________`

---

## Step 3 — Vercel (frontend)

**Goal:** Website talks **directly** to Render (no `/api` proxy).

### 3a — Import project (first time only)

1. Open: https://vercel.com/new  
2. **Import** `calebyesufu/freqfind` from GitHub.  
3. Framework Preset: **Other** (leave as detected from `vercel.json`).  
4. **Do not** change Root Directory (leave `.`).  
5. Click **Deploy** once (may fail until env var is set — that’s OK).

### 3b — Environment variable (critical)

1. Vercel → your **freqfind** project → **Settings** → **Environment Variables**.  
2. Add:

   | Key | Value |
   |-----|--------|
   | `RENDER_API_URL` | Your Render URL from Step 2 (e.g. `https://freqfind-api.onrender.com`) |

   No trailing slash. Apply to **Production**, **Preview**, and **Development**.

3. Save.

### 3c — Redeploy (required after every env change or git push)

1. **Deployments** tab.  
2. Latest deployment → **⋯** menu → **Redeploy**.  
3. Wait until status is **Ready**.  
4. Copy your site URL (e.g. `https://freqfind-xxxxx.vercel.app`).

### 3d — Verify frontend

1. Open your Vercel URL in the browser.  
2. Press **F12** → **Console** — there should be no red CORS errors.  
3. Open **Library** tab — you should see **5 songs**.  
4. If you see a red **Backend** banner, Render URL or redeploy is wrong — repeat Step 2 and 3b–3c.

---

## Step 4 — Quick checklist

| Check | URL | Expected |
|-------|-----|----------|
| Render health | `https://freqfind-api.onrender.com/health` | `{"status":"ok",...}` |
| Render songs | `https://freqfind-api.onrender.com/songs` | `"songs": [...]` |
| Vercel app | `https://YOUR-APP.vercel.app` | UI loads, Library has 5 songs |
| Identify | Upload `sample_songs/ode_to_joy.wav` | Match result |

---

## Still “Not Found”?

| Symptom | Cause | Fix |
|---------|--------|-----|
| Render `/health` fails | Backend not deployed | Step 2 |
| Render works, Vercel fails | Old deploy or wrong `RENDER_API_URL` | Step 3b + **Redeploy** |
| Worked once, then empty library | Render free tier slept | Wait 30s, refresh; hit `/health` first |
| Error on **Identify** only | Cold start | Wait, try again |
| Vercel 404 for whole site | Wrong URL or project deleted | Vercel dashboard → copy URL from **Domains** |

---

## Run locally (optional)

**Terminal 1:**

```powershell
cd c:\Users\USER\Desktop\freqfind
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

**Terminal 2:**

```powershell
cd c:\Users\USER\Desktop\freqfind
python -m http.server 3000
```

Open: http://localhost:3000/index.html

---

## Your live links (fill in after setup)

- GitHub: https://github.com/calebyesufu/freqfind  
- Render API: https://freqfind-api.onrender.com  
- Vercel app: _________________________________
