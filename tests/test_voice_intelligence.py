"""Tests for the voice intelligence feature set (memory, macros, analytics,
voice bank, sound events, personas). Isolated SQLite via DB_PATH patch."""

import math
import struct
import wave

import pytest

import speech_mcp.storage as storage


@pytest.fixture
def iso_db(tmp_path, monkeypatch):
    """Point storage at a temp SQLite DB so tests never touch real data/."""
    monkeypatch.setattr(storage, "_DATA_DIR", str(tmp_path))
    monkeypatch.setattr(storage, "DB_PATH", str(tmp_path / "test_speech_mcp.db"))
    yield storage


# ---------------------------------------------------------------------------
# Voice memory
# ---------------------------------------------------------------------------


def test_memory_store_recall_search(iso_db):
    storage.memory_store("Remember to buy milk", kind="note", topic="errands", speaker="Sandra")
    storage.memory_store("Say hello to Benny", kind="tts", provider="gemini")
    storage.memory_store("Meeting with Klaus at 4pm", kind="stt", speaker="Klaus")

    rec = storage.memory_recall(limit=10)
    assert len(rec) == 3
    assert rec[0]["text"] == "Meeting with Klaus at 4pm"  # newest first

    by_kind = storage.memory_recall(limit=10, kind="note")
    assert len(by_kind) == 1
    assert by_kind[0]["text"] == "Remember to buy milk"

    hits = storage.memory_search("milk")
    assert len(hits) == 1
    assert hits[0]["topic"] == "errands"

    assert storage.memory_stats()["total"] == 3


# ---------------------------------------------------------------------------
# Voice macros
# ---------------------------------------------------------------------------


def test_macro_lifecycle(iso_db):
    storage.macro_create("morning", label="Morning ritual", actions=[{"type": "weather", "target": "Vienna"}])
    (storage.macro_create("say hello", actions=[{"type": "tts", "text": "Hello"}]),)

    assert len(storage.macro_list()) == 2

    macro = storage.macro_get("Morning")  # case-insensitive
    assert macro is not None
    assert macro["actions"] == [{"type": "weather", "target": "Vienna"}]

    dup = storage.macro_create("morning", actions=[])
    assert "error" in dup  # unique phrase

    assert storage.macro_delete("morning") is True
    assert storage.macro_get("morning") is None
    assert storage.macro_delete("morning") is False


@pytest.mark.asyncio
async def test_macro_run_actions(iso_db):
    async def fake_speak(text, provider="windows", voice_id="default"):
        return {"success": True, "provider": provider}

    async def fake_weather(loc):
        return {"success": True, "location": loc, "temp": "21C"}

    from speech_mcp.tools.macros import _run_actions

    outcome = await _run_actions(
        [
            {"type": "weather", "target": "Vienna"},
            {"type": "tts", "text": "All good"},
            {"type": "bogus"},
        ],
        fake_speak,
        fake_weather,
    )
    assert outcome["ok_all"] is False  # bogus action fails, others succeed
    assert outcome["results"][0]["action"] == "weather"
    assert outcome["results"][1]["ok"] is True
    assert outcome["results"][2]["ok"] is False


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------


def test_analytics_summary(iso_db):
    storage.analytics_record("gemini", "tts", 120.0, success=True, source="tool")
    storage.analytics_record("gemini", "tts", 200.0, success=True, source="tool")
    storage.analytics_record("gemini", "tts", 400.0, success=False, source="tool")
    storage.analytics_record("windows", "tts", 30.0, success=True, source="rest")

    summary = storage.analytics_summary(hours=24)
    assert summary["total_calls"] == 4
    g = summary["providers"]["gemini"]
    assert g["calls"] == 3
    assert g["errors"] == 1
    assert g["success_rate"] == pytest.approx(0.667, abs=0.001)
    assert g["avg_latency_ms"] == pytest.approx(240.0)
    assert g["p95_latency_ms"] is not None
    assert summary["providers"]["windows"]["avg_latency_ms"] == 30.0


# ---------------------------------------------------------------------------
# Voice bank
# ---------------------------------------------------------------------------


def test_voice_bank_lifecycle(iso_db):
    res = storage.voice_profile_register(
        "benny", "elevenlabs", "ABC123", source="elevenlabs", description="Benny voice"
    )
    assert res["success"] is True

    prof = storage.voice_profile_get("benny")
    assert prof is not None
    assert prof["provider"] == "elevenlabs"
    assert prof["voice_id"] == "ABC123"

    dup = storage.voice_profile_register("benny", "gemini", "Kore")
    assert "error" in dup

    assert len(storage.voice_profile_list()) == 1
    assert storage.voice_profile_delete("benny") is True
    assert storage.voice_profile_get("benny") is None


# ---------------------------------------------------------------------------
# Sound events (deterministic generated WAV)
# ---------------------------------------------------------------------------


def _write_test_wav(path: str, rate: int = 8000):
    """0.5s silence + 0.3s loud 440 Hz tone + 0.2s silence."""
    n_silence = int(0.5 * rate)
    n_tone = int(0.3 * rate)
    n_tail = int(0.2 * rate)
    frames = bytearray()
    for _ in range(n_silence):
        frames += struct.pack("<h", 0)
    for i in range(n_tone):
        sample = int(0.8 * 32767 * math.sin(2 * math.pi * 440 * i / rate))
        frames += struct.pack("<h", sample)
    for _ in range(n_tail):
        frames += struct.pack("<h", 0)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(frames))


def test_sound_event_detection(tmp_path):
    from speech_mcp.tools.sound_events import detect_events

    wav = tmp_path / "tone.wav"
    _write_test_wav(str(wav))

    result = detect_events(str(wav), threshold_db=-30.0, min_duration_s=0.1)
    assert result["success"] is True
    assert result["count"] >= 1
    event = result["events"][0]
    assert event["label"] == "loud_event"
    assert 0.45 <= event["start_s"] <= 0.55  # tone onset around 0.5s
    assert event["peak_db"] > -6  # 0.8 amplitude -> ~-2 dBFS
    assert abs(result["duration_s"] - 1.0) < 0.1


# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------


def test_personas():
    from speech_mcp.personas import PERSONAS, persona_system

    assert len(PERSONAS) >= 4
    names = {p["name"] for p in PERSONAS}
    assert "custom" in names
    assert persona_system("custom") == ""
    assert persona_system("engineer") != ""
    assert persona_system("does-not-exist") == ""
