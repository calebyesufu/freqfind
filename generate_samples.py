"""
Generate synthetic demo songs for the FreqFind database.
These are simple sine-wave compositions to demonstrate the fingerprinting system.
In a real deployment, you'd replace these with actual audio files.
"""

import numpy as np
from scipy.io import wavfile
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "sample_songs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

SR = 22050  # Sample rate

def note_freq(note: str) -> float:
    """Convert note name to frequency (A4 = 440 Hz standard)."""
    notes = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    octave = int(note[-1])
    semitone = notes[note[0]]
    if "#" in note:
        semitone += 1
    # A4 = 440 Hz, MIDI number = 12*(octave+1) + semitone
    midi = 12 * (octave + 1) + semitone
    return 440.0 * (2 ** ((midi - 69) / 12))


def sine_wave(freq: float, duration: float, amplitude: float = 0.5) -> np.ndarray:
    t = np.linspace(0, duration, int(SR * duration), endpoint=False)
    # Add harmonics for richer tone
    wave = (amplitude * np.sin(2 * np.pi * freq * t)
            + 0.3 * amplitude * np.sin(2 * np.pi * 2 * freq * t)
            + 0.15 * amplitude * np.sin(2 * np.pi * 3 * freq * t))
    # Apply envelope (attack + release)
    env = np.ones_like(wave)
    attack = int(0.02 * SR)
    release = int(0.05 * SR)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release)
    return wave * env


def compose(melody: list[tuple[str, float]], tempo_bpm: float = 120) -> np.ndarray:
    """Compose a melody from list of (note, beats) pairs."""
    beat_duration = 60.0 / tempo_bpm
    audio = []
    for note, beats in melody:
        dur = beats * beat_duration
        if note == "R":  # Rest
            audio.append(np.zeros(int(SR * dur)))
        else:
            audio.append(sine_wave(note_freq(note), dur))
    return np.concatenate(audio).astype(np.float32)


# ─── Song Definitions ─────────────────────────────────────────────────────────

SONGS = [
    {
        "filename": "ode_to_joy.wav",
        "title": "Ode to Joy",
        "artist": "Beethoven",
        "melody": [
            ("E4", 1), ("E4", 1), ("F4", 1), ("G4", 1),
            ("G4", 1), ("F4", 1), ("E4", 1), ("D4", 1),
            ("C4", 1), ("C4", 1), ("D4", 1), ("E4", 1),
            ("E4", 1.5), ("D4", 0.5), ("D4", 2),
            ("E4", 1), ("E4", 1), ("F4", 1), ("G4", 1),
            ("G4", 1), ("F4", 1), ("E4", 1), ("D4", 1),
            ("C4", 1), ("C4", 1), ("D4", 1), ("E4", 1),
            ("D4", 1.5), ("C4", 0.5), ("C4", 2),
        ],
        "tempo": 108,
    },
    {
        "filename": "twinkle.wav",
        "title": "Twinkle Twinkle Little Star",
        "artist": "Traditional",
        "melody": [
            ("C4", 1), ("C4", 1), ("G4", 1), ("G4", 1),
            ("A4", 1), ("A4", 1), ("G4", 2),
            ("F4", 1), ("F4", 1), ("E4", 1), ("E4", 1),
            ("D4", 1), ("D4", 1), ("C4", 2),
            ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1),
            ("E4", 1), ("E4", 1), ("D4", 2),
            ("G4", 1), ("G4", 1), ("F4", 1), ("F4", 1),
            ("E4", 1), ("E4", 1), ("D4", 2),
        ],
        "tempo": 100,
    },
    {
        "filename": "fur_elise.wav",
        "title": "Für Elise",
        "artist": "Beethoven",
        "melody": [
            ("E5", 0.5), ("D#5", 0.5), ("E5", 0.5), ("D#5", 0.5),
            ("E5", 0.5), ("B4", 0.5), ("D5", 0.5), ("C5", 0.5),
            ("A4", 2), ("R", 0.5),
            ("C4", 0.5), ("E4", 0.5), ("A4", 0.5),
            ("B4", 2), ("R", 0.5),
            ("E4", 0.5), ("G#4", 0.5), ("B4", 0.5),
            ("C5", 2), ("R", 0.5),
            ("E4", 0.5), ("E5", 0.5), ("D#5", 0.5),
            ("E5", 0.5), ("D#5", 0.5), ("E5", 0.5),
            ("B4", 0.5), ("D5", 0.5), ("C5", 0.5),
            ("A4", 2),
        ],
        "tempo": 84,
    },
    {
        "filename": "happy_birthday.wav",
        "title": "Happy Birthday",
        "artist": "Traditional",
        "melody": [
            ("C4", 0.75), ("C4", 0.25), ("D4", 1), ("C4", 1), ("F4", 1), ("E4", 2),
            ("C4", 0.75), ("C4", 0.25), ("D4", 1), ("C4", 1), ("G4", 1), ("F4", 2),
            ("C4", 0.75), ("C4", 0.25), ("C5", 1), ("A4", 1), ("F4", 1), ("E4", 1), ("D4", 2),
            ("A#4", 0.75), ("A#4", 0.25), ("A4", 1), ("F4", 1), ("G4", 1), ("F4", 2),
        ],
        "tempo": 90,
    },
    {
        "filename": "jingle_bells.wav",
        "title": "Jingle Bells",
        "artist": "Traditional",
        "melody": [
            ("E4", 1), ("E4", 1), ("E4", 2),
            ("E4", 1), ("E4", 1), ("E4", 2),
            ("E4", 1), ("G4", 1), ("C4", 1), ("D4", 1), ("E4", 4),
            ("F4", 1), ("F4", 1), ("F4", 1), ("F4", 1),
            ("F4", 1), ("E4", 1), ("E4", 1), ("E4", 1),
            ("E4", 1), ("D4", 1), ("D4", 1), ("E4", 1), ("D4", 2), ("G4", 2),
        ],
        "tempo": 120,
    },
]


if __name__ == "__main__":
    print("🎵 Generating sample songs...\n")
    for song in SONGS:
        audio = compose(song["melody"], song["tempo"])
        # Normalize to prevent clipping
        audio = audio / np.max(np.abs(audio) + 1e-8) * 0.85
        # Convert to 16-bit PCM
        audio_int = (audio * 32767).astype(np.int16)
        path = os.path.join(OUTPUT_DIR, song["filename"])
        wavfile.write(path, SR, audio_int)
        duration = len(audio) / SR
        print(f"  ✅ {song['title']} by {song['artist']} — {duration:.1f}s → {song['filename']}")

    print(f"\n✨ Generated {len(SONGS)} songs in ./sample_songs/")
    print("\nTo index them into the database, run:")
    print("  python index_samples.py")
