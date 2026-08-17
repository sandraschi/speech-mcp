"""
Gemini TTS provider using the google-genai SDK (google.genai).

Model: gemini-3.1-flash-tts-preview  (released 2026-04-15)
Output: raw PCM, 16-bit signed little-endian, 24kHz, mono
        → wrapped in WAV headers before playback via wave stdlib module

200+ audio tags supported directly in the prompt text:
  [laughs]  [whispers]  [sighs]  [excited]  [sad]  [fast]  [slow]
  [dramatically]  [nervously]  [cheerfully]  [softly]  [sarcastically]
  and many more — see https://ai.google.dev/gemini-api/docs/speech-generation

Scene-direction prompting is also supported for richer control:
  Define environment context, speaker profiles, and tagged dialogue blocks.

Voices (prebuilt, 30+):
  Aoede, Charon, Fenrir, Kore, Orion, Puck, Leda, Orus, Zephyr,
  Callirrhoe, Autonoe, Enceladus, Iocaste, Umbriel, Algieba,
  Despina, Erinome, Algenib, Rasalgethi, Laomedeia, Achernar,
  Alnilam, Schedar, Gacrux, Pulcherrima, Achird, Zubenelgenubi,
  Vindemiatrix, Sadachbia, Sadaltager, Sulafar
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


class GeminiProvider:
    """
    Modular Gemini provider for TTS and STT (transcription).
    Requires GOOGLE_API_KEY in environment.
    """

    MODEL_ID = "gemini-3.1-flash-tts-preview"
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

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is not set.")
        from google import genai

        self._client = genai.Client(api_key=self.api_key)

    def synthesize_wav(self, text: str, voice_name: str = "Kore") -> bytes:
        """Synchronous TTS synthesis."""
        from google.genai import types

        if voice_name not in self.VOICES:
            logger.warning("Voice '%s' not in known list.", voice_name)

        response = self._client.models.generate_content(
            model=self.MODEL_ID,
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
            raise ValueError(f"Gemini TTS failed: {e}") from e

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
