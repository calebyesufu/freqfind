"""Seed demo songs when the fingerprint database is empty (e.g. fresh Render deploy)."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from db import get_db_stats, add_song
from fingerprint import fingerprint_audio
from index_samples import SONGS_META, SONGS_DIR


def seed():
    if get_db_stats()["total_songs"] > 0:
        print("Database already has songs — skip seed.")
        return

    if not os.path.isdir(SONGS_DIR):
        print("No sample_songs/ — skip seed.")
        return

    print("Seeding demo songs...")
    for meta in SONGS_META:
        path = os.path.join(SONGS_DIR, meta["filename"])
        if not os.path.exists(path):
            print(f"  skip missing: {meta['filename']}")
            continue
        result = fingerprint_audio(path)
        song_id = add_song(meta["title"], meta["artist"], result["hashes"], result["duration"])
        print(f"  indexed {meta['title']} -> {song_id}")

    stats = get_db_stats()
    print(f"Done: {stats['total_songs']} songs, {stats['total_hashes']} hashes.")


if __name__ == "__main__":
    seed()
