"""Unit tests for the Muse Voice Transcribe provider and STT tool wiring."""

import json

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
async def test_transcribe_audio_file_muse_not_configured(mcp_app):
    """MUSE_ENABLED/MUSE_API_KEY are unset in the test env, so muse_provider is None."""
    result = await mcp_app.call_tool(
        "transcribe_audio_file",
        {"file_path": "C:/tmp/test.wav", "provider": "muse"},
    )
    data = _tool_result_data(result)
    assert data.get("success") is False
    assert "Muse" in data.get("error", "")


@pytest.mark.asyncio
async def test_muse_transcribe_stream_not_configured(mcp_app):
    result = await mcp_app.call_tool("muse_transcribe_stream", {"action": "start"})
    data = _tool_result_data(result)
    assert data.get("success") is False
    assert data.get("error_type") == "not_enabled"


def test_turns_to_segments():
    from speech_mcp.providers.muse import _turns_to_segments

    turns = [
        {"speaker": "A", "startMs": 120, "endMs": 3450, "transcript": "Hello"},
        {"speaker": "B", "startMs": 3500, "endMs": 6000, "transcript": "World"},
    ]
    segments = _turns_to_segments(turns)
    assert len(segments) == 2
    assert segments[0] == {"speaker": "A", "start_s": 0.12, "end_s": 3.45, "text": "Hello"}
    assert segments[1]["speaker"] == "B"


def test_format_transcript_lines():
    from speech_mcp.providers.muse import _format_transcript_lines

    segments = [{"speaker": "A", "start_s": 0.0, "end_s": 1.5, "text": "hi there"}]
    formatted = _format_transcript_lines(segments)
    assert "[00.00s -> 01.50s] [Speaker A]: hi there" == formatted


def test_muse_config_requires_api_key():
    from speech_mcp.providers.muse import MuseConfig, MuseVoiceProvider

    with pytest.raises(ValueError):
        MuseVoiceProvider(MuseConfig(api_key=""))
