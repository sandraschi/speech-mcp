"""Persistent local stores: voice memory, voice macros, analytics, voice bank.

Single SQLite database at ``data/speech_mcp.db`` (stdlib sqlite3 only, no heavy
deps). Every store uses short-lived connections guarded by a module lock -
safe for the FastMCP async event loop and for concurrent REST access.

Stores:
  memory_episodes  - episodic voice diary (persistent, cross-session recall)
  voice_macros     - spoken-phrase -> action bindings
  analytics_samples- per-call latency/cost telemetry
  voice_profiles   - voice bank (provider-routed voice profiles)
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

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DB_PATH = os.path.join(_DATA_DIR, "speech_mcp.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_episodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  kind TEXT NOT NULL DEFAULT 'note',
  speaker TEXT DEFAULT '',
  text TEXT NOT NULL,
  topic TEXT DEFAULT '',
  provider TEXT DEFAULT '',
  meta_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_memory_ts ON memory_episodes (ts);

CREATE TABLE IF NOT EXISTS voice_macros (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  phrase TEXT NOT NULL UNIQUE,
  label TEXT DEFAULT '',
  actions_json TEXT NOT NULL DEFAULT '[]',
  enabled INTEGER NOT NULL DEFAULT 1,
  created_at TEXT
);

CREATE TABLE IF NOT EXISTS analytics_samples (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  provider TEXT NOT NULL,
  op TEXT NOT NULL,
  latency_ms REAL,
  success INTEGER NOT NULL DEFAULT 1,
  source TEXT DEFAULT '',
  meta_json TEXT DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_analytics_ts ON analytics_samples (ts);

CREATE TABLE IF NOT EXISTS voice_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  provider TEXT NOT NULL,
  voice_id TEXT DEFAULT '',
  source TEXT DEFAULT 'custom',
  description TEXT DEFAULT '',
  meta_json TEXT DEFAULT '{}',
  created_at TEXT
);
"""


def _connect() -> sqlite3.Connection:
    os.makedirs(_DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.executescript(_SCHEMA)
    return conn


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _dumps(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Voice memory (episodic diary)
# ---------------------------------------------------------------------------


def memory_store(
    text: str,
    kind: str = "note",
    speaker: str = "",
    topic: str = "",
    provider: str = "",
    meta: dict | None = None,
) -> dict:
    """Persist a voice episode. Returns the stored row."""
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute(
                "INSERT INTO memory_episodes (ts, kind, speaker, text, topic, provider, meta_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (_now(), kind, speaker, text, topic, provider, _dumps(meta or {})),
            )
            conn.commit()
            eid = cur.lastrowid
        finally:
            conn.close()
    return {
        "id": eid,
        "ts": _now(),
        "kind": kind,
        "speaker": speaker,
        "text": text,
        "topic": topic,
        "provider": provider,
    }


def memory_recall(limit: int = 20, kind: str | None = None, topic: str | None = None) -> list[dict]:
    """Return the most recent episodes, newest first."""
    sql = "SELECT * FROM memory_episodes WHERE 1=1"
    params: list = []
    if kind:
        sql += " AND kind = ?"
        params.append(kind)
    if topic:
        sql += " AND topic = ?"
        params.append(topic)
    sql += " ORDER BY id DESC LIMIT ?"
    params.append(max(1, min(int(limit), 200)))
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            out = [dict(r) for r in rows]
            for r in out:
                r["meta"] = json.loads(r.pop("meta_json", "{}"))
        finally:
            conn.close()
    return out


def memory_search(query: str, limit: int = 10) -> list[dict]:
    """LIKE keyword search over episode text/topic/speaker."""
    like = f"%{query}%"
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT * FROM memory_episodes WHERE text LIKE ? OR topic LIKE ? OR speaker LIKE ?"
                " ORDER BY id DESC LIMIT ?",
                (like, like, like, max(1, min(int(limit), 100))),
            ).fetchall()
            out = [dict(r) for r in rows]
            for r in out:
                r["meta"] = json.loads(r.pop("meta_json", "{}"))
        finally:
            conn.close()
    return out


def memory_stats() -> dict:
    with _lock:
        conn = _connect()
        try:
            total = conn.execute("SELECT COUNT(*) AS c FROM memory_episodes").fetchone()["c"]
            by_kind = {
                r["kind"]: r["c"]
                for r in conn.execute("SELECT kind, COUNT(*) AS c FROM memory_episodes GROUP BY kind").fetchall()
            }
        finally:
            conn.close()
    return {"total": total, "by_kind": by_kind}


# ---------------------------------------------------------------------------
# Voice macros (phrase -> actions)
# ---------------------------------------------------------------------------


def macro_create(phrase: str, label: str = "", actions: list | None = None) -> dict:
    phrase = phrase.strip().lower()
    actions = actions or []
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO voice_macros (phrase, label, actions_json, created_at) VALUES (?, ?, ?, ?)",
                (phrase, label, _dumps(actions), _now()),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": f"Macro for phrase '{phrase}' already exists", "phrase": phrase}
        finally:
            conn.close()
    return {"success": True, "phrase": phrase, "label": label, "actions": actions}


def macro_list() -> list[dict]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT * FROM voice_macros ORDER BY id").fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["actions"] = json.loads(d.pop("actions_json", "[]"))
                out.append(d)
        finally:
            conn.close()
    return out


def macro_get(phrase: str) -> dict | None:
    phrase = phrase.strip().lower()
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM voice_macros WHERE phrase = ?", (phrase,)).fetchone()
            if row is None:
                return None
            d = dict(row)
            d["actions"] = json.loads(d.pop("actions_json", "[]"))
        finally:
            conn.close()
    return d


def macro_delete(phrase: str) -> bool:
    phrase = phrase.strip().lower()
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM voice_macros WHERE phrase = ?", (phrase,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Speech analytics (per-call telemetry)
# ---------------------------------------------------------------------------


def analytics_record(
    provider: str, op: str, latency_ms: float | None, success: bool = True, source: str = "", meta: dict | None = None
):
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO analytics_samples (ts, provider, op, latency_ms, success, source, meta_json)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (time.time(), provider, op, latency_ms, 1 if success else 0, source, _dumps(meta or {})),
            )
            conn.commit()
        finally:
            conn.close()


def analytics_summary(hours: float = 24.0) -> dict:
    """Per-provider summary for the last N hours: calls, avg/p95 latency, errors."""
    since = time.time() - hours * 3600
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute(
                "SELECT provider, op, latency_ms, success FROM analytics_samples WHERE ts >= ?",
                (since,),
            ).fetchall()
        finally:
            conn.close()

    per_provider: dict[str, dict] = {}
    for r in rows:
        p = per_provider.setdefault(r["provider"], {"calls": 0, "errors": 0, "latencies": []})
        p["calls"] += 1
        if not r["success"]:
            p["errors"] += 1
        if r["latency_ms"] is not None:
            p["latencies"].append(r["latency_ms"])

    providers = {}
    for name, p in per_provider.items():
        lat = sorted(p["latencies"])
        avg_ms = round(sum(lat) / len(lat), 1) if lat else None
        p95_ms = None
        if lat:
            p95_idx = min(int(len(lat) * 0.95), len(lat) - 1)
            p95_ms = round(lat[p95_idx], 1)
        providers[name] = {
            "calls": p["calls"],
            "errors": p["errors"],
            "success_rate": round(1 - (p["errors"] / p["calls"] if p["calls"] else 0), 3),
            "avg_latency_ms": avg_ms,
            "p95_latency_ms": p95_ms,
        }
    return {
        "window_hours": hours,
        "total_calls": len(rows),
        "providers": providers,
    }


def analytics_prune(hours: float = 24.0 * 14):
    """Prune samples older than ``hours`` (default 14 days)."""
    cutoff = time.time() - hours * 3600
    with _lock:
        conn = _connect()
        try:
            conn.execute("DELETE FROM analytics_samples WHERE ts < ?", (cutoff,))
            conn.commit()
        finally:
            conn.close()


# ---------------------------------------------------------------------------
# Voice bank (voice profiles)
# ---------------------------------------------------------------------------


def voice_profile_register(
    name: str,
    provider: str,
    voice_id: str = "",
    source: str = "custom",
    description: str = "",
    meta: dict | None = None,
) -> dict:
    with _lock:
        conn = _connect()
        try:
            conn.execute(
                "INSERT INTO voice_profiles (name, provider, voice_id, source, description, meta_json, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, provider, voice_id, source, description, _dumps(meta or {}), _now()),
            )
            conn.commit()
            pid = conn.execute("SELECT id FROM voice_profiles WHERE name = ?", (name,)).fetchone()["id"]
        except sqlite3.IntegrityError:
            conn.close()
            return {"error": f"Voice profile '{name}' already exists", "name": name}
        finally:
            conn.close()
    return {"success": True, "id": pid, "name": name, "provider": provider, "voice_id": voice_id, "source": source}


def voice_profile_list() -> list[dict]:
    with _lock:
        conn = _connect()
        try:
            rows = conn.execute("SELECT * FROM voice_profiles ORDER BY name").fetchall()
            out = []
            for r in rows:
                d = dict(r)
                d["meta"] = json.loads(d.pop("meta_json", "{}"))
                out.append(d)
        finally:
            conn.close()
    return out


def voice_profile_get(name: str) -> dict | None:
    with _lock:
        conn = _connect()
        try:
            row = conn.execute("SELECT * FROM voice_profiles WHERE name = ?", (name,)).fetchone()
            if row is None:
                return None
            d = dict(row)
            d["meta"] = json.loads(d.pop("meta_json", "{}"))
        finally:
            conn.close()
    return d


def voice_profile_delete(name: str) -> bool:
    with _lock:
        conn = _connect()
        try:
            cur = conn.execute("DELETE FROM voice_profiles WHERE name = ?", (name,))
            conn.commit()
            return cur.rowcount > 0
        finally:
            conn.close()
