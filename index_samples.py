"""
Auto-index all sample songs into the FreqFind database.
Run this after generate_samples.py to populate the database.
"""

import os

from fingerprint import fingerprint_audio
from db import add_song, get_db_stats

SONGS_META = [
    {"filename": "ode_to_joy.wav",        "title": "Ode to Joy",                  "artist": "Beethoven"},
    {"filename": "twinkle.wav",            "title": "Twinkle Twinkle Little Star", "artist": "Traditional"},
    {"filename": "fur_elise.wav",          "title": "Für Elise",                   "artist": "Beethoven"},
    {"filename": "happy_birthday.wav",     "title": "Happy Birthday",              "artist": "Traditional"},
    {"filename": "jingle_bells.wav",       "title": "Jingle Bells",               "artist": "Traditional"},
]

SONGS_DIR = os.path.join(os.path.dirname(__file__), "sample_songs")

if __name__ == "__main__":
    print("📀 Indexing sample songs...\n")

    for meta in SONGS_META:
        path = os.path.join(SONGS_DIR, meta["filename"])
        if not os.path.exists(path):
            print(f"  ⚠️  Not found: {path} — run generate_samples.py first")
            continue

        print(f"  🔍 Processing: {meta['title']}...")
        result  = fingerprint_audio(path)
        song_id = add_song(meta["title"], meta["artist"], result["hashes"], result["duration"])
        print(f"     ✅ Indexed as ID={song_id} | {result['num_peaks']} peaks | {result['num_hashes']} hashes")

    stats = get_db_stats()
    print(f"\n✨ Database now has {stats['total_songs']} songs and {stats['total_hashes']} hashes.")
