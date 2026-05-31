import os
import sys
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

# Ensure root is in path for scripts.utils imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from speech_mcp.server import app, mcp

client = TestClient(app)
AUTH_HEADERS = {"X-Speech-MCP-Auth": "test_token"}


@pytest.mark.asyncio
async def test_server_initialization():
    """Verify that FastMCP and FastAPI are correctly initialized."""
    assert mcp.name == "speech-mcp"
    tools = await mcp.list_tools()
    assert len(tools) >= 5


def test_health_check_success():
    """Verify that health check succeeds with valid API key."""
    response = client.get("/api/v1/health", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "providers" in data
    assert "active_timers" in data
    assert "mcp_server" in data


def test_voices_endpoint():
    """Verify that the voices transparency endpoint returns data."""
    response = client.get("/api/v1/voices")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert any(p["name"] == "windows" for p in data["providers"])


def test_stats_endpoint():
    """Verify RAG stats returns row_count and sources."""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "row_count" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)


def test_history_endpoint():
    """Verify history returns a list (forensic trace)."""
    response = client.get("/api/v1/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_search_endpoint():
    """Verify search returns list of results."""
    response = client.get("/api/v1/search", params={"q": "test"})
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_agentic_post():
    """Verify agentic endpoint returns dispatched trace."""
    response = client.post(
        "/api/v1/agentic",
        json={"goal": "test goal"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert data.get("goal") == "test goal"
    assert "trace" in data
    assert isinstance(data["trace"], list)


def test_utility_post_timer_set():
    """Verify utility timer set returns timer_id and expires_in."""
    response = client.post(
        "/api/v1/utility",
        json={"action": "set", "type": "timer", "value": 30, "label": "Test"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert "timer_id" in data
    assert data.get("expires_in") == 30


def test_utility_post_timer_query():
    """Verify utility timer query returns active_timers."""
    response = client.post(
        "/api/v1/utility",
        json={"action": "query", "type": "timer"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data.get("success") is True
    assert "active_timers" in data


def test_tts_wav_requires_text():
    """Verify TTS WAV returns 400 when text is missing."""
    response = client.get("/api/v1/tts/wav", params={"text": "", "provider": "windows"})
    assert response.status_code == 400


def test_hardware_endpoint_mock(mock_hardware):
    """Verify that the hardware transparency endpoint returns mocked probe data."""
    with patch("scripts.utils.hardware_probe.get_monitors", return_value=mock_hardware["monitors"]):
        with patch("scripts.utils.hardware_probe.get_microphones", return_value=mock_hardware["microphones"]):
            with patch("scripts.utils.hardware_probe.get_cameras", return_value=mock_hardware["cameras"]):
                response = client.get("/api/v1/hardware", headers=AUTH_HEADERS)
                assert response.status_code == 200
                data = response.json()
                assert len(data["monitors"]) == 2
                assert "c922 Pro Stream Webcam" in data["cameras"]


def test_health_check_tokens():
    """Verify that health check reports token presence correctly."""
    response = client.get("/api/v1/health", headers=AUTH_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert "tokens" in data
    assert data["tokens"]["google_api_key"] is True  # Mocked in conftest
