# Speech-MCP logging

## Backend

- **Python logging**: Standard library `logging`. Logger names: `speech_mcp`, `uvicorn.access`, `uvicorn.error`, `fastmcp`.
- **Level**: Set via `--log-level` to uvicorn (e.g. `info`, `debug`). No separate log file by default; output is stdout.
- **In-memory broadcast**: A queue handler attaches to the above loggers and pushes each record to an asyncio queue. The `/ws/logs` WebSocket drains that queue and sends JSON to connected clients (e.g. the System Logs page).

## Log record shape (WebSocket)

Each message is JSON:

- `time`: Time string (e.g. `HH:MM:SS`).
- `level`: `INFO`, `DEBUG`, `WARN`, `ERROR`, etc.
- `context`: Short name (e.g. last segment of logger name).
- `msg`: Formatted message.

## Log viewer (webapp)

- **Page**: System Logs in the sidebar.
- **Features**: Level filter, text search over time/level/context/msg, export to `.txt`, clear buffer. Shows last N entries (in-memory only).
- **Connection**: WebSocket to `{BACKEND}/ws/logs`. If backend is down, the UI shows offline.

## Env / config

- No dedicated log config file. Uvicorn log level and CORS/origins are the main knobs; see `docs/configuration.md`.
