# GitHub Copilot Instructions — speech-mcp

- Python: `uv run ruff check src/ --fix` before commit; line length 120.
- Type hints: `Annotated[T, Field(description="...")]` — no `Args:` blocks.
- Tools return `{"success": bool, ...}` dicts; list/status tools use Prefab UI (`@mcp.tool(app=True)`).
- Never call `os.getenv()` outside `server.py`; never block the event loop.
- Frontend: React + Vite + Tailwind (dark theme only), Biome for lint/format.
- Tests: `uv run pytest tests/ -m "not live"`.

## Session Context (Speech MCP)

You have access to the fleet voice gateway: TTS (windows/gemini/hume/elevenlabs/gemma),
local STT (FunASR), offline wake word, RAG over speech docs, and a Voice Command Bus
into fleet-agent.

**Before starting work:**
1. Check provider availability: fleet_health_overview()
2. Find speech docs: search_docs(query="FunASR or wake word")

**At end of work, save insights:**
- Ingest useful speech findings into the RAG knowledge base
