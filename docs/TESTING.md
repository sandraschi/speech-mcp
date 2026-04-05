# Speech-MCP testing

## Scope

- **Backend**: pytest in `tests/` against the FastAPI app and MCP tools.
- **No frontend E2E** in-repo: the webapp is manual or run via external E2E if needed.

## Run tests

From repo root (use project env so `speech_mcp` is importable):

```powershell
uv sync --extra dev
uv run python -m pytest tests/ -v
```

With coverage (if configured):

```powershell
uv run python -m pytest tests/ -v --cov=speech_mcp --cov-report=term-missing
```

## Layout

| Path | Purpose |
|------|--------|
| `tests/conftest.py` | Fixtures: `mock_ctx`, `mcp_app`, `mock_hume`, `mock_elevenlabs`, `mock_env` (autouse: sets `HUME_API_KEY`, `ELEVENLABS_API_KEY`, `SPEECH_MCP_AUTH_TOKEN` for tests). |
| `tests/test_server.py` | FastAPI: server init, health (401 without auth, 200 with header), `/api/v1/voices`, `/api/v1/stats`, `/api/v1/history`, `/api/v1/search`, POST `/api/v1/agentic`, POST `/api/v1/utility` (timer set/query), GET `/api/v1/tts/wav` (400 when text empty). |
| `tests/test_tools.py` | MCP tools: `search_docs` (in-process, no session). Timer, TTS, EVI, and `ask_docs` tests are **skipped**: they require an MCP session (FastMCP Context injection); the same behavior is covered by API tests in `test_server.py`. |

## Auth in tests

When `SPEECH_MCP_AUTH_TOKEN` is set (as in `conftest.mock_env`), only `/api/v1/health` requires the header. Other endpoints (voices, stats, history, search, utility, agentic) do not. Use:

```python
AUTH_HEADERS = {"X-Speech-MCP-Auth": "test_token"}
response = client.get("/api/v1/health", headers=AUTH_HEADERS)
```

## Tool testing

- **In-process** (no MCP transport): Only `search_docs` is run via `mcp_app.call_tool(...)`; it does not require a live MCP session. Return shape is read via `_tool_result_data(result)` (FastMCP `ToolResult.structured_content` or parsed content).
- **Session-dependent tools**: `manage_domestic_utility`, `text_to_speech`, `start_evi_session`, and `ask_docs` need an established MCP session (Context injection). Those tests are skipped in unit runs; equivalent behavior is covered by `test_server.py` (utility POST, TTS endpoint, agentic POST, search endpoint).

## Extending

- Add API tests in `tests/test_server.py` for new endpoints.
- Add tool tests in `tests/test_tools.py`; mock external clients and stores via `conftest` or `unittest.mock.patch`.
- For RAG/streaming, consider integration tests that call a real LanceDB path or a test double.
- See [YAHBOOM_RASPBOT_VOICE.md](YAHBOOM_RASPBOT_VOICE.md) for notes on the Yahboom Raspbot v2 TTS/STT module and bridging with Speech-MCP.
