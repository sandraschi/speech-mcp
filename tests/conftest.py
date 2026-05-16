from unittest.mock import AsyncMock, Mock

import pytest


@pytest.fixture
def mock_ctx():
    """Mock MCP Context."""
    ctx = Mock()
    ctx.info = Mock()
    ctx.error = Mock()
    ctx.warning = Mock()
    ctx.sample = AsyncMock(return_value="Sampled response")
    return ctx


@pytest.fixture
def mcp_app():
    """Speech-MCP Instance for testing."""
    from speech_mcp.server import mcp

    return mcp


@pytest.fixture
def mock_hume():
    """Mock Hume AI Client."""
    client = Mock()
    client.tts = Mock()
    client.tts.synthesize = AsyncMock(return_value=b"audio_data")
    return client


@pytest.fixture
def mock_elevenlabs():
    """Mock ElevenLabs Client."""
    client = Mock()
    client.generate = Mock(return_value=iter([b"audio_chunk"]))
    return client


@pytest.fixture
def mock_hardware():
    """Mock hardware probe data."""
    return {
        "monitors": [
            {"left": 0, "top": 0, "right": 1920, "bottom": 1080, "width": 1920, "height": 1080},
            {"left": 1920, "top": 0, "right": 3840, "bottom": 1080, "width": 1920, "height": 1080}
        ],
        "microphones": [
            {"index": 0, "name": "Mock Mic", "channels": 1, "rate": 44100},
            {"index": 1, "name": "c922 Pro Stream Webcam", "channels": 2, "rate": 32000}
        ],
        "cameras": ["c922 Pro Stream Webcam"]
    }


def pytest_addoption(parser):
    """Add --live flag to pytest."""
    parser.addoption(
        "--live", action="store_true", default=False, help="Run live integration tests with real keys"
    )


@pytest.fixture(autouse=True)
def mock_env(monkeypatch, request):
    """
    Ensure environment variables are set for testing.
    If --live is NOT passed, we use mock keys to ensure safety in CI.
    """
    if not request.config.getoption("--live"):
        monkeypatch.setenv("HUME_API_KEY", "test_hume_key")
        monkeypatch.setenv("ELEVENLABS_API_KEY", "test_eleven_key")
        monkeypatch.setenv("GOOGLE_API_KEY", "test_google_key")
        monkeypatch.setenv("GEMINI_API_KEY", "test_google_key")
        monkeypatch.setenv("OPENWAKEWORD_MODEL_PATH", "")
        monkeypatch.setenv("SPEECH_MCP_AUTH_TOKEN", "test_token")
