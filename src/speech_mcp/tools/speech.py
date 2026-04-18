import logging
import os
import subprocess
import tempfile
from typing import Any

import anyio
import pyttsx3
from elevenlabs.client import ElevenLabs
from fastmcp import Context, FastMCP
from hume import HumeClient

logger = logging.getLogger(__name__)


async def _play_wav_file(path: str) -> None:
    """Play a WAV file via winsound (stdlib, zero dependencies)."""
    import winsound
    import anyio

    if not os.path.exists(path):
        raise FileNotFoundError(f"Audio file not found: {path}")

    # Use SND_FILENAME (131072) and SND_NODEFAULT (2) to ensure we don't play a beep on failure
    def _play():
        winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)

    await anyio.to_thread.run_sync(_play)


async def _play_mp3_bytes(data: bytes) -> None:
    """Write MP3 bytes to temp file and play via Windows Media Player."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp.write(data)
    tmp.close()
    try:
        await anyio.to_thread.run_sync(
            lambda: subprocess.run(
                ["wmplayer.exe", "/play", "/close", tmp.name],
                check=False, capture_output=True,
            )
        )
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass


def register_speech_tools(
    mcp: FastMCP,
    hume_client: HumeClient | None,
    eleven_client: ElevenLabs | None,
    gemini_client: Any | None = None,
):

    @mcp.tool()
    async def play_audio_file(path: str, ctx: Context = None) -> dict:
        """
        DIAGNOSTIC TOOL: Play an arbitrary audio file on the system speaker.
        Supports .wav and .mp3.

        Args:
            path: Absolute path to the audio file.
        """
        if not os.path.exists(path):
            return {"success": False, "error": f"File not found: {path}"}

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".wav":
                if ctx:
                    ctx.info(f"Playing WAV: {path}")
                await _play_wav_file(path)
            elif ext == ".mp3":
                if ctx:
                    ctx.info(f"Playing MP3: {path}")
                # _play_mp3_bytes expects bytes, so read them
                with open(path, "rb") as f:
                    content = f.read()
                await _play_mp3_bytes(content)
            else:
                return {"success": False, "error": f"Unsupported format: {ext}"}

            return {"success": True, "path": path}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @mcp.tool()
    async def text_to_speech(
        text: str,
        provider: str = "windows",
        voice_id: str = "default",
        description: str | None = None,
        ctx: Context = None,
    ) -> dict:
        """
        Synthesize speech and play it on the PC speaker.

        Providers:
          - 'windows'     Windows SAPI5, no API key, always works
          - 'hume'        Hume AI Octave REST (HUME_API_KEY). Use `description`
                          for prose style: "warm, scholarly, melancholic"
          - 'gemini'      Gemini 3.1 Flash TTS (GOOGLE_API_KEY). Embed audio
                          tags in text: [excited], [whispers], [laughs], etc.
                          Open vocabulary — any emotion in English works.
          - 'elevenlabs'  ElevenLabs (ELEVENLABS_API_KEY). voice_id must be a
                          valid voice ID from your account. Use
                          manage_voice_clones to list available voices.

        Args:
            text:        Text to speak.
            provider:    See above. Default: 'windows'.
            voice_id:    Provider-specific voice identifier:
                         - hume: named voice or 'default' (dynamic generation)
                         - gemini: prebuilt voice name e.g. Kore, Aoede, Charon
                         - elevenlabs: voice ID string from your EL account
                         - windows: ignored
            description: Hume only — prose style prompt driving Octave prosody.
            ctx:         FastMCP context for logging.
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
                    engine.save_to_file(text, tmp_path)
                    engine.runAndWait()

                await anyio.to_thread.run_sync(_synth)

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

            from hume.tts import FormatWav, PostedUtterance, PostedUtteranceVoiceWithName

            utt_kwargs: dict = {"text": text}
            if description:
                utt_kwargs["description"] = description
            if voice_id and voice_id.lower() != "default":
                utt_kwargs["voice"] = PostedUtteranceVoiceWithName(name=voice_id, provider="HUME_AI")

            utterance = PostedUtterance(**utt_kwargs)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth_hume():
                    audio = bytearray()
                    for chunk in hume_client.tts.synthesize_file(
                        utterances=[utterance], format=FormatWav(), strip_headers=False
                    ):
                        audio.extend(chunk)
                    with open(tmp_path, "wb") as f:
                        f.write(audio)

                await anyio.to_thread.run_sync(_synth_hume)

                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return {"success": False, "error": "Hume returned empty audio"}

                size = os.path.getsize(tmp_path)
                await _play_wav_file(tmp_path)
                return {
                    "success": True, "provider": "Hume AI Octave",
                    "voice": voice_id, "description_used": description,
                    "bytes_played": size, "status": "played",
                }
            except Exception as e:
                logger.exception("Hume TTS failed")
                return {"success": False, "error": str(e)}
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

        # ── Gemini 3.1 Flash TTS ───────────────────────────────────────────────
        elif provider == "gemini":
            if not gemini_client:
                return {
                    "success": False,
                    "error": "Gemini TTS not available — GOOGLE_API_KEY not set.",
                    "recovery": "Add GOOGLE_API_KEY to .env (free at aistudio.google.com/apikey) and restart.",
                }
            effective_voice = voice_id if voice_id and voice_id.lower() != "default" else "Kore"
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth_gemini():
                    wav = gemini_client.synthesize_wav(text, voice_name=effective_voice)
                    with open(tmp_path, "wb") as f:
                        f.write(wav)

                await anyio.to_thread.run_sync(_synth_gemini)

                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return {"success": False, "error": "Gemini returned empty audio"}

                size = os.path.getsize(tmp_path)
                await _play_wav_file(tmp_path)
                return {
                    "success": True, "provider": "Gemini 3.1 Flash TTS",
                    "model": "gemini-3.1-flash-tts-preview",
                    "voice": effective_voice, "bytes_played": size, "status": "played",
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

        # ── ElevenLabs ─────────────────────────────────────────────────────────
        elif provider == "elevenlabs":
            if not eleven_client:
                return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}
            if not voice_id or voice_id == "default":
                return {
                    "success": False,
                    "error": "voice_id required for ElevenLabs — use manage_voice_clones action='list' to see available voices",
                }
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name

                def _synth_el():
                    audio = bytearray()
                    for chunk in eleven_client.text_to_speech.convert(
                        voice_id=voice_id,
                        text=text,
                        output_format="mp3_44100_128",
                    ):
                        audio.extend(chunk)
                    with open(tmp_path, "wb") as f:
                        f.write(audio)

                await anyio.to_thread.run_sync(_synth_el)

                if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
                    return {"success": False, "error": "ElevenLabs returned empty audio"}

                size = os.path.getsize(tmp_path)
                await _play_mp3_bytes(open(tmp_path, "rb").read())
                return {
                    "success": True, "provider": "ElevenLabs",
                    "voice_id": voice_id, "bytes_played": size, "status": "played",
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

        else:
            return {
                "success": False,
                "error": f"Unknown provider '{provider}'. Use 'windows', 'hume', 'gemini', or 'elevenlabs'.",
            }

    @mcp.tool()
    async def text_to_dialogue(
        lines: list[dict],
        ctx: Context = None,
    ) -> dict:
        """
        Multi-voice dialogue synthesis via ElevenLabs — plays on the PC speaker.

        Each line is assigned a different voice ID, producing natural conversational
        audio with consistent pacing in a single API call (up to 10 voices).

        Requires ELEVENLABS_API_KEY and valid voice IDs. Use manage_voice_clones
        action='list' provider='elevenlabs' to see your available voices.

        Args:
            lines: List of {text, voice_id} dicts. Example:
                   [
                     {"text": "Good morning, Benny.", "voice_id": "abc123"},
                     {"text": "Woof.", "voice_id": "def456"}
                   ]

        Example use:
            Ask two different cloned voices to have a short philosophical exchange.
        """
        if not eleven_client:
            return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}

        if not lines:
            return {"success": False, "error": "lines list is empty"}

        from elevenlabs import DialogueInput

        inputs = [DialogueInput(text=line["text"], voice_id=line["voice_id"]) for line in lines]

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            def _synth_dialogue():
                audio = bytearray()
                for chunk in eleven_client.text_to_dialogue.convert(
                    inputs=inputs,
                    output_format="mp3_44100_128",
                ):
                    audio.extend(chunk)
                with open(tmp_path, "wb") as f:
                    f.write(audio)

            await anyio.to_thread.run_sync(_synth_dialogue)

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

    @mcp.tool()
    async def manage_voice_clones(
        action: str,
        provider: str = "elevenlabs",
        name: str | None = None,
        audio_path: str | None = None,
        voice_id: str | None = None,
        language: str = "en",
        ctx: Context = None,
    ) -> dict:
        """
        Manage voice clones across providers.

        Actions:
          list    — list all voices in your account
          clone   — create an Instant Voice Clone from a local audio file
                    (requires name + audio_path)
          delete  — delete a voice by voice_id

        Args:
            action:     'list', 'clone', or 'delete'
            provider:   'elevenlabs' or 'hume'
            name:       Display name for a new clone
            audio_path: Absolute path to audio file for cloning (WAV/MP3/M4A)
            voice_id:   Target voice ID for delete
            language:   Language code for IVC, e.g. 'en', 'de', 'ja'
        """
        if ctx:
            await ctx.info(f"Voice management: {action} via {provider}")

        if provider == "elevenlabs":
            if not eleven_client:
                return {"success": False, "error": "ELEVENLABS_API_KEY not configured"}

            if action == "list":
                try:
                    voices = await anyio.to_thread.run_sync(
                        lambda: eleven_client.voices.get_all()
                    )
                    return {
                        "success": True,
                        "provider": "ElevenLabs",
                        "voices": [
                            {"id": v.voice_id, "name": v.name, "category": getattr(v, "category", "unknown")}
                            for v in voices.voices
                        ],
                        "count": len(voices.voices),
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
                            return eleven_client.voices.ivc.create(
                                name=name,
                                files=[f],
                                description=f"IVC clone from {os.path.basename(audio_path)}",
                            )
                    result = await anyio.to_thread.run_sync(_clone)
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
                    await anyio.to_thread.run_sync(
                        lambda: eleven_client.voices.delete(voice_id)
                    )
                    return {"success": True, "deleted": voice_id}
                except Exception as e:
                    return {"success": False, "error": str(e)}

            return {"success": False, "error": f"Unknown action '{action}' for elevenlabs"}

        elif provider == "hume":
            if not hume_client:
                return {"success": False, "error": "HUME_API_KEY not configured"}
            if action == "list":
                try:
                    voices = await anyio.to_thread.run_sync(
                        lambda: list(hume_client.tts.voices.list())
                    )
                    return {
                        "success": True, "provider": "Hume AI",
                        "voices": [{"id": v.id, "name": v.name} for v in voices],
                    }
                except Exception as e:
                    return {"success": False, "error": str(e)}
            return {"success": False, "error": f"Action '{action}' not implemented for Hume"}

        return {"success": False, "error": f"Unknown provider '{provider}'"}
