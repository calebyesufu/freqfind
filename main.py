"""
FreqFind API — Shazam-like Music Identification Backend
========================================================
FastAPI application exposing endpoints for:
  - Indexing songs (POST /songs/add)
  - Identifying songs (POST /identify)
  - Listing the database (GET /songs)
  - Database stats (GET /stats)
  - Health check (GET /health)
"""

import os
import sys
import tempfile
import base64
import io

from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from fingerprint import fingerprint_audio, load_audio, compute_spectrogram, find_peaks
from db import add_song, match_song, list_songs, delete_song, get_db_stats

app = FastAPI(
    title="FreqFind",
    description="FFT-based music identification API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = tempfile.mkdtemp()


def fig_to_base64(fig) -> str:
    """Convert a matplotlib figure to a base64 PNG string."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor(), edgecolor="none")
    buf.seek(0)
    encoded = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return encoded


def render_spectrogram(frequencies, times, Sxx_db, peaks=None) -> str:
    """Render a dark-mode spectrogram with optional peak overlay."""
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor("#0d0d14")
    ax.set_facecolor("#0d0d14")

    # Plot spectrogram as heatmap
    vmin = np.percentile(Sxx_db, 5)
    vmax = np.percentile(Sxx_db, 99)

    freqs_arr = np.array(frequencies)
    times_arr = np.array(times)
    Sxx_arr   = np.array(Sxx_db)

    # Only show up to 8000 Hz (most musical content)
    freq_mask = freqs_arr <= 8000
    Sxx_plot  = Sxx_arr[freq_mask, :]

    im = ax.pcolormesh(
        times_arr, freqs_arr[freq_mask], Sxx_plot,
        shading="auto",
        cmap="inferno",
        vmin=vmin,
        vmax=vmax
    )

    # Overlay peaks
    if peaks:
        peak_times  = [times_arr[min(t, len(times_arr)-1)] for (t, f) in peaks if f < np.sum(freq_mask)]
        peak_freqs  = [freqs_arr[f] for (t, f) in peaks if f < np.sum(freq_mask)]
        ax.scatter(peak_times, peak_freqs, color="#00f5c4", s=8, alpha=0.7,
                   linewidths=0, label="Peaks", zorder=3)

    cbar = plt.colorbar(im, ax=ax, pad=0.01)
    cbar.set_label("dB", color="#aaa", fontsize=9)
    cbar.ax.yaxis.set_tick_params(color="#aaa")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#aaa")

    ax.set_xlabel("Time (s)", color="#aaa", fontsize=9)
    ax.set_ylabel("Frequency (Hz)", color="#aaa", fontsize=9)
    ax.tick_params(colors="#aaa", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

    plt.tight_layout(pad=0.5)
    return fig_to_base64(fig)


def render_fft_snapshot(audio, sr, start_sec=1.0) -> str:
    """Render the FFT of a single window — educational frequency domain view."""
    from fingerprint import FFT_WINDOW_SIZE
    from scipy.fft import fft, fftfreq

    start_sample = int(start_sec * sr)
    end_sample   = start_sample + FFT_WINDOW_SIZE
    if end_sample > len(audio):
        start_sample = 0
        end_sample   = min(FFT_WINDOW_SIZE, len(audio))

    window_data = audio[start_sample:end_sample]
    if len(window_data) < FFT_WINDOW_SIZE:
        window_data = np.pad(window_data, (0, FFT_WINDOW_SIZE - len(window_data)))

    # Apply Hann window before FFT
    hann = np.hanning(len(window_data))
    windowed = window_data * hann

    # === THE FFT ===
    # This is where the magic happens: O(N log N) DFT via Cooley-Tukey algorithm
    spectrum = fft(windowed)
    freqs    = fftfreq(len(windowed), d=1.0/sr)

    # Take only positive frequencies (FFT output is symmetric for real signals)
    pos_mask      = freqs >= 0
    freqs_pos     = freqs[pos_mask]
    magnitude_pos = np.abs(spectrum[pos_mask])

    # Limit to 8000 Hz
    hz_mask   = freqs_pos <= 8000
    freqs_plt = freqs_pos[hz_mask]
    mag_plt   = magnitude_pos[hz_mask]

    fig, ax = plt.subplots(figsize=(10, 3))
    fig.patch.set_facecolor("#0d0d14")
    ax.set_facecolor("#0d0d14")

    ax.fill_between(freqs_plt, mag_plt, alpha=0.4, color="#6e40c9")
    ax.plot(freqs_plt, mag_plt, color="#a855f7", linewidth=0.8)

    ax.set_xlabel("Frequency (Hz)", color="#aaa", fontsize=9)
    ax.set_ylabel("|X(f)|  Magnitude", color="#aaa", fontsize=9)
    ax.set_title(f"FFT Snapshot at t ≈ {start_sec:.1f}s", color="#ddd", fontsize=10)
    ax.tick_params(colors="#aaa", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")
    ax.set_xlim(0, 8000)

    plt.tight_layout(pad=0.5)
    return fig_to_base64(fig)


# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "FreqFind"}


@app.get("/songs")
def get_songs():
    return {"songs": list_songs()}


@app.get("/stats")
def stats():
    return get_db_stats()


@app.post("/songs/add")
async def index_song(
    file: UploadFile = File(...),
    title: str = Form(...),
    artist: str = Form(default="Unknown Artist"),
):
    """
    Index a song into the fingerprint database.
    Accepts WAV or MP3 files.
    """
    allowed_types = {"audio/wav", "audio/mpeg", "audio/mp3", "audio/x-wav",
                     "audio/wave", "application/octet-stream"}

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".wav", ".mp3"]:
        raise HTTPException(400, f"Unsupported file type: {ext}. Use .wav or .mp3")

    # Save upload to temp file
    tmp_path = os.path.join(UPLOAD_DIR, f"index_{file.filename}")
    content  = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        result  = fingerprint_audio(tmp_path)
        song_id = add_song(title, artist, result["hashes"], result["duration"])

        return {
            "success": True,
            "song_id": song_id,
            "title": title,
            "artist": artist,
            "duration": result["duration"],
            "num_peaks": result["num_peaks"],
            "num_hashes": result["num_hashes"],
            "message": f"✅ '{title}' indexed with {result['num_hashes']} fingerprint hashes."
        }
    except Exception as e:
        raise HTTPException(500, f"Processing error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/identify")
async def identify_song(file: UploadFile = File(...)):
    """
    Identify a song from a short audio clip.
    Returns top matches with confidence scores + visualization data.
    """
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".wav", ".mp3"]:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    tmp_path = os.path.join(UPLOAD_DIR, f"query_{file.filename}")
    content  = await file.read()
    with open(tmp_path, "wb") as f:
        f.write(content)

    try:
        # Fingerprint the query clip
        result = fingerprint_audio(tmp_path)

        # Match against database
        matches = match_song(result["hashes"], top_n=5)

        # Generate visualizations
        audio, sr = load_audio(tmp_path)
        freqs_arr = np.array(result["frequencies"])
        times_arr = np.array(result["times"])
        Sxx_arr   = np.array(result["spectrogram"])

        spectrogram_img = render_spectrogram(
            result["frequencies"],
            result["times"],
            result["spectrogram"],
            peaks=result["peaks"]
        )
        fft_img = render_fft_snapshot(audio, sr)

        return {
            "success": True,
            "query_info": {
                "duration": result["duration"],
                "num_peaks": result["num_peaks"],
                "num_hashes": result["num_hashes"],
            },
            "matches": matches,
            "top_match": matches[0] if matches else None,
            "spectrogram_png": spectrogram_img,
            "fft_png": fft_img,
            "waveform": result["waveform"],
        }
    except Exception as e:
        raise HTTPException(500, f"Identification error: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.delete("/songs/{song_id}")
def remove_song(song_id: str):
    if delete_song(song_id):
        return {"success": True, "message": f"Song {song_id} removed."}
    raise HTTPException(404, f"Song {song_id} not found.")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
