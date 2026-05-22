"""
Fingerprint Database
====================
JSON-based storage for song fingerprints.

Database schema (fingerprints.json):
{
  "songs": {
    "song_id": {
      "id": str,
      "title": str,
      "artist": str,
      "duration": float,
      "num_hashes": int,
      "added_at": str
    }
  },
  "hashes": {
    "hash_string": [
      [song_id, time_offset],  // Each entry is a (song, offset) pair
      ...
    ]
  }
}

Matching Algorithm:
    For a query fingerprint Q:
    1. For each hash h in Q with offset t_q:
       - Look up all (song_id, t_db) pairs in the database
       - Compute time alignment: delta = t_db - t_q
    2. Group matches by (song_id, delta):
       - Real matches cluster at the same delta (songs align in time)
       - False matches scatter randomly
    3. Score = count of matches at the most common (song_id, delta)
    4. Confidence = score / max_possible_matches
"""

import json
import os
from collections import defaultdict
from datetime import datetime
import uuid


DB_PATH = os.path.join(os.path.dirname(__file__), "fingerprints.json")


def _load_db() -> dict:
    if not os.path.exists(DB_PATH):
        return {"songs": {}, "hashes": {}}
    with open(DB_PATH, "r") as f:
        return json.load(f)


def _save_db(db: dict):
    with open(DB_PATH, "w") as f:
        json.dump(db, f)


def add_song(title: str, artist: str, hashes: list[tuple[str, int]], duration: float) -> str:
    """
    Store a song's fingerprints in the database.

    Args:
        title   : Song title
        artist  : Artist name
        hashes  : List of (hash_string, time_offset) tuples from fingerprint_audio()
        duration: Song duration in seconds

    Returns:
        song_id : Unique identifier for the stored song
    """
    db = _load_db()

    song_id = str(uuid.uuid4())[:8]

    # Store song metadata
    db["songs"][song_id] = {
        "id": song_id,
        "title": title,
        "artist": artist,
        "duration": duration,
        "num_hashes": len(hashes),
        "added_at": datetime.now().isoformat(),
    }

    # Store each hash → (song_id, time_offset)
    for hash_val, time_offset in hashes:
        if hash_val not in db["hashes"]:
            db["hashes"][hash_val] = []
        db["hashes"][hash_val].append([song_id, time_offset])

    _save_db(db)
    return song_id


def match_song(query_hashes: list[tuple[str, int]], top_n: int = 5) -> list[dict]:
    """
    Match query fingerprints against the database.

    The key insight: for a correct match, all matching hashes must align
    at the same time offset. We use a histogram over (song_id, time_delta)
    pairs — the correct song will have a sharp spike in this histogram.

    Args:
        query_hashes : List of (hash_string, time_offset) from the query clip
        top_n        : How many top matches to return

    Returns:
        List of match dicts sorted by confidence score (descending)
    """
    db = _load_db()

    if not db["songs"]:
        return []

    # Histogram: (song_id, time_delta) → count of matching hashes
    matches = defaultdict(int)

    for hash_val, query_time in query_hashes:
        if hash_val in db["hashes"]:
            for song_id, db_time in db["hashes"][hash_val]:
                # Time alignment: offset between where this hash appears
                # in the database vs. where it appears in the query
                time_delta = db_time - query_time
                matches[(song_id, time_delta)] += 1

    if not matches:
        return []

    # Aggregate: for each song, find the best time alignment (max votes)
    song_scores = defaultdict(int)
    for (song_id, _), count in matches.items():
        song_scores[song_id] = max(song_scores[song_id], count)

    # Compute confidence scores
    max_score = max(song_scores.values()) if song_scores else 1
    results = []

    for song_id, score in song_scores.items():
        if song_id not in db["songs"]:
            continue

        song = db["songs"][song_id]
        confidence = round(score / max(song["num_hashes"] * 0.1, 1) * 100, 2)
        confidence = min(confidence, 99.9)  # Cap at 99.9%

        results.append({
            "song_id": song_id,
            "title": song["title"],
            "artist": song["artist"],
            "duration": song["duration"],
            "score": score,
            "confidence": confidence,
            "num_hashes_db": song["num_hashes"],
        })

    # Sort by raw score (most hash matches wins)
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]


def list_songs() -> list[dict]:
    """Return all songs currently in the database."""
    db = _load_db()
    return list(db["songs"].values())


def delete_song(song_id: str) -> bool:
    """Remove a song and all its hashes from the database."""
    db = _load_db()

    if song_id not in db["songs"]:
        return False

    db["songs"].pop(song_id)

    # Remove all hash entries for this song
    to_delete = []
    for hash_val, entries in db["hashes"].items():
        db["hashes"][hash_val] = [e for e in entries if e[0] != song_id]
        if not db["hashes"][hash_val]:
            to_delete.append(hash_val)
    for h in to_delete:
        del db["hashes"][h]

    _save_db(db)
    return True


def get_db_stats() -> dict:
    """Return database statistics."""
    db = _load_db()
    return {
        "total_songs": len(db["songs"]),
        "total_hashes": sum(len(v) for v in db["hashes"].values()),
        "unique_hash_keys": len(db["hashes"]),
    }
