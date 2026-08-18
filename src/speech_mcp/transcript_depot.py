"""Transcript depot: SQLite index + on-disk SRT/change-log files.

Stores generated / revised subtitles with a draft -> revised -> reviewed
lifecycle. Files live under data/transcripts/{id}/ next to a SQLite index
(data/transcripts/depot.sqlite3). Exposed as transcript://{id} resources and
via REST so other fleet servers can ask "does episode X have a reviewed SRT?".
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
import time

logger = logging.getLogger(__name__)

_lock = threading.Lock()

DEPOT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "transcripts")
DB_PATH = os.path.join(DEPOT_DIR, "depot.sqlite3")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transcripts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  series TEXT DEFAULT '',
  season INTEGER,
  episode INTEGER,
  title TEXT DEFAULT '',
  source TEXT DEFAULT 'upload',
  source_media_key TEXT DEFAULT '',
  language TEXT DEFAULT 'ja',
  status TEXT DEFAULT 'draft',
  model TEXT DEFAULT '',
  raw_srt_path TEXT DEFAULT '',
  revised_srt_path TEXT DEFAULT '',
  changes_path TEXT DEFAULT '',
  created_at TEXT,
  updated_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(DEPOT_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    return conn


def _row_dir(tid: int) -> str:
    return os.path.join(DEPOT_DIR, str(tid))


def record(
    srt: str,
    *,
    series: str = "",
    season: int | None = None,
    episode: int | None = None,
    title: str = "",
    source: str = "upload",
    source_media_key: str = "",
    language: str = "ja",
    model: str = "",
) -> dict:
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                """INSERT INTO transcripts
                   (series, season, episode, title, source, source_media_key,
                    language, status, model, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,'draft',?,?,?)""",
                (series, season, episode, title, source, source_media_key, language, model, now, now),
            )
            tid = cur.lastrowid
            if tid is None:
                raise RuntimeError("Failed to allocate transcript id")
            conn.commit()
        finally:
            conn.close()
    rdir = _row_dir(tid)
    os.makedirs(rdir, exist_ok=True)
    raw_path = os.path.join(rdir, "raw.srt")
    with open(raw_path, "w", encoding="utf-8") as fh:
        fh.write(srt)
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE transcripts SET raw_srt_path=? WHERE id=?", (raw_path, tid))
            conn.commit()
        finally:
            conn.close()
    row = get(tid)
    if row is None:
        raise RuntimeError(f"Transcript #{tid} disappeared after insert")
    logger.info("Transcript depot: recorded #%s (%s S%sE%s)", tid, series, season, episode)
    return row


def save_revised(tid: int, revised_srt: str, changes: list[dict], model: str = "") -> dict | None:
    rdir = _row_dir(tid)
    os.makedirs(rdir, exist_ok=True)
    revised_path = os.path.join(rdir, "revised.srt")
    changes_path = os.path.join(rdir, "changes.json")
    with open(revised_path, "w", encoding="utf-8") as fh:
        fh.write(revised_srt)
    with open(changes_path, "w", encoding="utf-8") as fh:
        json.dump(changes, fh, ensure_ascii=False, indent=2)
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "UPDATE transcripts SET revised_srt_path=?, changes_path=?, status='revised', model=?, updated_at=? WHERE id=?",
                (revised_path, changes_path, model, now, tid),
            )
            conn.commit()
        finally:
            conn.close()
    return get(tid)


def set_status(tid: int, status: str) -> dict | None:
    if status not in ("draft", "revised", "reviewed"):
        raise ValueError("status must be draft, revised, or reviewed")
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ")
    with _lock:
        conn = _connect()
        try:
            conn.execute("UPDATE transcripts SET status=?, updated_at=? WHERE id=?", (status, now, tid))
            conn.commit()
        finally:
            conn.close()
    return get(tid)


def get(tid: int) -> dict | None:
    conn = _connect()
    try:
        row = conn.execute("SELECT * FROM transcripts WHERE id=?", (tid,)).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    return dict(row)


def list_transcripts(limit: int = 100) -> list[dict]:
    conn = _connect()
    try:
        rows = conn.execute("SELECT * FROM transcripts ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def read_file(path: str) -> str:
    if not path or not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def read_transcript(tid: int) -> dict | None:
    row = get(tid)
    if not row:
        return None
    row["raw_srt"] = read_file(row.get("raw_srt_path") or "")
    row["revised_srt"] = read_file(row.get("revised_srt_path") or "")
    changes = read_file(row.get("changes_path") or "")
    try:
        row["changes"] = json.loads(changes) if changes else []
    except Exception:
        row["changes"] = []
    return row
