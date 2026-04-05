import base64
import json
import logging
import math
import os
import struct
import tempfile
from typing import Any

import anyio
import pyttsx3
import websockets
from elevenlabs.client import ElevenLabs
from fastapi import WebSocket, WebSocketDisconnect
from pythonosc import udp_client

logger = logging.getLogger(__name__)

OSC_HOST = "127.0.0.1"
OSC_PORT = 9000
osc_client = udp_client.SimpleUDPClient(OSC_HOST, OSC_PORT)


def calculate_amplitude(audio_b64: str) -> float:
    try:
        audio_data = base64.b64decode(audio_b64)
        count = len(audio_data) // 2
        if count == 0:
            return 0.0
        samples = struct.unpack(f"<{count}h", audio_data)
        rms = math.sqrt(sum(s**2 for s in samples) / count)
        return min(1.0, rms / 8000.0)
    except Exception:
        return 0.0


async def handle_websocket_stream(
    websocket: WebSocket,
    eleven_client: ElevenLabs | None,
    hume_client: Any | None = None,
):
    await websocket.accept()

    # Auth check
    token = websocket.query_params.get("token")
    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if expected and token != expected:
        await websocket.close(code=1008, reason="Unauthorized")
        return

    provider = websocket.query_params.get("provider", "windows")
    voice_id = websocket.query_params.get("voice", "default")

    try:
        if provider == "windows":
            await _handle_windows(websocket)

        elif provider == "elevenlabs":
            if not eleven_client:
                await websocket.close(code=1008, reason="ElevenLabs key not configured")
                return
            await _handle_elevenlabs(websocket, eleven_client, voice_id)

        elif provider == "hume":
            api_key = os.getenv("HUME_API_KEY")
            if not api_key:
                await websocket.close(code=1008, reason="HUME_API_KEY not configured")
                return
            await _handle_hume(websocket, api_key)

        else:
            await websocket.close(code=1008, reason=f"Unknown provider: {provider}")

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.exception(f"WebSocket stream error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


async def _handle_windows(websocket: WebSocket):
    """
    Protocol:
      client -> server: {"type": "tts", "text": "..."}
      server -> client: raw WAV bytes (chunks)
      server closes connection when done
      client onclose -> decode accumulated bytes -> play
    """
    tmp_path = None
    try:
        msg = await websocket.receive_json()
        text = msg.get("text", "")
        if not text:
            await websocket.close()
            return

        logger.info(f"Windows TTS: '{text[:60]}'")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        # pyttsx3 is synchronous COM — run in thread pool
        def _synth():
            engine = pyttsx3.init()
            engine.save_to_file(text, tmp_path)
            engine.runAndWait()

        await anyio.to_thread.run_sync(_synth)

        # Verify file was written
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            logger.error(f"pyttsx3 produced empty file at {tmp_path}")
            await websocket.close(code=1011, reason="TTS synthesis failed")
            return

        logger.info(f"WAV size: {os.path.getsize(tmp_path)} bytes, streaming...")

        with open(tmp_path, "rb") as f:
            while chunk := f.read(8192):
                await websocket.send_bytes(chunk)

        # Close cleanly — this is what triggers onclose on the frontend
        await websocket.close()

    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


async def _handle_elevenlabs(websocket: WebSocket, client: ElevenLabs, voice_id: str):
    """
    Protocol: same as windows — receive text, send audio chunks, close.
    ElevenLabs returns MP3 chunks which AudioContext can decode.
    """
    msg = await websocket.receive_json()
    text = msg.get("text", "")
    if not text:
        await websocket.close()
        return

    logger.info(f"ElevenLabs TTS: voice={voice_id} text='{text[:60]}'")

    audio_stream = client.generate(
        text=text,
        voice=voice_id,
        model="eleven_turbo_v2_5",
        stream=True,
    )
    for chunk in audio_stream:
        if chunk:
            await websocket.send_bytes(chunk)

    await websocket.close()


async def _handle_hume(websocket: WebSocket, api_key: str):
    """Bidirectional proxy to Hume EVI with OSC lip-flap."""
    hume_url = f"wss://api.hume.ai/v0/evi/chat?api_key={api_key}"

    async with websockets.connect(
        hume_url,
        extra_headers={"X-Hume-Client-Type": "Speech-MCP-Proxy"},
    ) as hume_ws:

        async def hume_to_client():
            async for message in hume_ws:
                data = json.loads(message)
                if data.get("type") == "audio_output":
                    amp = calculate_amplitude(data.get("data", ""))
                    flap = min(1.0, amp * 1.5)
                    osc_client.send_message("/avatar/parameters/MouthOpen", flap if flap > 0.05 else 0.0)
                await websocket.send_text(message)

        async def client_to_hume():
            while True:
                message = await websocket.receive_text()
                await hume_ws.send(message)

        async with anyio.create_task_group() as tg:
            tg.start_soon(hume_to_client)
            tg.start_soon(client_to_hume)
