"""
Gemini TTS provider using the google-genai SDK (google.genai).

Models (Sept 2026):
  gemini-3.8-flash-tts       Flash TTS, creative direction + character design (default)
  gemini-3.8-flash-lite-tts  Flash-Lite TTS, high-volume cost-efficient scale
  gemini-3.1-flash-tts-preview  Legacy (April 2026), kept for backwards compat

Output: raw PCM, 16-bit signed little-endian, 24kHz, mono
        → wrapped in WAV headers before playback via wave stdlib module

Blog: https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-8-text-to-speech/

3.8 new capabilities (API surface is the same generate_content call):
  - generative voice design: NL prompt describes role/accent/character (100+ langs)
  - 2,000+ production voices (regional: Mexican Spanish, Quebec French, Scots English)
  - voice replication from 30s sample (consent-gated, SynthID + C2PA) - see CLONING_GUARDRAILS
  - line-by-line directing, long-form hours with minimal drift
  - native two-speaker staging + <laughs>/<sigh>/<gasp> + |mhm|/|yeah| backchanneling

Audio tags supported directly in the prompt text:
  [laughs]  [whispers]  [sighs]  [excited]  [sad]  [fast]  [slow]
  [dramatically]  [nervously]  [cheerfully]  [softly]  [sarcastically]
  and many more - see https://ai.google.dev/gemini-api/docs/speech-generation

Scene-direction prompting is also supported for richer control:
  Define environment context, speaker profiles, and tagged dialogue blocks.

Base prebuilt voices (3.1 set, still valid on 3.8):
  Aoede, Charon, Fenrir, Kore, Orion, Puck, Leda, Orus, Zephyr,
  Callirrhoe, Autonoe, Enceladus, Iocaste, Umbriel, Algieba,
  Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar,
  Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi,
  Vindemiatrix, Sadachbia, Sadaltager, Sulafar
Custom / saved 3.8 voices pass through as arbitrary voice_name strings.
"""

import io
import logging
import os
import wave
from typing import ClassVar

logger = logging.getLogger(__name__)

# PCM output spec from Gemini TTS API (fixed, not configurable)
_SAMPLE_RATE = 24000
_CHANNELS = 1
_SAMPLE_WIDTH = 2  # 16-bit


def _pcm_to_wav(pcm_bytes: bytes) -> bytes:
    """Wrap raw PCM bytes in a WAV container."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(_CHANNELS)
        wf.setsampwidth(_SAMPLE_WIDTH)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _wav_to_frames(wav_bytes: bytes) -> tuple[tuple[int, int, int], bytes]:
    """Split a WAV into ((channels, sampwidth, framerate), raw frames)."""
    buf = io.BytesIO(wav_bytes)
    with wave.open(buf, "rb") as wf:
        params = (wf.getnchannels(), wf.getsampwidth(), wf.getframerate())
        frames = wf.readframes(wf.getnframes())
    return params, frames


def _frames_to_wav(params: tuple[int, int, int], frames: bytes) -> bytes:
    """Re-wrap concatenated PCM frames in a WAV container."""
    channels, sampwidth, framerate = params
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(frames)
    return buf.getvalue()


def build_voice_design_prompt(
    role: str,
    accent: str = "",
    traits: str = "",
    language: str = "",
) -> str:
    """Build a natural-language voice-design prompt for AI Studio.

    Gemini 3.8 Flash TTS creates bespoke voices from prompts like this.
    The prompt itself is the design artifact - paste it into the AI Studio
    audio playground, save the resulting voice, then register the saved
    voice_id via manage_voice_bank.
    """
    parts = [f"Create a {role.strip()} voice"]
    if accent.strip():
        parts.append(f"with a {accent.strip()} accent")
    if language.strip():
        parts.append(f"speaking {language.strip()}")
    prompt = " ".join(parts) + "."
    if traits.strip():
        prompt += f" Character traits: {traits.strip()}."
    return prompt


def replication_requirements() -> dict:
    """Declare what Gemini 3.8 voice replication requires (no silent cloning)."""
    return {
        "reference_audio": "30-second clean single-speaker sample (5s minimum hard floor)",
        "consent_audio": "verbal consent recording from the voice owner, matching the reference speaker",
        "watermarking": "every clip watermarked with SynthID + C2PA credentials",
        "completion": "voice is designed/replicated in Google AI Studio; speech-mcp stores the saved voice_id",
        "policy": "see docs/CLONING_GUARDRAILS.md - rights statement + consent files required",
    }


class GeminiProvider:
    """
    Modular Gemini provider for TTS and STT (transcription).
    Requires GOOGLE_API_KEY in environment.
    Default TTS model is Gemini 3.8 Flash; override per-call or via GEMINI_TTS_MODEL.
    """

    MODEL_ID = "gemini-3.8-flash-tts"
    LITE_MODEL_ID = "gemini-3.8-flash-lite-tts"
    LEGACY_MODEL_ID = "gemini-3.1-flash-tts-preview"
    SUPPORTED_MODELS: ClassVar[dict[str, str]] = {
        "gemini-3.8-flash-tts": "Flash TTS - creative direction, voice design, character voices",
        "gemini-3.8-flash-lite-tts": "Flash-Lite TTS - high-volume, cost-efficient scale",
        "gemini-3.1-flash-tts-preview": "Legacy 3.1 Flash TTS (backwards compat)",
    }
    STT_MODEL_ID = "gemini-2.0-flash"  # SOTA for fast multimodal transcription

    # All prebuilt voices as of April 2026
    VOICES: ClassVar[list[str]] = [
        "Aoede",
        "Charon",
        "Fenrir",
        "Kore",
        "Orion",
        "Puck",
        "Leda",
        "Orus",
        "Zephyr",
        "Callirrhoe",
        "Autonoe",
        "Enceladus",
        "Iocaste",
        "Umbriel",
        "Algieba",
        "Despina",
        "Erinome",
        "Algenib",
        "Rasalgethi",
        "Laomedeia",
        "Achernar",
        "Alnilam",
        "Schedar",
        "Gacrux",
        "Pulcherrima",
        "Achird",
        "Zubenelgenubi",
        "Vindemiatrix",
        "Sadachbia",
        "Sadaltager",
        "Sulafar",
    ]

    def __init__(self, api_key: str | None = None, default_model: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        self.default_model = self._resolve_model(default_model or os.getenv("GEMINI_TTS_MODEL") or self.MODEL_ID)
        from google import genai

        self._client = genai.Client(api_key=self.api_key)

    @classmethod
    def _resolve_model(cls, model: str) -> str:
        model = (model or cls.MODEL_ID).strip()
        if model not in cls.SUPPORTED_MODELS:
            logger.warning("Unknown Gemini TTS model '%s', passing through anyway.", model)
        return model

    def synthesize_wav(self, text: str, voice_name: str = "Kore", model: str | None = None) -> bytes:
        """Synchronous TTS synthesis. model overrides the provider default."""
        from google.genai import types

        effective_model = self._resolve_model(model or self.default_model)
        if voice_name not in self.VOICES:
            logger.info("Voice '%s' not in base 31 list - forwarding as custom/saved 3.8 voice.", voice_name)

        response = self._client.models.generate_content(
            model=effective_model,
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice_name,
                        )
                    )
                ),
            ),
        )

        try:
            candidate = response.candidates[0] if response.candidates else None
            content = candidate.content if candidate else None
            part = content.parts[0] if content and content.parts else None
            pcm_bytes = part.inline_data.data if part and part.inline_data else None
            if not pcm_bytes:
                raise ValueError("Empty audio data")
            return _pcm_to_wav(pcm_bytes)
        except Exception as e:
            raise ValueError(f"Gemini TTS failed ({effective_model}): {e}") from e

    def synthesize_dialogue_wav(
        self,
        turns: list[dict],
        model: str | None = None,
    ) -> bytes:
        """Synthesize multi-turn dialogue, one WAV out.

        turns: [{"speaker": "Ava", "text": "...", "voice": "Aoede"}, ...]
          - speaker: label used in the native script (1-40 chars)
          - text: the line to speak (non-empty, tags allowed)
          - voice: prebuilt base voice OR custom/saved 3.8 voice_id

        Strategy: try the native single-call multi-speaker config when the
        installed google-genai SDK supports it; otherwise fall back to
        per-turn synthesize_wav + PCM concat. Both keep voices distinctly
        separated with natural turn-taking. Max 10 turns.
        """
        from google.genai import types

        if not turns or len(turns) > 10:
            raise ValueError("turns must contain 1-10 dialogue lines")
        cleaned: list[tuple[str, str, str]] = []
        for i, turn in enumerate(turns):
            speaker = str(turn.get("speaker") or f"Speaker {i + 1}").strip()[:40]
            text = str(turn.get("text") or "").strip()
            voice = str(turn.get("voice") or turn.get("voice_name") or "Kore").strip() or "Kore"
            if not text:
                raise ValueError(f"turn {i} has empty text")
            cleaned.append((speaker, text, voice))

        effective_model = self._resolve_model(model or self.default_model)
        native = self._synthesize_dialogue_native(cleaned, effective_model, types)
        if native is not None:
            return native
        return self._synthesize_dialogue_concat(cleaned, effective_model)

    def _synthesize_dialogue_native(
        self,
        cleaned: list[tuple[str, str, str]],
        effective_model: str,
        types,
    ) -> bytes | None:
        """Single-call multi-speaker attempt. Returns None when unsupported."""
        multi_cls = getattr(types, "MultiSpeakerVoiceConfig", None)
        speaker_cls = getattr(types, "SpeakerVoiceConfig", None)
        if multi_cls is None or speaker_cls is None:
            return None
        try:
            speaker_configs = []
            for speaker, _text, voice in cleaned:
                speaker_configs.append(
                    speaker_cls(
                        speaker=speaker,
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice),
                        ),
                    )
                )
            script = "\n".join(f"{speaker}: {text}" for speaker, text, _voice in cleaned)
            response = self._client.models.generate_content(
                model=effective_model,
                contents=script,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=multi_cls(speaker_voice_configs=speaker_configs),
                    ),
                ),
            )
            candidate = response.candidates[0] if response.candidates else None
            content = candidate.content if candidate else None
            part = content.parts[0] if content and content.parts else None
            pcm_bytes = part.inline_data.data if part and part.inline_data else None
            if not pcm_bytes:
                raise ValueError("Empty audio data")
            return _pcm_to_wav(pcm_bytes)
        except Exception as e:
            logger.info("Native multi-speaker unavailable, falling back to concat: %s", e)
            return None

    def _synthesize_dialogue_concat(
        self,
        cleaned: list[tuple[str, str, str]],
        effective_model: str,
    ) -> bytes:
        """Per-turn synthesis + PCM concat fallback (always available)."""
        base_params: tuple[int, int, int] | None = None
        frames_all = bytearray()
        for _speaker, text, voice in cleaned:
            wav = self.synthesize_wav(text, voice_name=voice, model=effective_model)
            params, frames = _wav_to_frames(wav)
            if base_params is None:
                base_params = params
            elif params != base_params:
                raise ValueError(f"Gemini TTS failed ({effective_model}): mixed audio params in dialogue concat")
            frames_all.extend(frames)
        if base_params is None or not frames_all:
            raise ValueError(f"Gemini TTS failed ({effective_model}): empty dialogue audio")
        return _frames_to_wav(base_params, bytes(frames_all))

    def transcribe(self, audio_bytes: bytes, mime_type: str = "audio/wav") -> str:
        """
        Synchronous STT (Transcription).

        Args:
            audio_bytes: Raw audio data.
            mime_type:   audio/wav, audio/mpeg, etc.

        Returns:
            The transcribed text.
        """
        from google.genai import types

        response = self._client.models.generate_content(
            model=self.STT_MODEL_ID,
            contents=[
                types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                "Transcribe the provided audio into highly accurate text. Return ONLY the transcript.",
            ],
            config=types.GenerateContentConfig(
                system_instruction="You are a professional stenographer. Transcribe audio exactly as heard."
            ),
        )

        try:
            text = response.text
            if not text:
                raise ValueError("Gemini returned empty transcript")
            return text.strip()
        except Exception as e:
            raise ValueError(f"Gemini STT failed: {e}") from e

    @property
    def voices(self) -> list[str]:
        return self.VOICES

    @property
    def models(self) -> dict[str, str]:
        return dict(self.SUPPORTED_MODELS)
