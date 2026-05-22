# FreqFind 🎵

> A Shazam-inspired music identification system built from scratch using **FFT, spectrogram analysis, and audio fingerprinting** — a practical demonstration of Fourier Transform applications in digital signal processing.

![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?logo=fastapi&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-1.26-013243?logo=numpy&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-7c3aed)

---

## What is This?

FreqFind identifies music from short audio clips using the same mathematical principles as Shazam — no external APIs, no black boxes. Every step of the signal processing pipeline is implemented from scratch and documented with the underlying math.

**Core concepts demonstrated:**
- Discrete Fourier Transform (DFT) and Fast Fourier Transform (FFT)
- Short-Time Fourier Transform (STFT) for spectrogram generation
- Constellation map peak extraction
- Combinatorial audio fingerprint hashing (Wang 2003 algorithm)
- Time-offset alignment matching

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        FRONTEND                              │
│  index.html — Drag & drop UI, waveform, spectrogram viewer  │
└───────────────────────────┬──────────────────────────────────┘
                            │ HTTP / FormData
┌───────────────────────────▼──────────────────────────────────┐
│                    FASTAPI BACKEND                           │
│  main.py — /identify  /songs/add  /songs  /stats            │
└───────────────────────────┬──────────────────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         ▼                  ▼                  ▼
  audio/fingerprint.py  database/db.py    matplotlib
  ─────────────────────  ────────────     ───────────
  load_audio()           add_song()       Spectrogram PNG
  compute_spectrogram()  match_song()     FFT snapshot PNG
  find_peaks()           list_songs()
  generate_hashes()      get_db_stats()
         │
         ▼
  fingerprints.json  ← JSON hash store
```

---

## FFT Pipeline (in plain English)

```
Raw Audio → Windowed Frames → FFT each frame → Spectrogram
    ↓
Find Local Peak Frequencies (Constellation Map)
    ↓
Hash Pairs of Peaks: hash(f1, f2, Δt)
    ↓
Store in Database

--- Identification ---

Query Clip → Same pipeline → Query Hashes
    ↓
Look up each hash in database → collect (song, time_offset) pairs
    ↓
Histogram over (song, Δt) → correct song peaks sharply
    ↓
Return best match + confidence score
```

### The Key Math

**DFT** (what FFT computes):
```
X[k] = Σ_{n=0}^{N-1} x[n] · e^{-j2πkn/N}
```

**STFT** (DFT applied to overlapping windows):
```
STFT(x)[m, k] = Σ_n x[n] · w[n - m·H] · e^{-j2πkn/N}
```

**Why FFT beats DFT:**
- DFT: O(N²) — 4096² = 16.7 million operations per window
- FFT: O(N log N) — 4096 × 12 ≈ 49,000 operations per window
- **~340× speedup** using Cooley-Tukey divide-and-conquer

---

## Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.10+, FastAPI, Uvicorn |
| DSP | NumPy, SciPy (FFT/STFT), Librosa |
| Visualization | Matplotlib (rendered server-side as PNG) |
| Storage | JSON flat file (no database setup needed) |
| Frontend | Vanilla HTML/CSS/JS (zero build step) |

---

## Project Structure

```
freqfind/
├── backend/
│   ├── audio/
│   │   ├── __init__.py
│   │   └── fingerprint.py     # Core FFT + fingerprinting engine
│   ├── database/
│   │   ├── __init__.py
│   │   ├── db.py              # Hash storage and matching
│   │   └── fingerprints.json  # Auto-generated database
│   └── main.py                # FastAPI app
├── frontend/
│   └── index.html             # Full SPA (single file)
├── sample_songs/              # Auto-generated WAV demos
├── generate_samples.py        # Synthesize demo audio
├── index_samples.py           # Bulk-index demo songs
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/freqfind.git
cd freqfind
pip install -r requirements.txt
```

### 2. Generate Sample Songs & Index Them

```bash
# Creates 5 synthesized WAV files in ./sample_songs/
python generate_samples.py

# Fingerprints and stores them in the database
python index_samples.py
```

### 3. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 4. Open the Frontend

Just open `frontend/index.html` in your browser. No build step needed.

Or serve it locally:
```bash
cd frontend && python -m http.server 3000
# open http://localhost:3000
```

### 5. Identify a Song

- Go to the **Identify** tab
- Upload one of the WAV files from `./sample_songs/`
- See the spectrogram, FFT snapshot, and match results

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/songs` | List all indexed songs |
| GET | `/stats` | Database statistics |
| POST | `/songs/add` | Index a new song (multipart: file, title, artist) |
| POST | `/identify` | Identify a song clip (multipart: file) |
| DELETE | `/songs/{id}` | Remove a song |

---

## Key Parameters (fingerprint.py)

| Parameter | Value | Description |
|---|---|---|
| `SAMPLE_RATE` | 22050 Hz | Audio sample rate |
| `FFT_WINDOW_SIZE` | 4096 | Samples per FFT frame (~186ms) |
| `FFT_OVERLAP` | 50% | Frame overlap for STFT |
| `PEAK_NEIGHBORHOOD` | 20 | Local max search radius |
| `MIN_AMPLITUDE` | -30 dB | Noise floor threshold |
| `FAN_OUT` | 15 | Pairs per anchor peak |
| `TIME_DELTA_MAX` | 200 | Max frame offset between peak pairs |

---

## References

- Wang, A. (2003). *An Industrial-Strength Audio Search Algorithm*. Shazam Entertainment.
- Cooley, J. W., & Tukey, J. W. (1965). *An Algorithm for the Machine Calculation of Complex Fourier Series*. Mathematics of Computation.
- Librosa: McFee et al. (2015). *librosa: Audio and Music Signal Analysis in Python*.

---

## Future Improvements

- [ ] Real-time microphone identification (Web Audio API)
- [ ] Noise robustness testing (add Gaussian noise to queries)
- [ ] GPU-accelerated FFT with CuPy
- [ ] PostgreSQL backend for large-scale deployment
- [ ] Docker container + Render deployment
- [ ] Top-N match visualization with timeline alignment plot
- [ ] Support for YouTube URL indexing

---

## License

MIT — built for educational purposes. Go learn some signal processing 🎛️
