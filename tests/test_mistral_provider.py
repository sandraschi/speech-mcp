"""Unit tests for the Mistral Voxtral 3 provider.

No network and no API key: a fake httpx client captures the exact request body
and returns canned responses, so the wire format is asserted rather than assumed.
Live verification needs MISTRAL_API_KEY and is deliberately out of scope here.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest

from speech_mcp.providers.mistral import (
    DEFAULT_STT_MODEL,
    MistralConfig,
    MistralProvider,
    MistralRealtimeSession,
    _normalize_segments,
    _validate_turn_detection,
)


class _FakeResponse:
    def __init__(self, status_code: int = 200, payload=None, text_body: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text_body

    def json(self):
        return self._payload


class _FakeClient:
    """Stand-in for httpx.AsyncClient that records outbound calls."""

    calls: list[dict] = []
    response: _FakeResponse = _FakeResponse()

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, **kwargs):
        type(self).calls.append({"method": "POST", "url": url, **kwargs})
        return type(self).response

    async def get(self, url, **kwargs):
        type(self).calls.append({"method": "GET", "url": url, **kwargs})
        return type(self).response


@pytest.fixture
def fake_http(monkeypatch):
    _FakeClient.calls = []
    _FakeClient.response = _FakeResponse()
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    return _FakeClient


@pytest.fixture
def audio_file(tmp_path):
    path = tmp_path / "clip.wav"
    path.write_bytes(b"RIFF....WAVEfmt ")
    return str(path)


@pytest.fixture
def hosted():
    return MistralProvider(MistralConfig(api_key="test-key"))


def test_config_requires_key_or_self_host():
    with pytest.raises(ValueError, match="MISTRAL_API_KEY"):
        MistralProvider(MistralConfig(api_key=""))
    # Self-hosted legitimately has no key.
    assert MistralProvider(MistralConfig(api_key="", self_hosted=True)).model_id == DEFAULT_STT_MODEL


async def test_transcribe_file_sends_diarize_and_context_bias(fake_http, hosted, audio_file):
    fake_http.response = _FakeResponse(
        payload={
            "model": "voxtral-small-transcribe-3",
            "language": "en",
            "text": "Hello Sandra.",
            "segments": [],
        }
    )

    result = await hosted.transcribe_file(audio_file, language="en")

    assert result["success"] is True
    assert result["text"] == "Hello Sandra."
    assert result["language"] == "en"
    call = fake_http.calls[0]
    assert call["url"].endswith("/v1/audio/transcriptions")
    assert call["headers"]["Authorization"] == "Bearer test-key"
    assert call["data"]["diarize"] == "true"
    assert call["data"]["language"] == "en"
    assert "FastMCP" in call["data"]["context_bias"]
    assert "file" in call["files"]


async def test_transcribe_file_auto_language_omits_field(fake_http, hosted, audio_file):
    fake_http.response = _FakeResponse(payload={"text": "ok", "segments": []})
    await hosted.transcribe_file(audio_file, language="auto")
    assert "language" not in fake_http.calls[0]["data"]


async def test_transcribe_file_self_hosted_skips_hosted_only_fields(fake_http, audio_file):
    local = MistralProvider(MistralConfig(api_key="", self_hosted=True, base_url="http://127.0.0.1:8000"))
    fake_http.response = _FakeResponse(payload={"text": "local", "segments": []})

    result = await local.transcribe_file(audio_file)

    assert result["success"] is True
    data = fake_http.calls[0]["data"]
    assert "diarize" not in data
    assert "context_bias" not in data
    assert fake_http.calls[0]["url"].startswith("http://127.0.0.1:8000")


async def test_transcribe_file_maps_http_errors(fake_http, hosted, audio_file):
    fake_http.response = _FakeResponse(status_code=429, text_body="slow down")
    result = await hosted.transcribe_file(audio_file)
    assert result["success"] is False
    assert "429" in result["error"]
    assert "rate limited" in result["error"]


async def test_transcribe_file_missing_path_is_not_a_request(fake_http, hosted):
    result = await hosted.transcribe_file("C:/nope/missing.wav")
    assert result["success"] is False
    assert fake_http.calls == []


async def test_segments_are_normalized_to_seconds(fake_http, hosted, audio_file):
    fake_http.response = _FakeResponse(
        payload={
            "text": "a b",
            "segments": [
                {"speaker": 1, "start_ms": 1500, "end_ms": 3200, "text": "first"},
                {"speaker_id": 2, "start": 3.5, "end": 4.25, "transcript": "second"},
                {"speaker": 1, "start": 1, "end": 2, "text": "   "},
            ],
        }
    )
    result = await hosted.transcribe_file(audio_file)
    assert [s["text"] for s in result["segments"]] == ["first", "second"]
    assert result["segments"][0]["start_s"] == 1.5
    assert result["segments"][1]["speaker"] == 2
    assert "[Speaker 1]" in result["formatted"]


def test_normalize_segments_ignores_junk():
    assert _normalize_segments([None, 3, {"text": ""}, {"text": "keep"}]) == [
        {"speaker": 1, "start_s": 0.0, "end_s": 0.0, "text": "keep"}
    ]


async def test_synthesize_wav_posts_json_and_decodes_audio(fake_http, hosted):
    pcm = b"RIFFfakewav"
    fake_http.response = _FakeResponse(payload={"audio_data": base64.b64encode(pcm).decode()})

    audio = await hosted.synthesize_wav("hello", voice_id="Sarah")

    assert audio == pcm
    call = fake_http.calls[0]
    assert call["url"].endswith("/v1/audio/speech")
    assert call["json"]["input"] == "hello"
    assert call["json"]["response_format"] == "wav"
    assert call["json"]["voice_id"] == "Sarah"


async def test_synthesize_wav_default_voice_is_omitted(fake_http, hosted):
    fake_http.response = _FakeResponse(payload={"audio_data": base64.b64encode(b"x").decode()})
    await hosted.synthesize_wav("hi", voice_id="default")
    assert "voice_id" not in fake_http.calls[0]["json"]


async def test_synthesize_wav_raises_on_error(fake_http, hosted):
    fake_http.response = _FakeResponse(status_code=401, text_body="bad key")
    with pytest.raises(RuntimeError, match="401"):
        await hosted.synthesize_wav("hi")


def test_turn_detection_rejects_inverted_thresholds():
    with pytest.raises(ValueError, match="end_threshold"):
        _validate_turn_detection({"start_threshold": 0.2, "eager_end_threshold": 0.5})
    with pytest.raises(ValueError, match="end_timeout_ms"):
        _validate_turn_detection({"min_silence_ms": 2000, "end_timeout_ms": 1000})


def test_turn_detection_merges_defaults():
    merged = _validate_turn_detection({"min_silence_ms": 300})
    assert merged["min_silence_ms"] == 300
    assert merged["end_threshold"] == 0.33


async def test_realtime_rejects_diarize_with_turn_detection():
    session = MistralRealtimeSession(MistralConfig(api_key="k"))
    with pytest.raises(ValueError, match="not compatible"):
        await session.connect(turn_detection={}, diarize=True)


async def test_realtime_connect_sends_session_update(monkeypatch):
    sent: list[dict] = []

    class _FakeWS:
        def __init__(self):
            self.recv_calls = 0

        async def recv(self):
            self.recv_calls += 1
            return json.dumps({"type": "session.created"})

        async def send(self, payload):
            sent.append(json.loads(payload))

        async def close(self):
            return None

    class _Ctx:
        def __await__(self):
            async def _resolve():
                return _FakeWS()

            return _resolve().__await__()

        async def __aenter__(self):
            return _FakeWS()

        async def __aexit__(self, *exc):
            return False

    captured: dict = {}

    def _connect(url, **kwargs):
        captured["url"] = url
        captured["headers"] = kwargs.get("additional_headers")
        return _Ctx()

    monkeypatch.setattr("speech_mcp.providers.mistral.websockets.connect", _connect)

    session = MistralRealtimeSession(MistralConfig(api_key="k"))
    created = await session.connect(sample_rate=16000, turn_detection={"min_silence_ms": 400})

    assert created["type"] == "session.created"
    assert captured["url"].startswith("wss://api.mistral.ai/v1/audio/transcriptions/realtime?model=")
    assert captured["headers"]["Authorization"] == "Bearer k"
    update = sent[0]
    assert update["type"] == "session.update"
    assert update["session"]["audio_format"] == {"encoding": "pcm_s16le", "sample_rate": 16000}
    assert update["session"]["turn_detection"]["min_silence_ms"] == 400


async def test_realtime_url_is_wss_for_self_hosted_http(monkeypatch):
    local = MistralConfig(api_key="", self_hosted=True, base_url="http://127.0.0.1:8000")
    assert local.realtime_url.startswith("ws://127.0.0.1:8000/v1/audio/transcriptions/realtime?model=")


# --- MCP surface: both tools must exist and degrade honestly when unconfigured ---


def _tool_result_data(result):
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        first = result.content[0]
        text = first.text if hasattr(first, "text") else str(first)
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}
    return result


@pytest.mark.asyncio
async def test_transcribe_audio_file_mistral_not_configured(mcp_app):
    """MISTRAL_ENABLED is unset in the test env, so the tool reports a usable recovery."""
    result = await mcp_app.call_tool("transcribe_audio_file", {"file_path": "C:/tmp/test.wav", "provider": "mistral"})
    data = _tool_result_data(result)
    assert data.get("success") is False
    assert "Mistral" in data.get("error", "")
    assert "MISTRAL_ENABLED" in data.get("recovery", "") or "MISTRAL_SELF_HOST_URL" in data.get("recovery", "")


@pytest.mark.asyncio
async def test_mistral_stream_tool_not_configured(mcp_app):
    result = await mcp_app.call_tool("mistral_transcribe_stream", {"action": "start"})
    data = _tool_result_data(result)
    assert data.get("success") is False
    assert data.get("error_type") == "not_enabled"
