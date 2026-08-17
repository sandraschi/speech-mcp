import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
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
from fastmcp import Context, FastMCP
from fastmcp.server import create_proxy
from hume import HumeClient
from pydantic import BaseModel

from speech_mcp.providers.funasr import FunASRConfig, FunASRProvider
from speech_mcp.providers.gemini import GeminiProvider
from speech_mcp.providers.gemma import gemma_provider
from speech_mcp.state import _timers, get_store
from speech_mcp.streaming import handle_websocket_stream
from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.demos import DemoName, register_demo_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.stt import register_stt_tools
from speech_mcp.tools.ui import register_ui_tools
from speech_mcp.tools.utility import register_utility_tools
from speech_mcp.tools.wake_word import register_wake_word_tools

if TYPE_CHECKING:
    pass

load_dotenv()

# --- SOTA 2026 Startup Hardening ---
# Suppress FastMCP noise for industrial stdio stability
os.environ["FASTMCP_BANNER"] = "0"
os.environ["FASTMCP_UPDATE_CHECK"] = "0"

# Resolve google-genai stdout collision warning (prevents handshake corruption)
# Antigravity/Claude often sets GEMINI_API_KEY globally; we prioritize GOOGLE_API_KEY.
if os.getenv("GOOGLE_API_KEY") and os.getenv("GEMINI_API_KEY"):
    os.environ.pop("GEMINI_API_KEY", None)

HUME_API_KEY = os.getenv("HUME_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# --- FunASR local STT ---
FUNASR_ENABLED = os.getenv("FUNASR_ENABLED", "").lower() in ("1", "true", "yes")
FUNASR_OPENAI_URL = os.getenv("FUNASR_OPENAI_URL", "").strip() or None
FUNASR_MODEL = os.getenv("FUNASR_MODEL", "FunAudioLLM/Fun-ASR-Nano-2512")
FUNASR_DEVICE = os.getenv("FUNASR_DEVICE", "cuda:0")
FUNASR_HUB = os.getenv("FUNASR_HUB", "hf")
FUNASR_VAD_MODEL = os.getenv("FUNASR_VAD_MODEL", "fsmn-vad")
FUNASR_PUNC_MODEL = os.getenv("FUNASR_PUNC_MODEL", "ct-punc")
FUNASR_SPK_MODEL = os.getenv("FUNASR_SPK_MODEL", "cam++")

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


def _probe_rag():
    """Verify LanceDB store is accessible before serving."""
    try:
        store = get_store()
        store.list_sources()
    except Exception as e:
        logger.warning("RAG store probe: %s — degraded mode, search will return empty.", e)


def _probe_funasr(log: logging.Logger):
    """Log FunASR configuration status at startup."""
    if FUNASR_OPENAI_URL:
        log.info("FunASR sidecar mode: %s", FUNASR_OPENAI_URL)
    elif FUNASR_ENABLED:
        log.info("FunASR native mode: model=%s device=%s hub=%s", FUNASR_MODEL, FUNASR_DEVICE, FUNASR_HUB)
    else:
        log.info("FunASR disabled — set FUNASR_ENABLED=true or FUNASR_OPENAI_URL to enable local STT.")


def _probe_api_keys(log: logging.Logger):
    """Warn on missing API keys but allow degraded startup."""
    if not os.getenv("GOOGLE_API_KEY"):
        log.warning("GOOGLE_API_KEY not set — Gemini TTS/STT disabled.")
    if not os.getenv("HUME_API_KEY"):
        log.warning("HUME_API_KEY not set — Hume EVI/Octave disabled.")
    if not os.getenv("ELEVENLABS_API_KEY"):
        log.warning("ELEVENLABS_API_KEY not set — ElevenLabs TTS disabled.")
    if all(k not in os.environ for k in ("GOOGLE_API_KEY", "HUME_API_KEY", "ELEVENLABS_API_KEY")):
        log.info("No TTS API keys configured — only Windows SAPI5 available.")


def _probe_bridges():
    """Verify MCP bridge URLs are reachable."""
    for url in _bridge_proxies:
        try:
            import httpx

            resp = httpx.get(url, timeout=5.0)
            resp.raise_for_status()
            logger.info("Bridge probe OK: %s", url)
        except Exception as e:
            logger.warning("Bridge probe failed for %s: %s — bridge will be unavailable.", url, e)


async def _log_broadcaster():
    while True:
        msg = await _log_queue.get()
        await _broadcast_log(msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _log_queue
    _log_queue = asyncio.Queue(maxsize=500)
    get_store()

    # ── Startup probes ─────────────────────────────────────────────────────
    _probe_rag()
    _probe_api_keys(logger)
    _probe_funasr(logger)
    _probe_bridges()

    broadcaster = asyncio.create_task(_log_broadcaster())
    logger.info("Speech-MCP backend started on port %s", os.getenv("SPEECH_MCP_PORT", "10909"))
    yield
    broadcaster.cancel()
    for task in _timers.values():
        task.cancel()


app = FastAPI(title="Speech MCP Stream Gateway", lifespan=lifespan)

# Modern CORS for local fleet dev + Tauri desktop
_tauri_desktop = os.environ.get("SPEECH_TAURI", "").lower() in ("1", "true", "yes")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10908",
        "http://127.0.0.1:10908",
        "http://goliath:10908",
        "http://localhost:10947",
        "http://127.0.0.1:10947",
        "http://goliath:10947",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://tauri\.localhost(:\d+)?" if _tauri_desktop else None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP("speech-mcp")

# ── MCP Bridge (ProxyProvider) ────────────────────────────────────────────
_bridge_proxies: list[str] = []
bridge_urls = os.getenv("MCP_BRIDGE_URLS", "")
if bridge_urls:
    for url in bridge_urls.split(","):
        url = url.strip()
        if url:
            try:
                mcp.add_provider(create_proxy(url))
                _bridge_proxies.append(url)
                logger.info("MCP bridge added: %s", url)
            except Exception as e:
                logger.warning("MCP bridge failed for %s: %s", url, e)

hume_client = HumeClient(api_key=HUME_API_KEY) if HUME_API_KEY else None
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None
try:
    gemini_client = GeminiProvider()
except Exception as e:
    logger.warning(f"Gemini client initialization skipped: {e}")
    gemini_client = None

gemma_client = gemma_provider

funasr_provider: FunASRProvider | None = None
if FUNASR_ENABLED or FUNASR_OPENAI_URL:
    funasr_provider = FunASRProvider(
        FunASRConfig(
            model=FUNASR_MODEL,
            device=FUNASR_DEVICE,
            hub=FUNASR_HUB,
            vad_model=FUNASR_VAD_MODEL or None,
            punc_model=FUNASR_PUNC_MODEL or None,
            spk_model=FUNASR_SPK_MODEL or None,
            openai_base_url=FUNASR_OPENAI_URL,
        )
    )

register_speech_tools(mcp, hume_client, eleven_client, gemini_client, gemma_client)
register_stt_tools(mcp, funasr_provider, gemini_client, gemma_client)
register_agentic_tools(mcp, hume_client)
register_utility_tools(mcp)
register_monitoring_tools(mcp)
register_rag_tools(mcp)
register_safety_tools(mcp)
register_ui_tools(mcp)
register_demo_tools(mcp)
register_wake_word_tools(mcp)

if funasr_provider:
    from pathlib import Path as _Path

    from speech_mcp.voice_bus import set_transcribe_path_hook

    def _voice_transcribe_file(path: _Path) -> str:
        import anyio

        async def _go() -> str:
            result = await funasr_provider.transcribe_file(str(path), language="auto")
            if not result.get("success", True):
                return ""
            return str(result.get("text") or result.get("formatted") or "").strip()

        return anyio.run(_go)

    set_transcribe_path_hook(_voice_transcribe_file)
    logger.info("Fleet voice STT hook: FunASR file transcription")

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


@app.post("/api/v1/stop")
async def api_stop():
    """Emergency stop: cancel all timers, stop wake word, and purge winsound audio."""
    import winsound

    try:
        # Purge all winsound buffers immediately
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass

    # Cancel all active timers
    cancelled_count = 0
    for timer_id, task in list(_timers.items()):
        if not task.done():
            task.cancel()
            cancelled_count += 1
        _timers.pop(timer_id, None)

    # Stop wake word listener
    from fastmcp import Context

    from speech_mcp.tools.wake_word import configure_local_wake_word

    try:
        await configure_local_wake_word(ctx=Context(), action="stop")
    except Exception:
        pass

    logger.warning(f"!!! EMERGENCY STOP TRIGGERED: Cancelled {cancelled_count} timers !!!")
    return {"success": True, "cancelled_timers": cancelled_count, "audio_purged": True}


@app.get("/api/v1/health")
async def health_check():
    from speech_mcp.tools.wake_word import _listener_thread

    wake_active = _listener_thread is not None and _listener_thread.is_alive()

    return {
        "status": "healthy",
        "version": "0.6.3",
        "mcp_server": "online",
        "rag_sources": get_store().list_sources(),
        "active_timers": len(_timers),
        "wake_word_active": wake_active,
        "tokens": {
            "google_api_key": bool(os.getenv("GOOGLE_API_KEY")),
            "hume_api_key": bool(os.getenv("HUME_API_KEY")),
            "hume_config_id": bool(os.getenv("HUME_CONFIG_ID")),
            "elevenlabs_api_key": bool(os.getenv("ELEVENLABS_API_KEY")),
        },
        "providers": {
            "hume": bool(hume_client),
            "elevenlabs": bool(eleven_client),
            "gemini": bool(gemini_client),
            "gemma": True,  # Local engine always assumed available
            "funasr": bool(funasr_provider),
            "windows": True,
        },
        "funasr": await funasr_provider.health_probe() if funasr_provider else {"available": False},
    }


@app.get("/health")
@app.get("/api/health")
@app.get("/api/status")
@app.get("/")
async def fleet_health_check():
    return {"status": "ok", "version": "0.6.3"}


@app.get("/api/capabilities")
async def api_capabilities():
    return {
        "server": "speech-mcp",
        "version": "0.6.3",
        "fastmcp": "3.2.0+",
        "protocols": ["MCP SSE", "REST", "WebSocket"],
        "features": {
            "tts": ["windows", "gemini", "hume", "elevenlabs", "gemma"],
            "stt": ["funasr", "gemini", "gemma"],
            "streaming": ["hume_evi", "gemini_live"],
            "rag": True,
            "voice_cloning": True,
            "wake_word": True,
            "prefab_ui": True,
            "sampling": True,
            "agentic_workflow": True,
            "mcp_bridge": bool(_bridge_proxies),
        },
        "bridges": _bridge_proxies,
        "endpoints": {
            "health": "/api/v1/health",
            "capabilities": "/api/capabilities",
            "mcp": "/mcp",
            "stream": "/ws/stream",
            "logs": "/ws/logs",
        },
    }


@app.get("/api/v1/hardware")
async def api_hardware():
    try:
        from scripts.utils.hardware_probe import get_cameras, get_microphones, get_monitors

        return {"monitors": get_monitors(), "microphones": get_microphones(), "cameras": get_cameras()}
    except Exception as e:
        logger.error(f"Hardware probe failed: {e}")
        return {"error": str(e)}


class WakeWordRequest(BaseModel):
    action: str
    keyword: str = "computer"
    sensitivity: float = 0.5


@app.post("/api/v1/wake_word")
async def api_wake_word(req: WakeWordRequest, ctx: Context = Depends(lambda: Context())):
    """Bridge to the configure_local_wake_word tool."""
    # We redefine/call the logic here for the API
    from speech_mcp.tools.wake_word import configure_local_wake_word

    return await configure_local_wake_word(ctx=ctx, keyword=req.keyword, sensitivity=req.sensitivity, action=req.action)


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
    answer = await local_llm_provider.generate(
        provider=provider, base_url=base_url, model=model, prompt=prompt, system=system
    )
    return {"success": True, "answer": answer, "sources": [r["metadata"].get("filename", "unknown") for r in results]}


@app.get("/api/v1/voices")
async def api_voices():
    providers = []
    if hume_client:
        providers.append({"name": "hume", "status": "available", "voices": ["ito", "kora"]})
    if eleven_client:
        try:
            resp = await anyio.to_thread.run_sync(lambda: eleven_client.voices.get_all())
            el_voices = [v.voice_id for v in resp.voices]
        except Exception as e:
            logger.warning(f"ElevenLabs voices fetch failed: {e}")
            el_voices = []
        providers.append({"name": "elevenlabs", "status": "available", "voices": el_voices})
    if gemini_client:
        providers.append({"name": "gemini", "status": "available", "voices": gemini_client.voices})
    if gemma_client:
        providers.append({"name": "gemma", "status": "available", "voices": gemma_client.voices})
    # Windows SAPI5 — enumerate installed voices
    try:
        import pyttsx3

        def _get_win_voices():
            engine = pyttsx3.init()
            vs = engine.getProperty("voices")
            engine.stop()
            return [v.name for v in vs] if vs else ["default"]

        win_voices = await anyio.to_thread.run_sync(_get_win_voices)
    except Exception:
        win_voices = ["default"]
    providers.append({"name": "windows", "status": "available", "voices": win_voices})
    return {"providers": providers}


@app.post("/api/v1/voices/clone")
async def api_voices_clone(request: Request):
    """Instant Voice Clone via ElevenLabs IVC. Accepts multipart/form-data: name (str) + file (audio)."""
    from fastapi import UploadFile

    if not eleven_client:
        raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")
    form = await request.form()
    name = form.get("name", "")
    file: UploadFile | None = form.get("file")
    if not name:
        raise HTTPException(status_code=400, detail="name field required")
    if not file:
        raise HTTPException(status_code=400, detail="file field required")
    suffix = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(await file.read())

        def _clone():
            with open(tmp_path, "rb") as f:
                return eleven_client.voices.ivc.create(
                    name=name,
                    files=[f],
                    description="IVC clone uploaded via speech-mcp webapp",
                )

        result = await anyio.to_thread.run_sync(_clone)
        return {"success": True, "voice_id": result.voice_id, "name": name, "status": "cloned"}
    except Exception as e:
        logger.exception("Voice clone failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@app.get("/api/v1/history")
async def api_history():
    from speech_mcp.state import _history

    return list(_history)


@app.post("/api/v1/tts")
async def api_tts(req: TTSRequest):
    """Synthesize speech via any provider and play on server speaker."""
    from speech_mcp.state import add_history

    add_history("tts", req.text, req.provider)
    try:
        if req.provider == "gemma":
            if not gemma_client:
                raise HTTPException(status_code=503, detail="Gemma not initialized")
            await gemma_client.synthesize_and_play(req.text, voice=req.voice_id)
            return {"success": True, "provider": "gemma", "voice": req.voice_id}
        if req.provider == "gemini":
            if not gemini_client:
                raise HTTPException(status_code=503, detail="Gemini not configured")
            await anyio.to_thread.run_sync(lambda: gemini_client.synthesize_and_play(req.text, voice=req.voice_id))
            return {"success": True, "provider": "gemini", "voice": req.voice_id}
        if req.provider == "hume":
            if not hume_client:
                raise HTTPException(status_code=503, detail="Hume not configured")
            from speech_mcp.tools.speech import _hume_speak

            await _hume_speak(hume_client, req.text, description=req.emotion)
            return {"success": True, "provider": "hume"}
        if req.provider == "elevenlabs":
            if not eleven_client:
                raise HTTPException(status_code=503, detail="ElevenLabs not configured")
            from speech_mcp.tools.speech import _elevenlabs_speak

            await anyio.to_thread.run_sync(lambda: _elevenlabs_speak(eleven_client, req.text, voice_id=req.voice_id))
            return {"success": True, "provider": "elevenlabs", "voice": req.voice_id}
        # fallback: windows
        import pyttsx3

        def _win():
            engine = pyttsx3.init()
            engine.say(req.text)
            engine.runAndWait()

        await anyio.to_thread.run_sync(_win)
        return {"success": True, "provider": "windows"}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("TTS endpoint failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/tts/wav")
async def api_tts_wav(text: str, provider: str = "windows", voice_id: str = "default"):
    from speech_mcp.state import add_history

    add_history("tts", text, provider)
    if not text:
        raise HTTPException(status_code=400, detail="text param required")
    if provider == "windows":
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        def _synth():
            import pyttsx3

            engine = pyttsx3.init()
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

        await anyio.to_thread.run_sync(_synth)
        with open(tmp_path, "rb") as f:
            wav_bytes = f.read()
        os.remove(tmp_path)
        return Response(content=wav_bytes, media_type="audio/wav")
    if provider == "elevenlabs":
        if not eleven_client:
            raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")
        effective_voice = voice_id if voice_id and voice_id != "default" else None
        if not effective_voice:
            raise HTTPException(status_code=400, detail="voice_id required for ElevenLabs preview")

        def _synth_el():
            audio = bytearray()
            for chunk in eleven_client.text_to_speech.convert(
                voice_id=effective_voice,
                text=text,
                output_format="mp3_44100_128",
            ):
                audio.extend(chunk)
            return bytes(audio)

        mp3_bytes = await anyio.to_thread.run_sync(_synth_el)
        return Response(content=mp3_bytes, media_type="audio/mpeg")
    if provider == "gemini":
        if not gemini_client:
            raise HTTPException(status_code=503, detail="Gemini not configured")
        effective_voice = voice_id if voice_id and voice_id != "default" else "Kore"

        def _synth_gemini():
            return gemini_client.synthesize_wav(text, voice_name=effective_voice)

        wav_bytes = await anyio.to_thread.run_sync(_synth_gemini)
        return Response(content=wav_bytes, media_type="audio/wav")
    raise HTTPException(status_code=400, detail=f"provider '{provider}' not supported")


@app.post("/api/v1/transcribe")
async def api_transcribe(request: Request):
    provider = request.query_params.get("provider", "funasr")
    language = request.query_params.get("language", "auto")

    if provider == "funasr":
        if not funasr_provider:
            raise HTTPException(
                status_code=503,
                detail="FunASR not configured — set FUNASR_ENABLED=true or FUNASR_OPENAI_URL",
            )
        try:
            body = await request.body()
            if not body:
                raise HTTPException(status_code=400, detail="Empty audio body")
            import base64

            result = await funasr_provider.transcribe_chunk(
                base64.b64encode(body).decode("ascii"),
                language=language,
            )
            if not result.get("success"):
                raise HTTPException(status_code=500, detail=result.get("error", "transcription failed"))
            return result
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("FunASR API transcription failed")
            raise HTTPException(status_code=500, detail=str(e)) from e

    if not gemini_client and not gemma_client:
        raise HTTPException(status_code=503, detail="No STT providers (Gemini/Gemma) configured")
    try:
        file = await request.body()
        if gemma_client and provider == "gemma":
            transcript = await gemma_client.transcribe(file, mime_type="audio/wav")
        elif gemini_client:
            transcript = await anyio.to_thread.run_sync(lambda: gemini_client.transcribe(file, mime_type="audio/wav"))
        else:
            raise HTTPException(status_code=503, detail=f"Provider '{provider}' not available")
        return {"success": True, "provider": provider, "transcript": transcript, "text": transcript}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("API transcription failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/demos/run")
async def api_run_demo(req: DemoRequest):
    from speech_mcp.tools.demos import DEMO_MAP

    script_filename = DEMO_MAP.get(req.demo)
    if not script_filename:
        return {"success": False, "error": f"Demo '{req.demo}' not found."}
    script_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "scripts", "demos")
    script_path = os.path.normpath(os.path.join(script_dir, script_filename))
    try:
        uv_path = shutil.which("uv") or "uv"
        result = await anyio.to_thread.run_sync(
            lambda: subprocess.run(
                [uv_path, "run", "python", script_path],
                capture_output=True,
                text=True,
                check=False,
            )
        )
        return {"success": result.returncode == 0, "demo": req.demo, "output": (result.stdout + result.stderr).strip()}
    except Exception as e:
        return {"success": False, "error": str(e)}


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
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _log_clients.discard(websocket)


def main():
    asyncio.run(mcp.run_stdio_async())


if __name__ == "__main__":
    main()
