import pytest
from unittest.mock import AsyncMock, Mock, patch


def _tool_result_data(result):
    """Extract dict from FastMCP ToolResult (structured_content or parsed content)."""
    if hasattr(result, "structured_content") and result.structured_content is not None:
        return result.structured_content
    if hasattr(result, "content") and result.content:
        import json
        text = result.content[0].text if hasattr(result.content[0], "text") else str(result.content[0])
        try:
            return json.loads(text)
        except Exception:
            return {"raw": text}
    return result


@pytest.mark.asyncio
async def test_search_docs_tool(mcp_app):
    """Test search_docs returns success and data list."""
    result = await mcp_app.call_tool("search_docs", {"query": "AI"})
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "data" in data
    assert isinstance(data["data"], list)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session (Context injection); covered by test_server.test_utility_post_timer_set")
async def test_manage_domestic_utility_timer_set(mcp_app):
    """Test timer set returns dict with timer_id and expires_in."""
    result = await mcp_app.call_tool(
        "manage_domestic_utility",
        {"action": "set", "type": "timer", "value": 10, "label": "TestTimer"},
    )
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "timer_id" in data
    assert data.get("expires_in") == 10
    assert "TestTimer" in data.get("timer_id", "")


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session; covered by test_server.test_utility_post_timer_query")
async def test_manage_domestic_utility_timer_query(mcp_app):
    """Test timer query returns active_timers count."""
    result = await mcp_app.call_tool(
        "manage_domestic_utility",
        {"action": "query", "type": "timer"},
    )
    data = _tool_result_data(result)
    assert data.get("success") is True
    assert "active_timers" in data
    assert isinstance(data["active_timers"], int)


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session; TTS behavior covered by test_server.test_tts_wav_* and API")
async def test_text_to_speech_windows(mcp_app):
    """Test TTS tool with windows provider (no API key required)."""
    result = await mcp_app.call_tool(
        "text_to_speech", {"text": "Hello world", "provider": "windows"}
    )
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "stream_url" in data
    assert "ws" in data["stream_url"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session; error-path covered by API tests")
async def test_text_to_speech_hume_missing_key(mcp_app):
    """Test TTS with hume provider when key missing returns error."""
    result = await mcp_app.call_tool(
        "text_to_speech", {"text": "Hi", "provider": "hume"}
    )
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is False
    assert "error" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session; agentic flow covered by test_server.test_agentic_post")
async def test_start_evi_session_returns_proxy(mcp_app):
    """Test start_evi_session returns local_proxy URL."""
    result = await mcp_app.call_tool("start_evi_session", {})
    data = _tool_result_data(result)
    assert isinstance(data, dict)
    assert data.get("success") is True
    assert "local_proxy" in data
    assert "ws" in data["local_proxy"]


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires MCP session (Context/sample); RAG search covered by test_server.test_search_endpoint")
async def test_ask_docs_sampling(mcp_app, mock_ctx):
    """Test ask_docs with mocked store returns sampled or grounded answer."""
    with patch("speech_mcp.tools.rag.get_store") as mock_get_store:
        mock_store = Mock()
        mock_store.search.return_value = [
            {"content": "Speech AI is cool", "metadata": {"filename": "doc1.md"}}
        ]
        mock_get_store.return_value = mock_store

        result = await mcp_app.call_tool("ask_docs", {"question": "What is speech AI?"})
        data = _tool_result_data(result)
        out = str(data) if not isinstance(data, dict) else str(data.get("raw", data))
        assert "Sampled response" in out or "Speech AI" in out or (isinstance(data, dict) and data.get("success") is True)
