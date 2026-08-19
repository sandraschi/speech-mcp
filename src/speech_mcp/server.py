import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from contextlib import asynccontextmanager
from time import localtime, strftime
from typing import TYPE_CHECKING, Any

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    Request,
    Response,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastmcp import FastMCP
from fastmcp.server import create_proxy
from hume import HumeClient
from pydantic import BaseModel

from speech_mcp.providers.funasr import FunASRConfig, FunASRProvider
from speech_mcp.providers.gemini import GeminiProvider
from speech_mcp.providers.gemma import gemma_provider
from speech_mcp.skills import get_skill, list_skills, register_skill_resources
from speech_mcp.state import _timers, get_store
from speech_mcp.streaming import handle_websocket_stream
from speech_mcp.synthesis import speak_text
from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.analytics import register_analytics_tools
from speech_mcp.tools.chat import register_chat_tools
from speech_mcp.tools.demos import DemoName, register_demo_tools
from speech_mcp.tools.macros import register_macro_tools
from speech_mcp.tools.memory import register_memory_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.readout import register_readout_tools
from speech_mcp.tools.revise import register_revise_tools
from speech_mcp.tools.runtime import register_runtime_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.sound_events import register_sound_event_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.streaming_asr import register_streaming_asr_tools
from speech_mcp.tools.stt import register_stt_tools
from speech_mcp.tools.translate import register_translate_tools
from speech_mcp.tools.ui import register_ui_tools
from speech_mcp.tools.utility import _weather_report, register_utility_tools
from speech_mcp.tools.voice_bank import register_voice_bank_tools
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
FUNASR_MODEL = os.getenv("FUNASR_MODEL", "FunAudioLLM/Fun-ASR-MLT-Nano-2512")
FUNASR_DEVICE = os.getenv("FUNASR_DEVICE", "cuda:0")
FUNASR_HUB = os.getenv("FUNASR_HUB", "hf")
FUNASR_VAD_MODEL = os.getenv("FUNASR_VAD_MODEL", "fsmn-vad")
FUNASR_PUNC_MODEL = os.getenv("FUNASR_PUNC_MODEL", "ct-punc")
FUNASR_SPK_MODEL = os.getenv("FUNASR_SPK_MODEL", "cam++")

# --- sherpa-onnx streaming STT (ja/en/de, CPU, barge-in) ---
SHERPA_ASR_ENABLED = os.getenv("SHERPA_ASR_ENABLED", "").lower() in ("1", "true", "yes")
SHERPA_ASR_LANG = os.getenv("SHERPA_ASR_LANG", "en").strip().lower()
SHERPA_MODEL_DIR = os.getenv("SHERPA_MODEL_DIR", "").strip() or None
SHERPA_NUM_THREADS = int(os.getenv("SHERPA_NUM_THREADS", "2"))
SHERPA_PROVIDER = os.getenv("SHERPA_PROVIDER", "").strip() or None
SHERPA_BARGE_IN = os.getenv("SHERPA_BARGE_IN", "").lower() in ("1", "true", "yes")

# --- Log broadcast infrastructure ---
_log_clients: set[WebSocket] = set()
_log_queue: asyncio.Queue | None = None
_START_TS: float = time.time()


def _server_version() -> str:
    try:
        from importlib.metadata import version

        return version("speech-mcp")
    except Exception:
        return "0.6.4"


def _fastmcp_version() -> str:
    try:
        from importlib.metadata import version

        return version("fastmcp")
    except Exception:
        return "3.4.x"


def _gpu_info() -> dict:
    """Real GPU / VRAM state from torch (if installed and CUDA available)."""
    try:
        import torch

        if not torch.cuda.is_available():
            return {"available": False, "device": "cpu", "torch": torch.__version__}
        props = torch.cuda.get_device_properties(0)
        free_bytes, _total = torch.cuda.mem_get_info(0)
        return {
            "available": True,
            "device": "cuda:0",
            "name": props.name,
            "vram_total_gb": round(props.total_memory / 1e9, 1),
            "vram_free_gb": round(free_bytes / 1e9, 1),
            "torch": torch.__version__,
        }
    except Exception as e:
        return {"available": False, "device": "cpu", "error": str(e)}


def _sherpa_device() -> str:
    try:
        from speech_mcp.runtime_config import sherpa_device as _sd

        return _sd()
    except Exception:
        return "cpu"


def funasr_device_runtime() -> str:
    try:
        from speech_mcp.runtime_config import funasr_device as _fd

        return _fd()
    except Exception:
        return FUNASR_DEVICE


def sherpa_device_runtime() -> str:
    return _sherpa_device()


def _ort_providers() -> list[str]:
    try:
        import onnxruntime as ort

        return list(ort.get_available_providers())
    except Exception:
        return []


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
        queue = _log_queue
        if queue is None:
            await asyncio.sleep(0.2)
            continue
        msg = await queue.get()
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

    # ── Voice Command Bus auto-start (HTTP mode only) ─────────────────────
    from speech_mcp.voice_bus import fleet_voice_enabled

    autostart = os.environ.get("FLEET_VOICE_AUTOSTART", "1").strip().lower()
    if fleet_voice_enabled() and autostart not in ("0", "false", "no"):
        from speech_mcp.voice_listener import start_fleet_listener

        wake_kw = os.environ.get("FLEET_VOICE_WAKE_KEYWORD", "hey_jarvis").strip() or "hey_jarvis"
        start_fleet_listener(wake_kw, 0.5, None)
        logger.info("Fleet voice listener auto-started (wake='%s')", wake_kw)

    yield
    broadcaster.cancel()
    for task in _timers.values():
        task.cancel()


app = FastAPI(title="Speech MCP Stream Gateway", lifespan=lifespan)

# Modern CORS for local fleet dev + Tauri desktop (unconditional regex per CORS_STANDARD)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:10908",
        "http://127.0.0.1:10908",
        "http://localhost:10947",
        "http://127.0.0.1:10947",
        "http://tauri.localhost",
        "https://tauri.localhost",
        "tauri://localhost",
    ],
    allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP("speech-mcp")

# Skill resources: skill://{name} -> SKILL.md (also served via /api/skills)
register_skill_resources(mcp)

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

# --- sherpa-onnx streaming STT (optional; auto-downloads model on first enable) ---
sherpa_asr = None
if SHERPA_ASR_ENABLED:
    try:
        from speech_mcp.providers.sherpa_onnx import SherpaBargeIn, SherpaStreamingASR, ensure_model

        model_dir = ensure_model(SHERPA_ASR_LANG, SHERPA_MODEL_DIR)
        sherpa_asr = SherpaStreamingASR(
            lang=SHERPA_ASR_LANG,
            model_dir=model_dir,
            num_threads=SHERPA_NUM_THREADS,
            provider=SHERPA_PROVIDER,
        )
        if SHERPA_BARGE_IN:
            sherpa_asr._barge_in = SherpaBargeIn(sherpa_asr)
        from speech_mcp.voice_listener import set_sherpa_streaming

        set_sherpa_streaming(sherpa_asr)
        logger.info("sherpa-onnx streaming ASR enabled (lang=%s, model=%s)", SHERPA_ASR_LANG, model_dir)
    except Exception as e:
        logger.warning("sherpa-onnx streaming ASR disabled: %s", e)
        sherpa_asr = None

register_speech_tools(mcp, hume_client, eleven_client, gemini_client, gemma_client)
register_stt_tools(mcp, funasr_provider, gemini_client, gemma_client)
register_agentic_tools(mcp, hume_client)
register_utility_tools(mcp)
register_monitoring_tools(mcp)
register_rag_tools(mcp)
register_safety_tools(mcp)

# Shared provider availability map + text-to-speech dispatcher for readout/
# macro/translate tools (avoids circular imports into this module).
_providers = {
    "hume": bool(hume_client),
    "elevenlabs": bool(eleven_client),
    "gemini": bool(gemini_client),
    "gemma": True,
    "funasr": bool(funasr_provider),
    "windows": True,
    "sherpa_streaming": bool(sherpa_asr),
}


async def _speak(
    text: str, provider: str = "windows", voice_id: str = "default", description: str | None = None
) -> dict:
    return await speak_text(
        text,
        provider=provider,
        voice_id=voice_id,
        description=description,
        gemini_client=gemini_client,
        eleven_client=eleven_client,
        hume_client=hume_client,
        gemma_client=gemma_client,
    )


register_ui_tools(mcp, providers=_providers)
register_streaming_asr_tools(mcp, sherpa_asr)
register_runtime_tools(mcp, sherpa_asr)
register_revise_tools(mcp)
register_demo_tools(mcp)
register_wake_word_tools(mcp)
register_memory_tools(mcp)
register_voice_bank_tools(mcp)
register_sound_event_tools(mcp)
register_chat_tools(mcp)
register_analytics_tools(mcp)
register_translate_tools(mcp, funasr_provider, _speak)
register_readout_tools(mcp, _providers, _speak)
register_macro_tools(mcp, _speak, _weather_report)

if funasr_provider:
    from pathlib import Path as _Path

    from speech_mcp.voice_bus import set_transcribe_path_hook

    _funasr = funasr_provider

    def _voice_transcribe_file(path: _Path) -> str:
        import asyncio

        async def _go() -> str:
            result = await _funasr.transcribe_file(str(path), language="auto")
            if not result.get("success", True):
                return ""
            return str(result.get("text") or result.get("formatted") or "").strip()

        return asyncio.run(_go())

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


class SubtitleReviseRequest(BaseModel):
    srt: str = ""
    language: str = "ja"
    series: str = ""
    glossary: str = ""


class TranscriptCreateRequest(BaseModel):
    srt: str
    series: str = ""
    season: int | None = None
    episode: int | None = None
    title: str = ""
    source: str = "upload"
    source_media_key: str = ""
    language: str = "ja"


class TranscriptStatusRequest(BaseModel):
    status: str


class PlexTranscribeRequest(BaseModel):
    media_key: str
    plex_mcp_url: str = "http://127.0.0.1:10740"
    series: str = ""
    season: int | None = None
    episode: int | None = None
    language: str = "ja"


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
    except Exception as e:
        logger.debug("winsound purge unavailable: %s", e)

    # Cancel all active timers
    cancelled_count = 0
    for timer_id, task in list(_timers.items()):
        if not task.done():
            task.cancel()
            cancelled_count += 1
        _timers.pop(timer_id, None)

    # Stop wake word listener

    from speech_mcp.tools.wake_word import wake_word_configure

    try:
        await wake_word_configure(ctx=None, action="stop")
    except Exception as e:
        logger.warning("Wake word stop during emergency stop failed: %s", e)

    logger.warning(f"!!! EMERGENCY STOP TRIGGERED: Cancelled {cancelled_count} timers !!!")
    return {"success": True, "cancelled_timers": cancelled_count, "audio_purged": True}


@app.get("/api/v1/health")
async def health_check():
    from speech_mcp.tools.wake_word import _listener_thread

    wake_active = _listener_thread is not None and _listener_thread.is_alive()
    gpu = _gpu_info()

    return {
        "status": "healthy",
        "version": _server_version(),
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
            "sherpa_streaming": bool(sherpa_asr),
        },
        "gpu": gpu,
        "devices": {
            "funasr": {
                "configured": bool(funasr_provider),
                "device": funasr_device_runtime(),
                "cuda_available": gpu.get("available", False),
                "loaded": bool(funasr_provider and getattr(funasr_provider, "_model", None) is not None),
            },
            "sherpa_streaming": {
                "configured": bool(sherpa_asr),
                "device": sherpa_device_runtime(),
                "lang": SHERPA_ASR_LANG if sherpa_asr else None,
                "onnxruntime_providers": _ort_providers(),
                "barge_in": bool(getattr(sherpa_asr, "_barge_in", None)),
            },
        },
        "funasr": await funasr_provider.health_probe() if funasr_provider else {"available": False},
    }


@app.get("/health")
@app.get("/api/health")
@app.get("/api/status")
@app.get("/")
async def fleet_health_check():
    return {"status": "ok", "version": _server_version()}


@app.get("/api/capabilities")
async def api_capabilities():
    return {
        "server": "speech-mcp",
        "version": _server_version(),
        "fastmcp": _fastmcp_version(),
        "protocols": ["MCP SSE", "REST", "WebSocket"],
        "features": {
            "tts": ["windows", "gemini", "hume", "elevenlabs", "gemma"],
            "stt": ["funasr", "gemini", "gemma", "sherpa_streaming"],
            "streaming": ["hume_evi", "gemini_live", "sherpa_streaming"],
            "barge_in": bool(getattr(sherpa_asr, "_barge_in", None)),
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


@app.get("/api/tools")
async def api_tools():
    """List registered MCP tools (dynamic, for the webapp Tools page)."""
    tools: list[dict] = []
    try:
        for t in await mcp.list_tools():
            tools.append({"name": t.name, "description": getattr(t, "description", "") or ""})
    except Exception as e:
        logger.warning("tool list failed: %s", e)
    return {"success": True, "tools": tools, "count": len(tools)}


@app.get("/api/skills")
async def api_skills():
    """List installed skills (from the skills/ directory)."""
    skills = list_skills()
    return {"success": True, "skills": skills, "count": len(skills)}


@app.get("/api/skills/{skill_name}")
async def api_skill_content(skill_name: str):
    content = get_skill(skill_name)
    if content is None:
        raise HTTPException(status_code=404, detail=f"Unknown skill: {skill_name}")
    return {"success": True, "name": skill_name, "content": content}


@app.get("/api/v1/diagnostics")
async def api_diagnostics():
    """Full diagnostics for CUA-NSIS smoke testing: tool list, system info, errors."""
    tools: list[dict] = []
    try:
        for t in await mcp.list_tools():
            tools.append({"name": t.name})
    except Exception as e:
        logger.warning("diagnostics tool list failed: %s", e)
    return {
        "status": "ok",
        "server": "speech-mcp",
        "version": _server_version(),
        "uptime_seconds": int(time.time() - _START_TS),
        "tool_count": len(tools),
        "tools": tools,
        "system": {"platform": platform.platform(), "python": platform.python_version()},
        "gpu": _gpu_info(),
        "devices": {
            "funasr": {
                "configured": bool(funasr_provider),
                "device": funasr_device_runtime(),
                "cuda_available": _gpu_info().get("available", False),
                "loaded": bool(funasr_provider and getattr(funasr_provider, "_model", None) is not None),
            },
            "sherpa_streaming": {
                "configured": bool(sherpa_asr),
                "device": sherpa_device_runtime(),
                "lang": SHERPA_ASR_LANG if sherpa_asr else None,
                "onnxruntime_providers": _ort_providers(),
                "barge_in": bool(getattr(sherpa_asr, "_barge_in", None)),
            },
        },
        "errors": [],
    }


class ShutdownRequest(BaseModel):
    confirm: bool = False


@app.post("/api/v1/shutdown")
async def api_shutdown(req: ShutdownRequest):
    """Graceful self-termination for the HTTP daemon (confirm=True required)."""
    if not req.confirm:
        return {"success": False, "error": "confirm=True required"}
    threading.Timer(1.0, os._exit, args=(0,)).start()
    return {"success": True, "message": "Server shutting down in ~1s"}


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
    sleep_keyword: str | None = None
    sensitivity: float = 0.5


@app.post("/api/v1/wake_word")
async def api_wake_word(req: WakeWordRequest):
    """Bridge to the configure_local_wake_word tool (REST has no MCP context)."""
    from speech_mcp.tools.wake_word import wake_word_configure

    return await wake_word_configure(
        ctx=None,
        keyword=req.keyword,
        sleep_keyword=req.sleep_keyword,
        sensitivity=req.sensitivity,
        action=req.action,
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

            def _get_el_voices(client: ElevenLabs) -> list[str]:
                from typing import Any, cast

                resp = client.voices.get_all()
                raw = cast(Any, getattr(resp, "voices", []))
                return [v.voice_id for v in raw]

            el_voices: list[str] = await asyncio.to_thread(_get_el_voices, eleven_client)
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
            from typing import Any, cast

            engine = pyttsx3.init()
            vs = cast(list[Any], engine.getProperty("voices"))
            engine.stop()
            return [v.name for v in vs] if vs else ["default"]

        win_voices = await asyncio.to_thread(_get_win_voices)
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
    name = form.get("name")
    file = form.get("file")
    if not isinstance(name, str) or not name:
        raise HTTPException(status_code=400, detail="name field required")
    if not isinstance(file, UploadFile):
        raise HTTPException(status_code=400, detail="file field required")
    suffix = os.path.splitext(file.filename or "audio.mp3")[1] or ".mp3"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(await file.read())

        el = eleven_client

        def _clone():
            with open(tmp_path, "rb") as f:
                return el.voices.ivc.create(
                    name=name,
                    files=[f],
                    description="IVC clone uploaded via speech-mcp webapp",
                )

        result = await asyncio.to_thread(_clone)
        return {"success": True, "voice_id": result.voice_id, "name": name, "status": "cloned"}
    except Exception as e:
        logger.exception("Voice clone failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as e:
                logger.debug("temp file cleanup failed for %s: %s", tmp_path, e)


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
            gemma = gemma_client
            if not gemma:
                raise HTTPException(status_code=503, detail="Gemma not initialized")
            played = await asyncio.to_thread(lambda: gemma.synthesize_and_play(req.text, voice=req.voice_id))
            if not played:
                raise HTTPException(status_code=500, detail="Gemma/SAPI TTS failed")
            return {"success": True, "provider": "gemma", "voice": req.voice_id}
        if req.provider == "gemini":
            gemini = gemini_client
            if not gemini:
                raise HTTPException(status_code=503, detail="Gemini not configured")
            from speech_mcp.tools.speech import _play_wav_file

            wav = await asyncio.to_thread(lambda: gemini.synthesize_wav(req.text, voice_name=req.voice_id or "Kore"))
            if not wav:
                raise HTTPException(status_code=500, detail="Gemini returned empty audio")
            import tempfile as _tf

            with _tf.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(wav)
                tmp_path = tmp.name
            try:
                await _play_wav_file(tmp_path)
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
            return {"success": True, "provider": "gemini", "voice": req.voice_id}
        if req.provider == "hume":
            hume = hume_client
            if not hume:
                raise HTTPException(status_code=503, detail="Hume not configured")
            from speech_mcp.tools.speech import _hume_speak

            await _hume_speak(hume, req.text, description=req.emotion)
            return {"success": True, "provider": "hume"}
        if req.provider == "elevenlabs":
            el = eleven_client
            if not el:
                raise HTTPException(status_code=503, detail="ElevenLabs not configured")
            from speech_mcp.tools.speech import _elevenlabs_speak

            await asyncio.to_thread(lambda: _elevenlabs_speak(el, req.text, voice_id=req.voice_id))
            return {"success": True, "provider": "elevenlabs", "voice": req.voice_id}
        # fallback: windows
        import pyttsx3

        def _win():
            engine = pyttsx3.init()
            engine.say(req.text)
            engine.runAndWait()

        await asyncio.to_thread(_win)
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

        await asyncio.to_thread(_synth)
        with open(tmp_path, "rb") as f:
            wav_bytes = f.read()
        os.remove(tmp_path)
        return Response(content=wav_bytes, media_type="audio/wav")
    if provider == "elevenlabs":
        el = eleven_client
        if not el:
            raise HTTPException(status_code=503, detail="ELEVENLABS_API_KEY not configured")
        effective_voice = voice_id if voice_id and voice_id != "default" else None
        if not effective_voice:
            raise HTTPException(status_code=400, detail="voice_id required for ElevenLabs preview")

        def _synth_el():
            audio = bytearray()
            for chunk in el.text_to_speech.convert(
                voice_id=effective_voice,
                text=text,
                output_format="mp3_44100_128",
            ):
                audio.extend(chunk)
            return bytes(audio)

        mp3_bytes = await asyncio.to_thread(_synth_el)
        return Response(content=mp3_bytes, media_type="audio/mpeg")
    if provider == "gemini":
        gemini = gemini_client
        if not gemini:
            raise HTTPException(status_code=503, detail="Gemini not configured")
        effective_voice = voice_id if voice_id and voice_id != "default" else "Kore"

        def _synth_gemini():
            return gemini.synthesize_wav(text, voice_name=effective_voice)

        wav_bytes = await asyncio.to_thread(_synth_gemini)
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
        gemma = gemma_client
        gemini = gemini_client
        if gemma and provider == "gemma":
            transcript = await gemma.transcribe(file, mime_type="audio/wav")
        elif gemini:
            transcript = await asyncio.to_thread(lambda: gemini.transcribe(file, mime_type="audio/wav"))
        else:
            raise HTTPException(status_code=503, detail=f"Provider '{provider}' not available")
        return {"success": True, "provider": provider, "transcript": transcript, "text": transcript}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("API transcription failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


def _segments_to_srt(segments: list[dict]) -> str:
    def _ts(seconds: float) -> str:
        ms = round(seconds * 1000)
        h, rem = divmod(ms, 3600000)
        m, rem = divmod(rem, 60000)
        s, ms = divmod(rem, 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    blocks: list[str] = []
    for i, seg in enumerate(segments, 1):
        blocks.append(f"{i}\n{_ts(seg['start_s'])} --> {_ts(seg['end_s'])}\n{seg['text'].strip()}")
    return "\n\n".join(blocks) + "\n"


def _segments_to_vtt(segments: list[dict]) -> str:
    def _ts(seconds: float) -> str:
        ms = round(seconds * 1000)
        m, rem = divmod(ms, 60000)
        s, ms = divmod(rem, 1000)
        return f"{m:02d}:{s:02d}.{ms:03d}"

    blocks = ["WEBVTT", ""]
    for seg in segments:
        blocks.append(f"{_ts(seg['start_s'])} --> {_ts(seg['end_s'])}\n{seg['text'].strip()}")
        blocks.append("")
    return "\n".join(blocks)


def _segments_to_txt(segments: list[dict]) -> str:
    return "\n".join(seg["text"].strip() for seg in segments if seg["text"].strip())


def _render_subtitles(segments: list[dict], fmt: str) -> str:
    if fmt == "srt":
        return _segments_to_srt(segments)
    if fmt == "vtt":
        return _segments_to_vtt(segments)
    if fmt == "txt":
        return _segments_to_txt(segments)
    raise HTTPException(status_code=400, detail="format must be srt, vtt, or txt")


@app.post("/api/v1/transcribe/file")
async def api_transcribe_file(
    file: UploadFile = File(...),
    language: str = "auto",
    format: str = "json",
):
    """Transcribe an uploaded audio file. format: json (segments), srt, vtt, or txt."""
    if not funasr_provider:
        raise HTTPException(status_code=503, detail="FunASR not configured — set FUNASR_ENABLED=true")
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")
        suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
        import tempfile

        tmpdir = tempfile.mkdtemp(prefix="speech-mcp-")
        tmp_path = os.path.join(tmpdir, f"upload{suffix}")
        with open(tmp_path, "wb") as fh:
            fh.write(data)
        try:
            result = await funasr_provider.transcribe_file(tmp_path, language=language)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "transcription failed"))
        segments = result.get("segments", [])
        if format == "json":
            return {
                "success": True,
                "provider": "funasr",
                "text": result.get("text", ""),
                "segments": segments,
            }
        return Response(content=_render_subtitles(segments, format), media_type="text/plain; charset=utf-8")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("File transcription failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/api/v1/transcribe/batch")
async def api_transcribe_batch(
    files: list[UploadFile] = File(...),
    language: str = "auto",
):
    """Batch-transcribe multiple uploaded audio files (FunASR)."""
    if not funasr_provider:
        raise HTTPException(status_code=503, detail="FunASR not configured — set FUNASR_ENABLED=true")
    import tempfile

    results: list[dict] = []
    for file in files:
        try:
            data = await file.read()
            suffix = os.path.splitext(file.filename or "audio.wav")[1] or ".wav"
            tmpdir = tempfile.mkdtemp(prefix="speech-mcp-")
            tmp_path = os.path.join(tmpdir, f"upload{suffix}")
            with open(tmp_path, "wb") as fh:
                fh.write(data)
            try:
                result = await funasr_provider.transcribe_file(tmp_path, language=language)
            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
            results.append(
                {
                    "filename": file.filename or "audio.wav",
                    "success": bool(result.get("success")),
                    "error": result.get("error"),
                    "text": result.get("text", ""),
                    "segments": result.get("segments", []),
                }
            )
        except Exception as e:
            logger.exception("Batch item failed: %s", file.filename)
            results.append(
                {
                    "filename": file.filename or "audio.wav",
                    "success": False,
                    "error": str(e),
                    "text": "",
                    "segments": [],
                }
            )
    return {"success": True, "results": results, "count": len(results)}


@app.post("/api/v1/subtitles/revise")
async def api_subtitles_revise(req: SubtitleReviseRequest):
    from speech_mcp.tools.revise import revise_srt

    return await revise_srt(req.srt, series=req.series, glossary=req.glossary, language=req.language)


@app.post("/api/v1/transcripts")
async def api_transcript_create(req: TranscriptCreateRequest):
    import speech_mcp.transcript_depot as depot

    row = depot.record(
        req.srt,
        series=req.series,
        season=req.season,
        episode=req.episode,
        title=req.title,
        source=req.source,
        source_media_key=req.source_media_key,
        language=req.language,
        model="funasr",
    )
    return {"success": True, "transcript": row}


@app.get("/api/v1/transcripts")
async def api_transcript_list(limit: int = 100):
    import speech_mcp.transcript_depot as depot

    transcripts = depot.list_transcripts(limit=limit)
    return {"success": True, "transcripts": transcripts, "count": len(transcripts)}


@app.get("/api/v1/transcripts/{tid}")
async def api_transcript_get(tid: int):
    import speech_mcp.transcript_depot as depot

    row = depot.read_transcript(tid)
    if not row:
        raise HTTPException(status_code=404, detail=f"No transcript #{tid}")
    return {"success": True, "transcript": row}


@app.post("/api/v1/transcripts/{tid}/status")
async def api_transcript_status(tid: int, req: TranscriptStatusRequest):
    import speech_mcp.transcript_depot as depot

    row = depot.set_status(tid, req.status)
    if not row:
        raise HTTPException(status_code=404, detail=f"No transcript #{tid}")
    return {"success": True, "transcript": row}


@app.post("/api/v1/transcripts/{tid}/revise")
async def api_transcript_revise(tid: int, req: SubtitleReviseRequest | None = None):
    import speech_mcp.transcript_depot as depot
    from speech_mcp.tools.revise import revise_srt

    row = depot.read_transcript(tid)
    if not row:
        raise HTTPException(status_code=404, detail=f"No transcript #{tid}")
    series = (req.series if req and req.series else row.get("series", "")) or ""
    glossary = (req.glossary if req else "") or ""
    result = await revise_srt(row["raw_srt"], series=series, glossary=glossary, language=row.get("language", "ja"))
    if not result.get("success"):
        raise HTTPException(status_code=503, detail=result.get("error", "revision failed"))
    updated = depot.save_revised(tid, result["revised_srt"], result["changes"], model=result.get("model", ""))
    return {
        "success": True,
        "transcript": updated,
        "changes": result["changes"],
        "applied_count": result["applied_count"],
        "flagged_count": result["flagged_count"],
    }


@app.post("/api/v1/transcribe/plex")
async def api_transcribe_plex(req: PlexTranscribeRequest):
    """Fetch audio for a Plex item via plex-mcp, transcribe with FunASR, store draft SRT."""
    import speech_mcp.transcript_depot as depot
    from speech_mcp.tools.subtitles import fetch_audio_and_transcribe

    if not funasr_provider:
        raise HTTPException(status_code=503, detail="FunASR not configured — set FUNASR_ENABLED=true")
    try:
        result = await fetch_audio_and_transcribe(
            plex_mcp_url=req.plex_mcp_url,
            media_key=req.media_key,
            language=req.language,
            funasr=funasr_provider,
        )
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "plex fetch failed"))
        row = depot.record(
            result["srt"],
            series=req.series,
            season=req.season,
            episode=req.episode,
            title=result.get("title") or "",
            source="plex",
            source_media_key=req.media_key,
            language=req.language,
            model="funasr",
        )
        return {"success": True, "transcript": row, "info": result.get("info", {})}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Plex transcription failed")
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/api/v1/runtime")
async def api_runtime_get():
    from speech_mcp.runtime_config import snapshot

    return {"success": True, **snapshot(), "gpu": _gpu_info()}


class RuntimeDeviceRequest(BaseModel):
    target: str = "funasr"
    device: str = "cpu"


@app.post("/api/v1/runtime")
async def api_runtime_set(req: RuntimeDeviceRequest):
    from speech_mcp.runtime_config import set_funasr_device, set_sherpa_device

    try:
        if req.target == "funasr":
            device = set_funasr_device(req.device)
        elif req.target == "sherpa":
            if sherpa_asr is None:
                raise HTTPException(status_code=503, detail="sherpa-onnx not enabled (SHERPA_ASR_ENABLED=1)")
            device = set_sherpa_device(req.device)
            await asyncio.to_thread(sherpa_asr.set_device, device)
        else:
            raise HTTPException(status_code=400, detail="target must be funasr or sherpa")
        return {"success": True, "target": req.target, "device": device, "gpu": _gpu_info()}
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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
        result = await asyncio.to_thread(
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
    """REST mirror of the agentic workflow. Honest failure: real orchestration
    requires MCP sampling (ctx.sample), which REST cannot provide."""
    return {
        "success": False,
        "goal": req.goal,
        "status": "unavailable",
        "error": "REST orchestration dispatch is not available - sampling requires an MCP client",
        "error_type": "not_implemented",
        "suggestions": [
            "Call the MCP tool agentic_conversation_workflow from a sampling-capable client",
            "Use the Voice Chat page for live conversational interaction",
        ],
    }


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
    if req.type == "timer" and req.action == "cancel":
        from speech_mcp.state import _timers as _timer_store

        matched = {k: v for k, v in _timer_store.items() if req.label in k}
        for k, v in matched.items():
            v.cancel()
            del _timer_store[k]
        return {"success": True, "cancelled": list(matched.keys())}
    if req.type == "weather" and req.action == "query":
        from speech_mcp.tools.utility import _weather_report

        return await _weather_report(req.label if req.label != "Default" else "Vienna")
    return {
        "success": False,
        "error": f"Action '{req.action}' / type '{req.type}' not supported",
        "error_type": "not_implemented",
    }


@app.post("/api/v1/action")
async def api_action(req: ActionRequest):
    params = req.params or {}
    return {
        "success": False,
        "error": "IoT actions require the devices-mcp bridge, which is not wired in this server",
        "error_type": "requires_bridge",
        "action_type": req.action_type,
        "params": params,
        "suggestions": [
            "Call the MCP tool trigger_action for orchestrated handling",
            "Configure devices-mcp and wire a real bridge",
        ],
    }


# ---------------------------------------------------------------------------
# Voice intelligence REST surface (memory / macros / translate / analytics /
# sound events / voice bank / chat / readout)
# ---------------------------------------------------------------------------


class MemoryStoreRequest(BaseModel):
    text: str
    kind: str = "note"
    speaker: str = ""
    topic: str = ""
    provider: str = ""


class MacroRequest(BaseModel):
    phrase: str
    label: str = ""
    actions: list[dict] | None = None


class MacroRunRequest(BaseModel):
    phrase: str


class TranslateRequest(BaseModel):
    text: str = ""
    target_language: str
    provider: str = "ollama"
    model: str | None = None
    base_url: str | None = None


class ChatRequest(BaseModel):
    message: str
    personality: str = "custom"
    skill: str | None = None
    provider: str = "ollama"
    model: str | None = None
    base_url: str | None = None
    remember: bool = True


class VoiceBankRequest(BaseModel):
    name: str
    provider: str = "elevenlabs"
    voice_id: str = ""
    source: str = "custom"
    description: str = ""


class ReadAloudRequest(BaseModel):
    text: str | None = None
    file_path: str | None = None
    provider: str = "windows"
    voice_id: str = "default"


@app.get("/api/v1/memory")
async def api_memory_list(limit: int = 20, kind: str | None = None):
    from speech_mcp.storage import memory_recall

    episodes = memory_recall(limit=limit, kind=kind)
    return {"success": True, "episodes": episodes, "count": len(episodes)}


@app.post("/api/v1/memory")
async def api_memory_store(req: MemoryStoreRequest):
    from speech_mcp.storage import memory_store

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    episode = memory_store(req.text.strip(), kind=req.kind, speaker=req.speaker, topic=req.topic, provider=req.provider)
    return {"success": True, "episode": episode}


@app.get("/api/v1/memory/search")
async def api_memory_search(q: str = "", limit: int = 10):
    from speech_mcp.storage import memory_search

    if not q.strip():
        return {"success": True, "results": [], "count": 0}
    results = memory_search(q, limit=limit)
    return {"success": True, "results": results, "count": len(results)}


@app.get("/api/v1/memory/stats")
async def api_memory_stats():
    from speech_mcp.storage import memory_stats

    return {"success": True, **memory_stats()}


@app.get("/api/v1/analytics")
async def api_analytics(hours: float = 24.0):
    from speech_mcp.storage import analytics_prune, analytics_summary

    analytics_prune()
    return {"success": True, **analytics_summary(hours=hours)}


@app.get("/api/v1/macros")
async def api_macros_list():
    from speech_mcp.storage import macro_list

    return {"success": True, "macros": macro_list()}


@app.post("/api/v1/macros")
async def api_macros_create(req: MacroRequest):
    from speech_mcp.storage import macro_create

    if not req.phrase.strip():
        raise HTTPException(status_code=400, detail="phrase is required")
    res = macro_create(req.phrase, label=req.label, actions=req.actions or [])
    if "error" in res:
        raise HTTPException(status_code=409, detail=res["error"])
    return {"success": True, **res}


@app.delete("/api/v1/macros")
async def api_macros_delete(phrase: str = ""):
    from speech_mcp.storage import macro_delete

    removed = macro_delete(phrase) if phrase else False
    return {"success": True, "phrase": phrase, "removed": removed}


@app.post("/api/v1/macros/run")
async def api_macros_run(req: MacroRunRequest):
    from speech_mcp.storage import macro_get
    from speech_mcp.tools.macros import _run_actions

    macro = macro_get(req.phrase)
    if macro is None:
        raise HTTPException(status_code=404, detail=f"no macro for phrase '{req.phrase}'")
    outcome = await _run_actions(macro.get("actions", []), _speak, _weather_report)
    return {"success": outcome["ok_all"], "phrase": req.phrase, **outcome}


@app.post("/api/v1/translate")
async def api_translate(req: TranslateRequest):
    from speech_mcp.tools.translate import _llm_translate

    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    translation = await _llm_translate(req.text, req.target_language, req.provider, req.model, req.base_url)
    if translation.startswith("Generation failed"):
        raise HTTPException(status_code=503, detail=translation)
    return {"success": True, "text": req.text, "translation": translation, "provider": req.provider}


@app.post("/api/v1/sound/events")
async def api_sound_events(request: Request):
    from speech_mcp.tools.sound_events import detect_events

    body = await request.body()
    if not body:
        raise HTTPException(status_code=400, detail="Empty audio body")
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
            tmp.write(body)
        return detect_events(tmp_path)
    except Exception as e:
        logger.exception("sound event analysis failed")
        raise HTTPException(status_code=500, detail=str(e)) from e
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


@app.get("/api/v1/voicebank")
async def api_voicebank_list():
    from speech_mcp.storage import voice_profile_list

    return {"success": True, "profiles": voice_profile_list()}


@app.post("/api/v1/voicebank")
async def api_voicebank_register(req: VoiceBankRequest):
    from speech_mcp.storage import voice_profile_register

    if not req.name.strip():
        raise HTTPException(status_code=400, detail="name is required")
    res = voice_profile_register(req.name, req.provider, req.voice_id, req.source, req.description)
    if "error" in res:
        raise HTTPException(status_code=409, detail=res["error"])
    return {"success": True, **res}


@app.delete("/api/v1/voicebank")
async def api_voicebank_delete(name: str = ""):
    from speech_mcp.storage import voice_profile_delete

    removed = voice_profile_delete(name) if name else False
    return {"success": True, "name": name, "removed": removed}


@app.get("/api/v1/personas")
async def api_personas():
    from speech_mcp.personas import PERSONAS

    return {"success": True, "personas": PERSONAS}


@app.post("/api/v1/chat")
async def api_chat(req: ChatRequest):
    from speech_mcp.providers.local import local_llm_provider
    from speech_mcp.tools.chat import compose_system

    if not req.message.strip():
        raise HTTPException(status_code=400, detail="message is required")
    system = compose_system(req.personality, req.skill)
    base = req.base_url or ("http://localhost:11434" if req.provider == "ollama" else "http://localhost:1234")
    effective = req.model or ("llama3" if req.provider == "ollama" else "default")
    reply = await local_llm_provider.generate(
        provider=req.provider, base_url=base, model=effective, prompt=req.message.strip(), system=system
    )
    if reply.startswith("Generation failed"):
        raise HTTPException(status_code=503, detail=reply)
    if req.remember:
        from speech_mcp.storage import memory_store

        memory_store(
            req.message.strip(), kind="chat", topic=req.personality, provider=req.provider, meta={"role": "user"}
        )
        memory_store(reply, kind="chat", topic=req.personality, provider=req.provider, meta={"role": "assistant"})
    return {"success": True, "reply": reply, "personality": req.personality, "skill": req.skill}


@app.post("/api/v1/readout")
async def api_readout(provider: str = "windows", voice_id: str = "default"):
    from speech_mcp.tools.readout import _compose_status

    text = _compose_status(_providers)
    spoken = await _speak(text, provider, voice_id)
    return {"success": bool(spoken.get("success")), "text": text, "spoken": spoken}


@app.post("/api/v1/read")
async def api_read_aloud(req: ReadAloudRequest):
    if req.text is None and req.file_path is None:
        raise HTTPException(status_code=400, detail="Provide text or file_path")
    if req.text is not None and req.file_path is not None:
        raise HTTPException(status_code=400, detail="Provide only one of text or file_path")
    if req.file_path is not None:
        try:
            with open(req.file_path, encoding="utf-8") as f:
                req.text = f.read()
        except OSError as e:
            raise HTTPException(status_code=400, detail=f"Cannot read {req.file_path}: {e}") from e
    assert req.text is not None
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Nothing to read - empty input")
    spoken = await _speak(req.text.strip(), req.provider, req.voice_id)
    return {"success": bool(spoken.get("success")), "spoken": spoken, "chars": len(req.text.strip())}


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
