import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from contextlib import asynccontextmanager
from time import localtime, strftime
from typing import TYPE_CHECKING, Any

import anyio
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastmcp import FastMCP, Context
import uuid
from hume import HumeClient
from pydantic import BaseModel

from speech_mcp.providers.gemini import GeminiProvider
from speech_mcp.state import _timers, get_store
from speech_mcp.streaming import handle_websocket_stream
from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.demos import DemoName, register_demo_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.ui import register_ui_tools
from speech_mcp.tools.utility import register_utility_tools
from speech_mcp.tools.wake_word import register_wake_word_tools

if TYPE_CHECKING:
    pass

load_dotenv()
HUME_API_KEY = os.getenv("HUME_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# --- Log broadcast infrastructure ---
_log_clients: set[WebSocket] = set()
_log_queue: asyncio.Queue = None

async def _broadcast_log(msg: dict):
    dead = set()
    for ws in _log_clients:
        try:
            await ws.send_text(json.dumps(msg))
        except Exception:
            dead.add(ws)
    _log_clients.difference_update(dead)

class _QueueLogHandler(logging.Handler):
    def emit(self, record: logging.LogRecord):
        if _log_queue is None:
            return
        msg = {
            "id": str(uuid.uuid4()),
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

logger = logging.getLogger(__name__)

async def _log_broadcaster():
    while True:
        msg = await _log_queue.get()
        await _broadcast_log(msg)

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

app = FastAPI(title="Speech MCP Stream Gateway", lifespan=lifespan)

# Modern CORS for local fleet dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10917", "http://127.0.0.1:10917",
        "http://localhost:10761", "http://127.0.0.1:10761"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP("speech-mcp")

hume_client = HumeClient(api_key=HUME_API_KEY) if HUME_API_KEY else None
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None
try:
    gemini_client = GeminiProvider()
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
register_demo_tools(mcp)
register_wake_word_tools(mcp)

api_key_header = APIKeyHeader(name="X-Speech-MCP-Auth", auto_error=False)

async def get_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if not expected:
        return True
    if api_key == expected:
        return api_key
    raise HTTPException(status_code=401, detail="Unauthorized")

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

class DemoRequest(BaseModel):
    demo: DemoName

@app.get("/api/v1/health")
async def health_check(_: str = Depends(get_api_key)):
    from speech_mcp.tools.wake_word import _listener_thread
    wake_active = _listener_thread is not None and _listener_thread.is_alive()

    return {
        "status": "healthy",
        "version": "0.3.0",
        "mcp_server": "online",
        "rag_sources": get_store().list_sources(),
        "active_timers": len(_timers),
        "wake_word_active": wake_active,
        "providers": {
            "hume": bool(hume_client),
            "elevenlabs": bool(eleven_client),
            "gemini": bool(gemini_client),
            "windows": True,
        },
    }


class WakeWordRequest(BaseModel):
    action: str
    keyword: str = "computer"
    sensitivity: float = 0.5


@app.post("/api/v1/wake_word")
async def api_wake_word(req: WakeWordRequest, ctx: Context = Depends(lambda: Context())):
    """Bridge to the configure_local_wake_word tool."""
    # We redefine/call the logic here for the API
    from speech_mcp.tools.wake_word import configure_local_wake_word
    return await configure_local_wake_word(
        ctx=ctx,
        keyword=req.keyword,
        sensitivity=req.sensitivity,
        action=req.action
    )

@app.get("/api/v1/stats")
async def api_stats():
    store = get_store()
    return {"row_count": store.count_rows(), "sources": store.list_sources()}

@app.get("/api/v1/search")
async def api_search(q: str = ""):
    return [
        {
            "id": r.get("id", f"chk_{i}"),
            "filename": r["metadata"].get("filename", "unknown"),
            "score": max(0.0, 1.0 - r.get("_distance", 0.0)),
            "content": r["content"],
        }
        for i, r in enumerate(get_store().search(q, limit=10))
    ]

@app.get("/api/v1/local/models")
async def api_local_models(provider: str = "ollama", url: str | None = None):
    from speech_mcp.providers.local import local_llm_provider
    base_url = url or ("http://localhost:11434" if provider == "ollama" else "http://localhost:1234")
    models = await local_llm_provider.list_models(provider, base_url)
    return {"success": True, "provider": provider, "models": models}

@app.post("/api/v1/ask")
async def api_ask(req: AskRequest):
    from speech_mcp.providers.local import local_llm_provider
    store = get_store()
    results = store.search(req.question, limit=5)
    context = "\n".join([r["content"] for r in results])
    prompt = f"Context:\n{context}\n\nQuestion: {req.question}"
    system = "You are a SOTA speech technology expert. Answer concisely based on context provided."
    provider = req.provider
    base_url = req.api_url or ("http://localhost:11434" if provider == "ollama" else "http://localhost:1234")
    model = req.model or ("llama3" if provider == "ollama" else "default")
    answer = await local_llm_provider.generate(provider=provider, base_url=base_url, model=model, prompt=prompt, system=system)
    return {"success": True, "answer": answer, "sources": [r["metadata"].get("filename", "unknown") for r in results]}

@app.get("/api/v1/voices")
async def api_voices():
    providers = []
    if hume_client: providers.append({"name": "hume", "status": "available", "voices": ["ito", "kora"]})
    if eleven_client: providers.append({"name": "elevenlabs", "status": "available", "voices": []})
    if gemini_client: providers.append({"name": "gemini", "status": "available", "voices": gemini_client.voices})
    providers.append({"name": "windows", "status": "available", "voices": ["default"]})
    return {"providers": providers}

@app.get("/api/v1/history")
async def api_history():
    from speech_mcp.state import _history
    return list(_history)

@app.get("/api/v1/tts/wav")
async def api_tts_wav(text: str, provider: str = "windows"):
    from speech_mcp.state import add_history
    add_history("tts", text, provider)
    if not text: raise HTTPException(status_code=400, detail="text param required")
    if provider == "windows":
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        def _synth():
            import pyttsx3
            engine = pyttsx3.init()
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()
        await anyio.to_thread.run_sync(_synth)
        with open(tmp_path, "rb") as f: wav_bytes = f.read()
        os.remove(tmp_path)
        return Response(content=wav_bytes, media_type="audio/wav")
    raise HTTPException(status_code=400, detail=f"provider '{provider}' not supported")

@app.post("/api/v1/transcribe")
async def api_transcribe(request: Request, _: str = Depends(get_api_key)):
    if not gemini_client: raise HTTPException(status_code=503, detail="Gemini STT not configured")
    try:
        file = await request.body()
        transcript = await anyio.to_thread.run_sync(lambda: gemini_client.transcribe(file, mime_type="audio/wav"))
        return {"success": True, "transcript": transcript}
    except Exception as e:
        logger.exception("API transcription failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/demos/run")
async def api_run_demo(req: DemoRequest):
    from speech_mcp.tools.demos import DEMO_MAP
    script_filename = DEMO_MAP.get(req.demo)
    if not script_filename: return {"success": False, "error": f"Demo '{req.demo}' not found."}
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "demos")
    script_path = os.path.normpath(os.path.join(script_dir, script_filename))
    try:
        uv_path = shutil.which("uv") or "uv"
        result = await anyio.to_thread.run_sync(lambda: subprocess.run([uv_path, "run", "python", script_path], capture_output=True, text=True, check=False))
        return {"success": result.returncode == 0, "demo": req.demo, "output": (result.stdout + result.stderr).strip()}
    except Exception as e: return {"success": False, "error": str(e)}

@app.post("/api/v1/agentic")
async def api_agentic(req: AgenticRequest):
    return {"success": True, "goal": req.goal, "status": "dispatched", "trace": ["Industrial dispatcher trace active."]}

@app.post("/api/v1/utility")
async def api_utility(req: UtilityRequest):
    from datetime import datetime

    from speech_mcp.state import run_timer
    if req.type == "timer" and req.action == "set":
        seconds = int(req.value) if req.value else 60
        timer_id = f"timer_{req.label}_{datetime.now().timestamp()}"
        task = asyncio.create_task(run_timer(timer_id, seconds, req.label))
        _timers[timer_id] = task
        return {"success": True, "timer_id": timer_id, "expires_in": seconds}
    if req.type == "timer" and req.action == "query":
        return {"success": True, "active_timers": len(_timers)}
    return {"success": False, "error": "not implemented"}

@app.post("/api/v1/action")
async def api_action(req: ActionRequest):
    params = req.params or {}
    if req.action_type in ("light_on", "light_off"):
        room = params.get("room", "living_room")
        state = "on" if "on" in req.action_type else "off"
        from speech_mcp.state import add_history
        add_history("iot", f"Light {state} in {room}", "Tapo Smarthome")
        return {"success": True, "device": "Tapo Smart Bulb", "room": room, "state": state}
    return {"success": True, "status": "triggered"}

@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    await handle_websocket_stream(websocket, eleven_client, hume_client, gemini_client)

@app.websocket("/ws/stt")
async def websocket_stt(websocket: WebSocket):
    from speech_mcp.streaming import _handle_stt_stream
    await websocket.accept()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        await websocket.close(code=1008, reason="GOOGLE_API_KEY not configured")
        return
    await _handle_stt_stream(websocket, api_key)

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    _log_clients.add(websocket)
    try:
        while True: await websocket.receive_text()
    except WebSocketDisconnect: pass
    finally: _log_clients.discard(websocket)

def main():
    asyncio.run(mcp.run_stdio_async())

if __name__ == "__main__":
    main()
