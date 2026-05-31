"""Unit tests for FunASR provider and STT tools."""

import base64
import json
from unittest.mock import AsyncMock, patch

import pytest


def _tool_result_data(result):
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        text = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}
    return result


@pytest.mark.asyncio
async def test_transcribe_audio_file_not_found(mcp_app):
    result = await mcp_app.call_tool(
        "transcribe_audio_file",
        {"file_path": "D:/nonexistent/audio.wav", "provider": "funasr"},
    )
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is False


@pytest.mark.asyncio
async def test_transcribe_audio_file_funasr_disabled(mcp_app):
    """When FunASR is not configured, tool returns recovery hint."""
    result = await mcp_app.call_tool(
        "transcribe_audio_file",
        {"file_path": "C:/tmp/test.wav"},
    )
    data = _tool_result_data(result)
    if not data.get("success"):
        assert "FunASR" in data.get("error", "") or "recovery" in data


@pytest.mark.asyncio
async def test_parse_transcript_result():
    from speech_mcp.providers.funasr import _format_transcript_lines, _parse_transcript_result

    raw = [
        {
            "sentence_info": [
                {"spk": 0, "start": 120, "end": 3450, "text": "Hello", "emotion": "happy"},
                {"spk": 1, "start": 3500, "end": 6000, "text": "World"},
            ]
        }
    ]
    parsed = _parse_transcript_result(raw)
    assert parsed["text"] == "Hello World"
    assert len(parsed["segments"]) == 2
    assert parsed["segments"][0]["start_s"] == 0.12
    formatted = _format_transcript_lines(parsed)
    assert "Speaker 0" in formatted
    assert "(happy)" in formatted


@pytest.mark.asyncio
async def test_funasr_provider_file_transcription(tmp_path):
    from speech_mcp.providers.funasr import FunASRConfig, FunASRProvider

    audio_file = tmp_path / "test.wav"
    audio_file.write_bytes(b"RIFF" + b"\x00" * 40)

    provider = FunASRProvider(FunASRConfig(model="test-model", device="cpu"))

    mock_result = [{"sentence_info": [{"spk": 0, "start": 0, "end": 1000, "text": "test"}]}]
    with patch.object(provider, "_generate_sync", return_value=mock_result):
        result = await provider.transcribe_file(str(audio_file))

    assert result["success"] is True
    assert result["text"] == "test"
    assert len(result["segments"]) == 1


@pytest.mark.asyncio
async def test_funasr_provider_chunk_transcription():
    from speech_mcp.providers.funasr import FunASRConfig, FunASRProvider

    provider = FunASRProvider(FunASRConfig())
    provider.transcribe_file = AsyncMock(
        return_value={"success": True, "text": "chunk ok", "segments": [], "formatted": "chunk ok"}
    )

    b64 = base64.b64encode(b"fake-audio").decode("ascii")
    result = await provider.transcribe_chunk(b64)
    assert result["success"] is True
    assert result["text"] == "chunk ok"
