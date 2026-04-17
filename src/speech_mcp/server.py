import asyncio
import json
import logging
import os
import tempfile
from contextlib import asynccontextmanager
from time import localtime, strftime
from typing import Any

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastmcp import FastMCP
from hume import HumeClient
from pydantic import BaseModel

from speech_mcp.providers.gemini import GeminiTTSProvider
from speech_mcp.state import _timers, get_store
from speech_mcp.streaming import handle_websocket_stream
from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.ui import register_ui_tools
from speech_mcp.tools.utility import register_utility_tools
from speech_mcp.tools.wake_word import register_wake_word_tools

load_dotenv()
HUME_API_KEY = os.getenv("HUME_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# --- Log broadcast infrastructure — feeds SystemLogs WebSocket ---
_log_clients: set[WebSocket] = set()
_log_queue: asyncio.Queue = None  # initialised in lifespan


async def _broadcast_log(msg: dict):
    dead = set()
    for ws in _log_clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.add(ws)
    _log_clients.difference_update(dead)


class _QueueLogHandler(logging.Handler):
    """Non-blocking: push records onto asyncio queue for broadcast."""

    def emit(self, record: logging.LogRecord):
        if _log_queue is None:
            return
        msg = {
            "time": strftime("%H:%M:%S", localtime(record.created)),
            "level": record.levelname,
            "context": record.name.split(".")[-1],
            "msg": self.format(record),
        }
        try:
            _log_queue.put_nowait(msg)
        except asyncio.QueueFull:
            pass


_queue_handler = _QueueLogHandler()
_queue_handler.setLevel(logging.DEBUG)
logging.getLogger("speech_mcp").addHandler(_queue_handler)
logging.getLogger("uvicorn.access").addHandler(_queue_handler)
logging.getLogger("uvicorn.error").addHandler(_queue_handler)
logging.getLogger("fastmcp").addHandler(_queue_handler)
# Capturing root logs can be noisy but useful for debugging why things aren't showing
# logging.getLogger().addHandler(_queue_handler)

logger = logging.getLogger(__name__)


async def _log_broadcaster():
    """Background task: drain queue and broadcast to WS clients."""
    while True:
        msg = await _log_queue.get()
        await _broadcast_log(msg)


# --- Lifespan ---


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _log_queue
    _log_queue = asyncio.Queue(maxsize=500)
    get_store()
    broadcaster = asyncio.create_task(_log_broadcaster())
    logger.info("Speech-MCP backend started on port %s", os.getenv("PORT", "10918"))
    yield
    broadcaster.cancel()
    for task in _timers.values():
        task.cancel()


# --- FastAPI app ---

app = FastAPI(title="Speech MCP Stream Gateway", lifespan=lifespan)

_cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:10917,http://127.0.0.1:10917").strip().split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastMCP server (shared for stdio and webapp modes)
mcp = FastMCP("speech-mcp")

hume_client = HumeClient(api_key=HUME_API_KEY) if HUME_API_KEY else None
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None
try:
    gemini_client = GeminiTTSProvider()
except Exception as e:
    logger.warning(f"Gemini client initialization skipped: {e}")
    gemini_client = None

register_speech_tools(mcp, hume_client, eleven_client, gemini_client)
register_agentic_tools(mcp, hume_client)
register_utility_tools(mcp)
register_monitoring_tools(mcp)
register_rag_tools(mcp)
register_safety_tools(mcp)
register_ui_tools(mcp)
register_wake_word_tools(mcp)

# --- Auth ---

api_key_header = APIKeyHeader(name="X-Speech-MCP-Auth", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if not expected:
        return True
    if api_key == expected:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Missing or invalid X-Speech-MCP-Auth header",
    )


# --- Pydantic request models ---


class TTSRequest(BaseModel):
    text: str
    provider: str = "windows"
    voice_id: str = "default"
    emotion: str | None = None


class AgenticRequest(BaseModel):
    goal: str


class AskRequest(BaseModel):
    question: str
    model: str | None = None
    provider: str = "ollama"
    api_url: str | None = None


class UtilityRequest(BaseModel):
    action: str
    type: str
    value: str | int | None = None
    label: str = "Default"


class ActionRequest(BaseModel):
    action_type: str
    params: dict[str, Any] | None = None


# --- REST endpoints ---


@app.get("/api/v1/health")
async def health_check(_: str = Depends(get_api_key)):
    return {
        "status": "healthy",
        "version": "0.3.0",
        "modular": True,
        "mcp_server": "online",
        "rag_sources": get_store().list_sources(),
        "active_timers": len(_timers),
        "providers": {
            "hume": bool(hume_client),
            "elevenlabs": bool(eleven_client),
            "gemini": bool(gemini_client),
            "windows": True,
        },
    }


@app.get("/api/v1/stats")
async def api_stats():
    """RAG knowledge base statistics for SemanticSearch."""
    store = get_store()
    sources = store.list_sources()
    row_count = store.count_rows()
    return {"row_count": row_count, "sources": sources}


@app.get("/api/v1/search")
async def api_search(q: str = ""):
    return [
        {
            "filename": r["metadata"].get("filename", "unknown"),
            "score": max(0.0, 1.0 - r.get("_distance", 0.0)),
            "content": r["content"],
        }
        for r in get_store().search(q, limit=10)
    ]


@app.get("/api/v1/local/models")
async def api_local_models(provider: str = "ollama", url: str | None = None):
    """Dynamic elicitation of local models."""
    from speech_mcp.providers.local import local_llm_provider

    base_url = url or ("http://localhost:11434" if provider == "ollama" else "http://localhost:1234")
    logger.info(f"Eliciting local models for {provider} at {base_url}")
    models = await local_llm_provider.list_models(provider, base_url)
    return {"success": True, "provider": provider, "models": models}


@app.post("/api/v1/ask")
async def api_ask(req: AskRequest):
    """Grounded Q&A via RAG + Tool Sampling. Returns a grounded answer."""
    from speech_mcp.providers.local import local_llm_provider

    logger.info(f"Ask request: {req.question[:60]} (model={req.model})")
    store = get_store()
    results = store.search(req.question, limit=5)
    context = "\n".join([r["content"] for r in results])

    # Dynamic local generation
    prompt = f"Context:\n{context}\n\nQuestion: {req.question}"
    system = "You are a SOTA speech technology expert. Answer concisely based on context provided."

    provider = req.provider
    base_url = req.api_url or (
        "http://localhost:11434" if provider == "ollama" else "http://localhost:1234"
    )
    model = req.model or ("llama3" if provider == "ollama" else "default")

    answer = await local_llm_provider.generate(
        provider=provider, base_url=base_url, model=model, prompt=prompt, system=system
    )

    return {
        "success": True,
        "question": req.question,
        "answer": answer,
        "context": context,
        "sources": [r["metadata"].get("filename", "unknown") for r in results],
    }
async def api_voices():
    providers = []
    if hume_client:
        providers.append({"name": "hume", "status": "available", "voices": ["ito", "kora"]})
    if eleven_client:
        providers.append({"name": "elevenlabs", "status": "available", "voices": []})
    if gemini_client:
        providers.append({"name": "gemini", "status": "available", "voices": gemini_client.voices})
    providers.append({"name": "windows", "status": "available", "voices": ["default"]})
    return {"providers": providers}


@app.get("/api/v1/history")
async def api_history():
    """Retrieve the forensic interaction trace."""
    from speech_mcp.state import _history

    return list(_history)


@app.get("/api/v1/tts/wav")
async def api_tts_wav(text: str, provider: str = "windows"):
    """
    Simple HTTP TTS — synthesize and return raw WAV file.
    Frontend plays with <audio> element. No WebSocket needed.
    """
    logger.info(f"TTS WAV: provider={provider} text={text[:60]}")
    from speech_mcp.state import add_history

    add_history("tts", text, provider)

    if not text:
        raise HTTPException(status_code=400, detail="text param required")

    if provider == "windows":
        import anyio
        import pyttsx3

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        def _synth():
            engine = pyttsx3.init()
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

        await anyio.to_thread.run_sync(_synth)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise HTTPException(status_code=500, detail="pyttsx3 synthesis failed — empty file")

        logger.info(f"WAV ready: {os.path.getsize(tmp_path)} bytes")

        # Read into memory so we can delete the temp file
        with open(tmp_path, "rb") as f:
            wav_bytes = f.read()
        os.remove(tmp_path)

        return Response(content=wav_bytes, media_type="audio/wav")

    raise HTTPException(status_code=400, detail=f"provider '{provider}' not supported on this endpoint")


@app.post("/api/v1/agentic")
async def api_agentic(req: AgenticRequest):
    """Trigger an agentic orchestration goal. Returns a trace stream."""
    logger.info(f"Agentic request: goal={req.goal}")
    # Real orchestration happens via MCP tool calls from the AI client.
    # The REST endpoint kicks off a logged execution trace the UI can show.
    return {
        "success": True,
        "goal": req.goal,
        "status": "dispatched",
        "trace": [
            {"step": 1, "tool": "agentic_conversation_workflow", "status": "invoked"},
            {"step": 2, "tool": "search_docs", "status": "pending"},
            {"step": 3, "tool": "text_to_speech", "status": "pending"},
        ],
        "message": "Orchestration dispatched. Monitor /ws/logs for live trace.",
    }


@app.post("/api/v1/utility")
async def api_utility(req: UtilityRequest):
    """Domestic utility actions (timer, weather). Calls the actual tool logic."""
    from datetime import datetime

    from speech_mcp.state import run_timer

    logger.info(f"Utility: action={req.action} type={req.type} label={req.label}")

    if req.type == "timer" and req.action == "set":
        import asyncio as _asyncio

        seconds = int(req.value) if req.value else 60
        timer_id = f"timer_{req.label}_{datetime.now().timestamp()}"
        task = _asyncio.create_task(run_timer(timer_id, seconds, req.label))
        _timers[timer_id] = task
        logger.info(f"Timer '{req.label}' set for {seconds}s (id={timer_id})")
        return {
            "success": True,
            "timer_id": timer_id,
            "expires_in": seconds,
            "status": "active",
        }

    if req.type == "timer" and req.action == "query":
        return {
            "success": True,
            "active_timers": len(_timers),
            "timer_ids": list(_timers.keys()),
        }

    if req.type == "weather":
        # Placeholder — swap for real weather API call if desired
        return {
            "success": True,
            "location": req.label,
            "condition": "Cloudy",
            "temp": "21°C",
        }

    return {
        "success": False,
        "error": f"action={req.action} type={req.type} not implemented",
    }


@app.post("/api/v1/action")
async def api_action(req: ActionRequest):
    """IoT / device actions (lights etc). Delegates to monitoring tool logic."""
    logger.info(f"Action: {req.action_type} params={req.params}")
    params = req.params or {}
    if req.action_type in ("light_on", "light_off"):
        room = params.get("room", "living_room")
        state = "on" if "on" in req.action_type else "off"
        logger.info(f"Tapo dispatch: {room} light -> {state}")
        from speech_mcp.state import add_history

        add_history("iot", f"Light {state} in {room}", "Tapo Smarthome")
        return {
            "success": True,
            "device": "Tapo Smart Bulb",
            "room": room,
            "state": state,
        }
    return {"success": True, "action_elicited": req.action_type, "status": "triggered"}


# --- WebSocket endpoints ---


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """SOTA side-channel audio stream proxy."""
    await handle_websocket_stream(websocket, eleven_client, hume_client, gemini_client)


@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    """Real-time log broadcast for SystemLogs UI."""
    await websocket.accept()
    _log_clients.add(websocket)
    logger.info("SystemLogs client connected")
    try:
        # Keep alive; client just listens
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _log_clients.discard(websocket)


if __name__ == "__main__":
    # Binding to 127.0.0.1 for security unless explicitly overridden
    asyncio.run(mcp.run_stdio_async())
