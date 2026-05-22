# How to Run FreqFind (Windows)

FreqFind has three parts: a **JSON fingerprint database** (no separate DB server), a **FastAPI backend**, and a **static frontend**. Follow these steps each time you want to run it locally.

## Prerequisites

- **Python 3.10+** installed (`python --version`)
- Project folder: `c:\Users\USER\Desktop\freqfind`

## First-time setup (once)

Open **PowerShell** or **Command Prompt**:

```powershell
cd c:\Users\USER\Desktop\freqfind
pip install -r requirements.txt
$env:PYTHONIOENCODING='utf-8'
python generate_samples.py
python index_samples.py
```

On Windows, set `PYTHONIOENCODING=utf-8` if sample scripts print emoji and fail with `UnicodeEncodeError`.

`generate_samples.py` creates demo WAV files in `sample_songs\`.  
`index_samples.py` builds `fingerprints.json` next to `db.py`.

## Every time you want to run the app

You need **two terminals** (backend + frontend).

### Terminal 1 — Backend API (port 8000)

```powershell
cd c:\Users\USER\Desktop\freqfind
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Leave this running. API docs: http://127.0.0.1:8000/docs

### Terminal 2 — Frontend (port 3000)

```powershell
cd c:\Users\USER\Desktop\freqfind
python -m http.server 3000
```

Open in your browser: **http://localhost:3000/index.html**

> Use the HTTP server URL above. Opening `index.html` directly from File Explorer can break API calls in some browsers.

## Quick test

1. Go to the **Identify** tab.
2. Upload a file from `sample_songs\` (e.g. `ode_to_joy.wav`).
3. You should see match results, spectrogram, and FFT chart.

## Health checks

| What | URL |
|------|-----|
| Backend health | http://127.0.0.1:8000/health |
| Song list | http://127.0.0.1:8000/songs |
| Database stats | http://127.0.0.1:8000/stats |

## Stopping

Press **Ctrl+C** in each terminal.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` from the project folder |
| No matches / empty library | Run `python generate_samples.py` then `python index_samples.py` |
| Frontend can't reach API | Ensure Terminal 1 is running on port 8000; use http://localhost:3000/index.html not `file://` |
| Port already in use | Change port: `uvicorn main:app --port 8001` and edit `API` in `index.html` to match |

## Re-index after adding songs

Use the **Library** tab in the UI, or run `python index_samples.py` again after regenerating samples.
