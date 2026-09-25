"""Unit tests for VoiceStudio sidecar provider (declared httpx mocks, no live backend)."""

import base64
import os
from unittest.mock import AsyncMock, patch

import pytest


def test_disabled_by_default(monkeypatch):
    from speech_mcp.providers import voicestudio as vs

    monkeypatch.delenv("VOICESTUDIO_ENABLED", raising=False)
    assert vs.is_enabled() is False


def test_config_defaults(monkeypatch):
    from speech_mcp.providers.voicestudio import config_from_env

    for key in ("VOICESTUDIO_URL", "VOICESTUDIO_CLIENT_ID", "VOICESTUDIO_TIMEOUT_S", "VOICESTUDIO_BASE_PATH"):
        monkeypatch.delenv(key, raising=False)
    cfg = config_from_env()
    assert cfg.base_url == "http://127.0.0.1:3900"
    assert cfg.client_id == "speech-mcp"
    assert cfg.timeout_s == 120.0
    assert cfg.base_path is None


@pytest.mark.asyncio
async def test_health_probe_unavailable(monkeypatch):
    import httpx

    from speech_mcp.providers.voicestudio import VoiceStudioConfig, VoiceStudioProvider

    async def _boom(*args, **kwargs):
        raise httpx.ConnectError("refused")

    provider = VoiceStudioProvider(VoiceStudioConfig(base_url="http://127.0.0.1:3900"))
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = _boom
        result = await provider.health_probe()
    assert result["available"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_synthesize_base64_path():
    from speech_mcp.providers.voicestudio import VoiceStudioConfig, VoiceStudioProvider

    provider = VoiceStudioProvider(VoiceStudioConfig(base_url="http://127.0.0.1:3900"))
    wav = b"RIFF" + b"\x00" * 40
    payload = {"wav_base64": base64.b64encode(wav).decode("ascii")}
    with patch.object(provider, "_mcp_call", AsyncMock(return_value=payload)):
        result = await provider.synthesize("hello", "default")
    assert result["success"] is True
    assert result["wav_bytes"] == wav


@pytest.mark.asyncio
async def test_synthesize_audio_url_download():
    from speech_mcp.providers.voicestudio import VoiceStudioConfig, VoiceStudioProvider

    provider = VoiceStudioProvider(VoiceStudioConfig(base_url="http://127.0.0.1:3900"))
    with patch.object(provider, "_mcp_call", AsyncMock(return_value={"audio_url": "/audio/abc.wav"})):
        with patch.object(provider, "_download_audio_url", AsyncMock(return_value=b"WAVBYTES")):
            data = await provider.synthesize_wav("hello", "morgan")
    assert data == b"WAVBYTES"


@pytest.mark.asyncio
async def test_synthesize_backend_down_returns_dialogic():
    from speech_mcp.providers.voicestudio import VoiceStudioConfig, VoiceStudioProvider

    provider = VoiceStudioProvider(VoiceStudioConfig(base_url="http://127.0.0.1:3900"))
    with patch.object(provider, "_mcp_call", AsyncMock(side_effect=RuntimeError("refused"))):
        result = await provider.synthesize("hello")
    assert result["success"] is False
    assert result["provider"] == "voicestudio"
    assert "suggestions" in result


@pytest.mark.asyncio
async def test_clone_missing_file():
    from speech_mcp.providers.voicestudio import VoiceStudioProvider

    provider = VoiceStudioProvider()
    result = await provider.clone_voice("morgan", "D:/nonexistent/ref.wav")
    assert result["success"] is False


@pytest.mark.asyncio
async def test_extract_mcp_result_envelope():
    from dataclasses import dataclass

    from mcp.types import TextContent

    from speech_mcp.providers.voicestudio import _extract_mcp_result

    @dataclass
    class _FakeCallToolResult:
        content: list
        data: object = None
        structured_content: dict | None = None

    result = _FakeCallToolResult(content=[TextContent(type="text", text='{"profile_id": "p1"}')])
    assert _extract_mcp_result(result) == {"profile_id": "p1"}


def test_env_flag_enables(monkeypatch):
    from speech_mcp.providers import voicestudio as vs

    monkeypatch.setenv("VOICESTUDIO_ENABLED", "true")
    assert vs.is_enabled() is True
    assert os.getenv("VOICESTUDIO_ENABLED") == "true"
