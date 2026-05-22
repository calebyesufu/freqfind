"""
Audio Fingerprinting Engine
============================
A simplified reimplementation of Shazam's core algorithm using FFT.

How it works:
1. Load audio and convert to mono
2. Apply Short-Time Fourier Transform (STFT) to get a spectrogram
3. Find local peak frequencies (constellation map)
4. Hash pairs of peaks with time offsets (combinatorial hashing)
5. Store/match hashes against a database

Mathematical Foundation:
    The Discrete Fourier Transform (DFT) converts a time-domain signal x[n]
    of length N into its frequency-domain representation X[k]:

        X[k] = Σ_{n=0}^{N-1} x[n] * e^{-j2πkn/N}

    The FFT computes this in O(N log N) instead of O(N²) by exploiting
    the symmetry of complex exponentials (Cooley-Tukey algorithm).
"""

import numpy as np
from scipy import signal
from scipy.ndimage import maximum_filter
from scipy.ndimage import generate_binary_structure, binary_erosion
import hashlib
import json


# ─── Constants ────────────────────────────────────────────────────────────────

SAMPLE_RATE        = 22050   # Hz — standard for music analysis
FFT_WINDOW_SIZE    = 4096    # Samples per FFT window (~186ms at 22050Hz)
FFT_OVERLAP        = 0.5     # 50% overlap between windows
HOP_LENGTH         = FFT_WINDOW_SIZE // 2

# Fingerprint peak extraction
PEAK_NEIGHBORHOOD  = 20      # Size of local max search window
MIN_AMPLITUDE      = -30     # dB threshold — ignore quiet frequencies
MAX_PEAKS_PER_WIN  = 5       # Max peaks to extract per time window

# Hash generation
FAN_OUT            = 15      # How many pairs to form per anchor peak
TIME_DELTA_MIN     = 1       # Min time offset between paired peaks
TIME_DELTA_MAX     = 200     # Max time offset between paired peaks
FREQ_BINS_MAX      = 1024    # Cap on frequency bin index


def load_audio(file_path: str) -> tuple[np.ndarray, int]:
    """
    Load an audio file and return (samples, sample_rate).
    Converts stereo to mono by averaging channels.
    """
    import librosa
    audio, sr = librosa.load(file_path, sr=SAMPLE_RATE, mono=True)
    return audio, sr


def compute_spectrogram(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the Short-Time Fourier Transform (STFT) spectrogram.

    The STFT slices the signal into overlapping windows and applies FFT to each:
        STFT(x)[m, k] = Σ_n x[n] * w[n - m*H] * e^{-j2πkn/N}

    where:
        w = Hann window (reduces spectral leakage)
        H = hop length (step between windows)
        N = FFT window size
        m = time frame index
        k = frequency bin index

    Returns:
        frequencies : array of frequency values (Hz)
        times       : array of time values (seconds)
        Sxx         : 2D power spectrogram in dB
    """
    # Apply Hann window to each frame — reduces spectral leakage at edges
    window = signal.windows.hann(FFT_WINDOW_SIZE)

    # scipy.signal.spectrogram internally uses FFT on each windowed frame
    frequencies, times, Sxx = signal.spectrogram(
        audio,
        fs=SAMPLE_RATE,
        window=window,
        nperseg=FFT_WINDOW_SIZE,
        noverlap=int(FFT_WINDOW_SIZE * FFT_OVERLAP),
        scaling='spectrum'
    )

    # Convert power to decibels: dB = 10 * log10(power)
    # This compresses the dynamic range and matches human hearing
    Sxx_db = 10 * np.log10(Sxx + 1e-10)

    return frequencies, times, Sxx_db


def find_peaks(Sxx_db: np.ndarray) -> list[tuple[int, int]]:
    """
    Find local maxima (peaks) in the spectrogram — the "constellation map".

    Shazam's key insight: instead of storing the entire spectrogram,
    only store the coordinates of prominent peaks. These are robust to noise
    because noise is spread across all frequencies while musical tones
    create sharp, stable peaks.

    Returns list of (time_idx, freq_idx) tuples.
    """
    # Create a 2D local maximum filter
    struct = generate_binary_structure(2, 1)
    neighborhood = maximum_filter(Sxx_db, size=PEAK_NEIGHBORHOOD)

    # A point is a local max if it equals the neighborhood maximum
    local_max = (Sxx_db == neighborhood)

    # Remove background noise below threshold
    background = (Sxx_db == Sxx_db.min())
    eroded = binary_erosion(background, structure=struct, border_value=1)
    detected_peaks = local_max ^ eroded  # XOR to get true peaks

    # Apply amplitude threshold
    amp_min_mask = Sxx_db > MIN_AMPLITUDE

    # Combine: must be local max AND above threshold
    peaks = np.argwhere(detected_peaks & amp_min_mask)

    # peaks are (freq_idx, time_idx) — transpose to (time_idx, freq_idx)
    if len(peaks) == 0:
        return []

    peaks_list = [(int(p[1]), int(p[0])) for p in peaks]  # (time, freq)
    peaks_list.sort(key=lambda x: x[0])  # sort by time
    return peaks_list


def generate_hashes(peaks: list[tuple[int, int]], song_id: str = None) -> list[tuple[str, int]]:
    """
    Generate fingerprint hashes using combinatorial hashing.

    For each "anchor" peak, we pair it with nearby "target" peaks and hash:
        hash = SHA1(freq1 | freq2 | time_delta)

    The time offset of the anchor is stored alongside the hash.
    This allows us to verify that multiple matching hashes occur at the
    same relative time offset — proving it's a real match, not a coincidence.

    Returns list of (hash_string, time_offset) tuples.
    """
    hashes = []

    for i, (t1, f1) in enumerate(peaks):
        # Fan out to the next FAN_OUT peaks within the time delta window
        for j in range(1, FAN_OUT + 1):
            if i + j >= len(peaks):
                break

            t2, f2 = peaks[i + j]
            time_delta = t2 - t1

            if time_delta < TIME_DELTA_MIN:
                continue
            if time_delta > TIME_DELTA_MAX:
                break

            # Cap frequency bins to avoid hash collisions
            f1_capped = min(f1, FREQ_BINS_MAX)
            f2_capped = min(f2, FREQ_BINS_MAX)

            # Create a unique hash from the pair of peaks
            # Format: "freq1:freq2:time_delta"
            hash_input = f"{f1_capped}:{f2_capped}:{time_delta}"
            hash_val = hashlib.sha1(hash_input.encode()).hexdigest()[:20]

            hashes.append((hash_val, t1))

    return hashes


def fingerprint_audio(file_path: str) -> dict:
    """
    Full pipeline: audio file → fingerprint hashes + visualization data.

    Returns a dict with:
        hashes      : list of (hash, time_offset) for matching
        frequencies : frequency axis for plots
        times       : time axis for plots
        spectrogram : 2D dB spectrogram for visualization
        peaks       : list of (time, freq) peak coordinates
        waveform    : downsampled audio samples for waveform plot
        sample_rate : audio sample rate
    """
    audio, sr = load_audio(file_path)
    frequencies, times, Sxx_db = compute_spectrogram(audio)
    peaks = find_peaks(Sxx_db)
    hashes = generate_hashes(peaks)

    # Downsample waveform for frontend (max 2000 points)
    step = max(1, len(audio) // 2000)
    waveform_samples = audio[::step].tolist()

    return {
        "hashes": hashes,
        "frequencies": frequencies.tolist(),
        "times": times.tolist(),
        "spectrogram": Sxx_db.tolist(),
        "peaks": peaks,
        "waveform": waveform_samples,
        "sample_rate": sr,
        "duration": float(len(audio) / sr),
        "num_peaks": len(peaks),
        "num_hashes": len(hashes),
    }
