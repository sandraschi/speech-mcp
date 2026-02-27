import asyncio
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from fastapi import Depends, FastAPI, HTTPException, WebSocket, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastmcp import FastMCP
from hume import HumeClient

from speech_mcp.state import _timers, get_store
from speech_mcp.streaming import handle_websocket_stream
from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.utility import register_utility_tools

# Load environment variables
load_dotenv()
HUME_API_KEY = os.getenv("HUME_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle initialization and cleanup."""
    get_store()
    yield
    for task in _timers.values():
        task.cancel()


# Initialize FastAPI (webapp mode only)
app = FastAPI(title="Speech MCP Stream Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:10761", "http://127.0.0.1:10761"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FastMCP server (shared for both stdio and webapp modes)
mcp = FastMCP("speech-mcp")

# Clients (only initialized when API keys are present)
hume_client = HumeClient(api_key=HUME_API_KEY) if HUME_API_KEY else None
eleven_client = ElevenLabs(api_key=ELEVENLABS_API_KEY) if ELEVENLABS_API_KEY else None

# Register Modular Tools
register_speech_tools(mcp, hume_client, eleven_client)
register_agentic_tools(mcp, hume_client)
register_utility_tools(mcp)
register_monitoring_tools(mcp)
register_rag_tools(mcp)
register_safety_tools(mcp)

# Security: API Key requirement
api_key_header = APIKeyHeader(name="X-Speech-MCP-Auth", auto_error=False)


async def get_api_key(api_key: str = Depends(api_key_header)):
    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if not expected:
        # If not configured, we allow access but log a warning (developer mode)
        return True
    if api_key == expected:
        return api_key
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Missing or invalid X-Speech-MCP-Auth header",
    )


# --- REST API Routes (webapp mode) ---


@app.get("/api/v1/health")
async def health_check(_: str = Depends(get_api_key)):
    return {
        "status": "healthy",
        "version": "0.2.1",
        "modular": True,
        "mcp_server": "online",
        "rag_sources": get_store().list_sources(),
        "active_timers": len(_timers),
        "providers": {
            "hume": bool(hume_client),
            "elevenlabs": bool(eleven_client),
            "windows": True,
        },
    }


@app.get("/api/v1/search")
async def api_search(q: str = ""):
    results = get_store().search(q, limit=10)
    return [
        {
            "filename": r["metadata"].get("filename", "unknown"),
            "score": max(0.0, 1.0 - r.get("_distance", 0.0)),
            "content": r["content"],
        }
        for r in results
    ]


@app.get("/api/v1/voices")
async def api_voices():
    """Provider transparency endpoint — lists available TTS providers."""
    providers = []
    if hume_client:
        providers.append({"name": "hume", "status": "available", "voices": ["ito", "kora"]})
    if eleven_client:
        providers.append({"name": "elevenlabs", "status": "available", "voices": []})
    providers.append({"name": "windows", "status": "available", "voices": ["default"]})
    return {"providers": providers}


# --- WebSocket Stream Endpoint (webapp mode) ---


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """SOTA Side-channel audio stream proxy."""
    await handle_websocket_stream(websocket, eleven_client, hume_client)


if __name__ == "__main__":
    # stdio mode — for Claude Desktop and other MCP clients
    asyncio.run(mcp.run_stdio_async())
