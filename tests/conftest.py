import pytest
from unittest.mock import Mock, AsyncMock


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


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Ensure environment variables are set for testing."""
    monkeypatch.setenv("HUME_API_KEY", "test_hume_key")
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test_eleven_key")
    monkeypatch.setenv("SPEECH_MCP_AUTH_TOKEN", "test_token")
