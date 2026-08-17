# -*- mode: python ; coding: utf-8 -*-
# Tauri sidecar — one-file EXE (FunASR/torch excluded; install via uv --extra funasr separately)
from PyInstaller.utils.hooks import copy_metadata

datas = [("src/speech_mcp", "speech_mcp")]
for pkg in ("fastmcp", "fastapi", "uvicorn", "pydantic", "starlette", "prefab_ui", "httpx", "lancedb"):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

a = Analysis(
    ["run_server.py"],
    pathex=["src"],
    binaries=[],

    datas=datas,
    hiddenimports=[

    "_datetime",
        "uvicorn.logging",
        "uvicorn.loops",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols",
        "uvicorn.protocols.http",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.lifespan",
        "uvicorn.lifespan.on",
        "speech_mcp.tools.speech",
        "speech_mcp.tools.stt",
        "speech_mcp.tools.wake_word",
        "speech_mcp.tools.rag",
        "speech_mcp.tools.utility",
        "speech_mcp.tools.agentic",
        "speech_mcp.tools.safety",
        "speech_mcp.tools.monitoring",
        "speech_mcp.tools.ui",
        "speech_mcp.providers.gemini",
        "speech_mcp.providers.local",
        "speech_mcp.providers.windows",
        "speech_mcp.voice_bus",
        "speech_mcp.voice_listener",
    "_strptime",
],
    hookspath=[],

    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "funasr",
        "torch",
        "torchaudio",
        "modelscope",
        "transformers",
        "tensorflow",
        "keras",
    ],
    noarchive=True,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],

    name="speech-mcp-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
)
