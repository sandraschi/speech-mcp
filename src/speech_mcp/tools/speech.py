import asyncio
import logging
import os
import subprocess
import tempfile
from typing import Annotated, Any

import pyttsx3
from elevenlabs.client import ElevenLabs
from fastmcp import Context, FastMCP
from hume import HumeClient
from pydantic import Field

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_MUTATING = {"readonly": False}
_DESTRUCTIVE = {"readonly": False, "destructive": True}


async def _play_wav_file(path: str) -> None:
    """Play a WAV file via winsound (stdlib, zero dependencies)."""
    import winsound

    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Use SND_FILENAME (131072) and SND_NODEFAULT (2) to ensure we don't play a beep on failure
    def _play():
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)

    await asyncio.to_thread(_play)


async def _play_mp3_bytes(data: bytes) -> None:
    """Write MP3 bytes to temp file and play via Windows Media Player."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(data)
    tmp.close()
    try:
        await asyncio.to_thread(
            lambda: subprocess.run(
                ["wmplayer.exe", "/play", "/close", tmp.name],
                check=False,
                capture_output=True,
            )
        )
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass


async def _hume_speak(
    hume_client: HumeClient,
    text: str,
    description: str | None = None,
) -> dict:
    """Synthesize via Hume Octave and play on the server speaker (shared by MCP + REST)."""
    from hume.tts import FormatWav, PostedUtterance

    utterance = PostedUtterance(text=text, description=description) if description else PostedUtterance(text=text)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        def _synth():
            audio = bytearray()
            for chunk in hume_client.tts.synthesize_file(
                utterances=[utterance], format=FormatWav(), strip_headers=False
            ):
                audio.extend(chunk)
            with open(tmp_path, "wb") as f:
                f.write(audio)

        await asyncio.to_thread(_synth)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return {"success": False, "error": "Hume returned empty audio"}

        size = os.path.getsize(tmp_path)
        await _play_wav_file(tmp_path)
        return {"success": True, "provider": "Hume AI Octave", "bytes_played": size, "status": "played"}
    except Exception as e:
        logger.exception("Hume TTS failed")
        return {"success": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


async def _elevenlabs_speak(eleven_client: ElevenLabs, text: str, voice_id: str) -> dict:
    """Synthesize via ElevenLabs and play on the server speaker (shared by MCP + REST)."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name

        def _synth():
            audio = bytearray()
            for chunk in eleven_client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                output_format="mp3_44100_128",
            ):
                audio.extend(chunk)
            with open(tmp_path, "wb") as f:
                f.write(audio)

        await asyncio.to_thread(_synth)

        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            return {"success": False, "error": "ElevenLabs returned empty audio"}

        size = os.path.getsize(tmp_path)
        await _play_mp3_bytes(open(tmp_path, "rb").read())
        return {
            "success": True,
            "provider": "ElevenLabs",
            "voice_id": voice_id,
            "bytes_played": size,
            "status": "played",
        }
    except Exception as e:
        logger.exception("ElevenLabs TTS failed")
        return {"success": False, "error": str(e)}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def register_speech_tools(
    mcp: FastMCP,
    hume_client: HumeClient | None,
    eleven_client: ElevenLabs | None,
    gemini_client: Any | None = None,
    gemma_client: Any | None = None,
    voicestudio_client: Any | None = None,
):

    @mcp.tool(annotations=_MUTATING)
    async def play_audio_file(
        path: Annotated[str, Field(description="Absolute path to the audio file.")],
        ctx: Context | None = None,
    ) -> dict:
        """
        DIAGNOSTIC TOOL: Play an arbitrary audio file on the system speaker.
        Supports .wav and .mp3.

        ## Return Format
        {"success": bool, "path"?: str, "error"?: str}

        ## Examples
        ``play_audio_file(path="C:/sounds/alert.wav")`` -> plays the file and
        returns ``{"success": True, "path": "C:/sounds/alert.wav"}``.
        """
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".wav":
                if ctx:
                    await ctx.info(f"Playing WAV: {path}")
                await _play_wav_file(path)
            elif ext == ".mp3":
                if ctx:
                    await ctx.info(f"Playing MP3: {path}")
                # _play_mp3_bytes expects bytes, so read them
                with open(path, "rb") as f:
                    content = f.read()
                await _play_mp3_bytes(content)
            else:
                return {"success": False, "error": f"Unsupported format: {ext}"}

            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool(annotations=_MUTATING)
    async def text_to_speech(
        text: Annotated[str, Field(description="Text to synthesize and play.")],
        provider: Annotated[
            str, Field(description="TTS provider: windows, hume, gemini, gemma, elevenlabs, voicestudio, qwen, kokoro.")
        ] = "windows",
        voice_id: Annotated[str, Field(description="Provider-specific voice identifier.")] = "default",
        description: Annotated[
            str | None, Field(description="Hume-only: prose style prompt driving Octave prosody.")
        ] = None,
        model: Annotated[
            str | None,
            Field(
                description="Gemini-only: TTS model override (gemini-3.8-flash-tts, "
                "gemini-3.8-flash-lite-tts, gemini-3.1-flash-tts-preview). "
                "Defaults to provider default (3.8 Flash)."
            ),
        ] = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Synthesize speech and play it on the PC speaker.

        Providers:
          - 'windows'     Windows SAPI5, no API key, always works
          - 'hume'        Hume AI Octave REST (HUME_API_KEY). Use `description`
                          for prose style.
          - 'gemini'      Gemini 3.8 Flash / Flash-Lite TTS (GOOGLE_API_KEY).
                          Embed audio tags in text: [excited], [whispers],
                          [laughs], <laughs>/<sigh>/<gasp>, |mhm|/|yeah|.
                          voice_id accepts base 31 voices AND custom/saved
                          3.8 voices. Use `model` to pick Flash vs Flash-Lite.
          - 'gemma'       Gemma 4 Native Local (No API Key).
          - 'elevenlabs'  ElevenLabs (ELEVENLABS_API_KEY). voice_id must be a
                          valid voice ID from your account.
          - 'voicestudio' Local VoiceStudio sidecar (VOICESTUDIO_ENABLED=true).
                          voice_id is a profile_id or voice-bank name. Requires
                          the VoiceStudio backend on VOICESTUDIO_URL.
          - 'qwen'        Qwen3-TTS local (QWEN_TTS_URL endpoint or
                          `uv sync --extra qwen-tts`). No API key.
          - 'kokoro'      Kokoro 82M local (`uv sync --extra kokoro`).
                          No API key, CPU-friendly fallback.

        ## Return Format
        {"success": bool, "provider": str, "voice_id": str}

        ## Examples
        await text_to_speech("Hello world", provider="windows")
        await text_to_speech("[excited] Great job!", provider="gemini", voice_id="Kore")
        await text_to_speech("Dub this at scale", provider="gemini", model="gemini-3.8-flash-lite-tts")
        """
        if ctx:
            await ctx.info(f"TTS [{provider}/{voice_id}]: {text[:60]}")

        # ── Windows SAPI5 ──────────────────────────────────────────────────────
        if provider == "windows":
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth():
                    engine = pyttsx3.init()
                    if voice_id and voice_id != "default":
                        try:
                            voices = engine.getProperty("voices") or []
                            target_id = None
                            for v in voices:
                                vid = getattr(v, "id", "") or ""
                                vname = getattr(v, "name", "") or ""
                                if (
                                    voice_id == vid
                                    or voice_id.lower() in vname.lower()
                                    or voice_id.lower() in vid.lower()
                                ):
                                    target_id = vid
                                    break
                            if not target_id:
                                alias_map = {"heart": "zira", "sky": "hazel", "adam": "david"}
                                alias = alias_map.get(voice_id.lower())
                                if alias:
                                    for v in voices:
                                        if alias in (getattr(v, "name", "") or "").lower():
                                            target_id = getattr(v, "id", "")
                                            break
                            if not target_id and voices:
                                idx = abs(hash(voice_id)) % len(voices)
                                target_id = getattr(voices[idx], "id", None)
                            if target_id:
                                engine.setProperty("voice", target_id)
                        except Exception:
                            pass
                    engine.save_to_file(text, tmp_path)
                    engine.runAndWait()

                await asyncio.to_thread(_synth)

                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return {"success": False, "error": "pyttsx3 produced empty file"}

                size = os.path.getsize(tmp_path)
                await _play_wav_file(tmp_path)
                return {"success": True, "provider": "Windows SAPI5", "bytes_played": size, "status": "played"}
            except Exception as e:
                logger.exception("Windows TTS failed")
                return {"success": False, "error": str(e)}
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

        # ── Hume AI Octave ─────────────────────────────────────────────────────
        elif provider == "hume":
            if not hume_client:
                return {"success": False, "error": "HUME_API_KEY not configured"}
            return await _hume_speak(hume_client, text, description)

        # ── Gemini 3.8 Flash / Flash-Lite TTS ────────────────────────────────────
        elif provider == "gemini":
            gemini = gemini_client
            if not gemini:
                return {
                    "success": False,
                    "error": "Gemini TTS not available - GOOGLE_API_KEY not set.",
                    "recovery": "Add GOOGLE_API_KEY to .env (free at aistudio.google.com/apikey) and restart.",
                }
            effective_voice = voice_id if voice_id and voice_id.lower() != "default" else "Kore"
            _default_model = getattr(gemini, "default_model", None)
            _default_model = _default_model if isinstance(_default_model, str) else "gemini-3.8-flash-tts"
            effective_model = model or _default_model
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth_gemini(_text=text, _voice=effective_voice, _model=effective_model):
                    if _model is None:
                        wav = gemini.synthesize_wav(_text, voice_name=_voice)
                    else:
                        wav = gemini.synthesize_wav(_text, voice_name=_voice, model=_model)
                    with open(tmp_path, "wb") as f:
                        f.write(wav)

                await asyncio.to_thread(_synth_gemini)

                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return {"success": False, "error": "Gemini returned empty audio"}

                size = os.path.getsize(tmp_path)
                await _play_wav_file(tmp_path)
                return {
                    "success": True,
                    "provider": "Gemini 3.8 Flash TTS",
                    "model": effective_model,
                    "voice": effective_voice,
                    "bytes_played": size,
                    "status": "played",
                }
            except Exception as e:
                logger.exception("Gemini TTS failed")
                return {"success": False, "error": str(e)}
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

        # ── Gemma 4 Native Local ──────────────────────────────────────────────
        elif provider == "gemma":
            gemma = gemma_client
            if not gemma:
                return {"success": False, "error": "Gemma provider not initialized"}
            try:
                played = await asyncio.to_thread(lambda: gemma.synthesize_and_play(text, voice=voice_id))
                if not played:
                    return {"success": False, "error": "Gemma/SAPI TTS failed"}
                return {
                    "success": True,
                    "provider": "Gemma 4 (SAPI fallback)",
                    "voice": voice_id,
                    "status": "played",
                    "note": "Gemma native audio not wired; used Windows SAPI5 fallback.",
                }
            except Exception as e:
                logger.exception("Gemma TTS failed")
                return {"success": False, "error": str(e)}

        # ── Qwen3-TTS local ──────────────────────────────────────────────────
        elif provider == "qwen":
            try:
                from speech_mcp.providers.qwen_tts import QwenTTSProvider

                qwen = QwenTTSProvider()
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name

                    def _synth_qwen(_text=text, _voice=voice_id):
                        wav = qwen.synthesize_wav(_text, voice=_voice)
                        with open(tmp_path, "wb") as f:
                            f.write(wav)

                    await asyncio.to_thread(_synth_qwen)
                    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                        return {"success": False, "error": "Qwen-TTS returned empty audio"}
                    size = os.path.getsize(tmp_path)
                    await _play_wav_file(tmp_path)
                    return {
                        "success": True,
                        "provider": "Qwen3-TTS (local)",
                        "voice": voice_id,
                        "bytes_played": size,
                        "status": "played",
                    }
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception as e:
                logger.exception("Qwen-TTS failed")
                return {"success": False, "error": str(e)}

        # ── Kokoro local ─────────────────────────────────────────────────────
        elif provider == "kokoro":
            try:
                from speech_mcp.providers.kokoro import KokoroProvider

                koko = KokoroProvider()
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name

                    def _synth_kokoro(_text=text, _voice=voice_id):
                        wav = koko.synthesize_wav(_text, voice=_voice)
                        with open(tmp_path, "wb") as f:
                            f.write(wav)

                    await asyncio.to_thread(_synth_kokoro)
                    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                        return {"success": False, "error": "Kokoro returned empty audio"}
                    size = os.path.getsize(tmp_path)
                    await _play_wav_file(tmp_path)
                    return {
                        "success": True,
                        "provider": "Kokoro (local)",
                        "voice": voice_id,
                        "bytes_played": size,
                        "status": "played",
                    }
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception as e:
                logger.exception("Kokoro TTS failed")
                return {"success": False, "error": str(e)}

        # ── ElevenLabs ─────────────────────────────────────────────────────────
        elif provider == "elevenlabs":
            if not eleven_client:
                return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}
            if not voice_id or voice_id == "default":
                return {
                    "success": False,
                    "error": (
                        "voice_id required for ElevenLabs - use manage_voice_clones "
                        "action='list' to see available voices"
                    ),
                }
            return await _elevenlabs_speak(eleven_client, text, voice_id)

        # ── VoiceStudio local sidecar ────────────────────────────────────────
        elif provider == "voicestudio":
            if not voicestudio_client:
                return {
                    "success": False,
                    "error": "VoiceStudio not configured - set VOICESTUDIO_ENABLED=true and restart.",
                    "recovery": "Start the VoiceStudio backend (Electron app or Docker) on VOICESTUDIO_URL.",
                }
            from speech_mcp.storage import voice_profile_get

            profile_id = voice_id
            if voice_id and voice_id != "default":
                profile = voice_profile_get(voice_id)
                if profile and profile.get("provider") == "voicestudio":
                    profile_id = profile.get("voice_id") or voice_id
            try:
                result = await voicestudio_client.synthesize(text, profile_id)
                if not result.get("success"):
                    return result
                wav_bytes = result.get("wav_bytes")
                if not wav_bytes:
                    return {"success": False, "provider": "voicestudio", "error": "VoiceStudio returned empty audio"}
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(wav_bytes)
                    tmp_path = tmp.name
                try:
                    await _play_wav_file(tmp_path)
                finally:
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass
                return {
                    "success": True,
                    "provider": "VoiceStudio (local)",
                    "voice": profile_id,
                    "bytes_played": len(wav_bytes),
                    "status": "played",
                }
            except Exception as e:
                logger.exception("VoiceStudio TTS failed")
                return {"success": False, "provider": "voicestudio", "error": str(e)}

        else:
            return {
                "success": False,
                "error": (
                    f"Unknown provider '{provider}'. "
                    "Use 'windows', 'hume', 'gemini', 'gemma', 'elevenlabs', 'voicestudio', 'qwen', or 'kokoro'."
                ),
            }

    @mcp.tool(annotations=_MUTATING)
    async def text_to_dialogue(
        lines: list[dict],
        provider: Annotated[str, Field(description="Dialogue provider: elevenlabs or gemini.")] = "elevenlabs",
        model: Annotated[
            str | None,
            Field(
                description="Gemini-only: TTS model override (gemini-3.8-flash-tts, "
                "gemini-3.8-flash-lite-tts, gemini-3.1-flash-tts-preview)."
            ),
        ] = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Multi-voice dialogue synthesis - plays on the PC speaker.

        Providers:
          - 'elevenlabs'  ElevenLabs text_to_dialogue (ELEVENLABS_API_KEY).
                          ``lines`` is ``[{text, voice_id}]`` (max 10 voices).
          - 'gemini'      Gemini 3.8 two-speaker staging (GOOGLE_API_KEY).
                          ``lines`` is ``[{text, voice_id, speaker?}]`` -
                          voice_id accepts base 31 AND custom/saved 3.8
                          voices; speaker labels the script turn. Audio tags
                          (``[laughs]``, ``<sigh>``, ``|mhm|``) allowed per line.

        ## Return Format
        ``{"success": bool, "provider": str, "lines": int, "voices_used": int,
        "bytes_played": int, "status": "played"}`` - or ``{"success": False,
        "error": str}`` on failure.

        ## Examples
        ``text_to_dialogue(lines=[{"text": "Hello.", "voice_id": "v1"},
        {"text": "Hi.", "voice_id": "v2"}])`` -> ElevenLabs dialogue.
        ``text_to_dialogue(lines=[{"text": "Welcome.", "voice_id": "Aoede", "speaker": "Ava"},
        {"text": "Thanks!", "voice_id": "Charon", "speaker": "Ben"}], provider="gemini")``
        -> Gemini two-speaker scene.
        """
        if not lines:
            return {"success": False, "error": "lines list is empty"}
        if len(lines) > 10:
            return {"success": False, "error": "max 10 dialogue lines"}

        if provider == "gemini":
            gemini = gemini_client
            if not gemini:
                return {
                    "success": False,
                    "error": "Gemini TTS not available - GOOGLE_API_KEY not set.",
                    "recovery": "Add GOOGLE_API_KEY to .env (free at aistudio.google.com/apikey) and restart.",
                }
            try:
                turns = []
                for i, line in enumerate(lines):
                    text = str(line.get("text") or "").strip()
                    if not text:
                        return {"success": False, "error": f"line {i} has empty text"}
                    turns.append(
                        {
                            "speaker": str(line.get("speaker") or f"Speaker {i + 1}"),
                            "text": text,
                            "voice": str(line.get("voice_id") or line.get("voice") or "Kore"),
                        }
                    )
                _default = getattr(gemini, "default_model", None)
                effective_model = model or (_default if isinstance(_default, str) else "gemini-3.8-flash-tts")
                tmp_path = None
                try:
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp_path = tmp.name

                    def _synth_gemini_dialogue():
                        wav = gemini.synthesize_dialogue_wav(turns, model=effective_model)
                        with open(tmp_path, "wb") as f:
                            f.write(wav)

                    await asyncio.to_thread(_synth_gemini_dialogue)

                    if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                        return {"success": False, "error": "Gemini dialogue returned empty audio"}
                    size = os.path.getsize(tmp_path)
                    await _play_wav_file(tmp_path)
                    return {
                        "success": True,
                        "provider": "Gemini 3.8 dialogue",
                        "model": effective_model,
                        "lines": len(turns),
                        "voices_used": len({t["voice"] for t in turns}),
                        "bytes_played": size,
                        "status": "played",
                    }
                finally:
                    if tmp_path and os.path.exists(tmp_path):
                        try:
                            os.remove(tmp_path)
                        except OSError:
                            pass
            except Exception as e:
                logger.exception("Gemini dialogue failed")
                return {"success": False, "error": str(e)}

        if provider != "elevenlabs":
            return {"success": False, "error": f"Unknown dialogue provider '{provider}'. Use 'elevenlabs' or 'gemini'."}
        if not eleven_client:
            return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}

        from elevenlabs import DialogueInput

        el = eleven_client
        try:
            inputs = [DialogueInput(text=line["text"], voice_id=line["voice_id"]) for line in lines]
        except KeyError as e:
            return {"success": False, "error": f"each line needs text + voice_id (missing {e})"}

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            def _synth_dialogue():
                audio = bytearray()
                for chunk in el.text_to_dialogue.convert(
                    inputs=inputs,
                    output_format="mp3_44100_128",
                ):
                    audio.extend(chunk)
                with open(tmp_path, "wb") as f:
                    f.write(audio)

            await asyncio.to_thread(_synth_dialogue)

            if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                return {"success": False, "error": "ElevenLabs dialogue returned empty audio"}

            size = os.path.getsize(tmp_path)
            await _play_mp3_bytes(open(tmp_path, "rb").read())
            return {
                "success": True,
                "provider": "ElevenLabs text_to_dialogue",
                "lines": len(lines),
                "voices_used": len({line["voice_id"] for line in lines}),
                "bytes_played": size,
                "status": "played",
            }
        except Exception as e:
            logger.exception("ElevenLabs dialogue failed")
            return {"success": False, "error": str(e)}
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    @mcp.tool(annotations=_DESTRUCTIVE)
    async def manage_voice_clones(
        action: str,
        provider: str = "elevenlabs",
        name: str | None = None,
        audio_path: str | None = None,
        voice_id: str | None = None,
        language: str = "en",
        ctx: Context | None = None,
    ) -> dict:
        """
        Manage voice clones across providers.

        Actions:
          list    - list all voices in your account
          clone   - create an Instant Voice Clone from a local audio file
                    (requires name + audio_path)
          delete  - delete a voice by voice_id

        ## Return Format
        ``{"success": bool, "action": str, "provider": str, ...}`` - ``list``
        returns ``voices``; ``clone`` returns ``voice_id``; ``delete`` returns
        ``deleted``. ``{"success": False, "error": str}`` on failure.

        ## Examples
        ``manage_voice_clones(action="list", provider="elevenlabs")`` -> lists
        your ElevenLabs voices.
        ``manage_voice_clones(action="clone", name="Benny",
        audio_path="C:/samples/benny.wav")`` -> creates an IVC clone and returns
        its ``voice_id``.
        """
        if ctx:
            await ctx.info(f"Voice management: {action} via {provider}")

        if provider == "elevenlabs":
            el = eleven_client
            if not el:
                return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}

            if action == "list":
                try:
                    voices = await asyncio.to_thread(lambda: el.voices.get_all())
                    return {
                        "success": True,
                        "provider": "ElevenLabs",
                        "voices": [
                            {"id": v.voice_id, "name": v.name, "category": getattr(v, "category", "unknown")}
                            for v in getattr(voices, "voices", [])
                        ],
                        "count": len(getattr(voices, "voices", [])),
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}

            elif action == "clone":
                if not name or not audio_path:
                    return {"success": False, "error": "name and audio_path required for clone"}
                if not os.path.exists(audio_path):
                    return {"success": False, "error": f"File not found: {audio_path}"}
                try:

                    def _clone():
                        with open(audio_path, "rb") as f:
                            return el.voices.ivc.create(
                                name=name,
                                files=[f],
                                description=f"IVC clone from {os.path.basename(audio_path)}",
                            )

                    result = await asyncio.to_thread(_clone)
                    return {
                        "success": True,
                        "voice_id": result.voice_id,
                        "name": name,
                        "status": "cloned",
                        "note": "Use this voice_id with text_to_speech provider='elevenlabs'",
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}

            elif action == "delete":
                if not voice_id:
                    return {"success": False, "error": "voice_id required for delete"}
                try:
                    await asyncio.to_thread(lambda: el.voices.delete(voice_id))
                    return {"success": True, "deleted": voice_id}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            return {"success": False, "error": f"Unknown action '{action}' for elevenlabs"}

        elif provider == "hume":
            hume = hume_client
            if not hume:
                return {"success": False, "error": "HUME_API_KEY not configured"}
            if action == "list":
                try:
                    voices = await asyncio.to_thread(lambda: list(hume.tts.voices.list(provider="HUME_AI")))
                    return {
                        "success": True,
                        "provider": "Hume AI",
                        "voices": [{"id": v.id, "name": v.name} for v in voices],
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": f"Action '{action}' not implemented for Hume"}

        elif provider == "voicestudio":
            if not voicestudio_client:
                return {
                    "success": False,
                    "error": "VoiceStudio not configured - set VOICESTUDIO_ENABLED=true and restart.",
                }
            if action == "list":
                return await voicestudio_client.list_voices()
            if action == "clone":
                if not name or not audio_path:
                    return {"success": False, "error": "name and audio_path required for clone"}
                result = await voicestudio_client.clone_voice(name, audio_path)
                if result.get("success"):
                    result["note"] = "Use profile_id with text_to_speech provider='voicestudio'"
                return result
            return {"success": False, "error": f"Action '{action}' not implemented for voicestudio (use list/clone)"}

        return {"success": False, "error": f"Unknown provider '{provider}'"}
