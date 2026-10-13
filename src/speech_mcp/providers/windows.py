import logging
import os
import tempfile
from typing import Any, cast

import pyttsx3

logger = logging.getLogger(__name__)


class WindowsProvider:
    """
    Modular Windows SAPI5 provider using pyttsx3.
    Requires no API keys, uses the system default voice.
    """

    def __init__(self):
        # We don't persist the 'engine' because pyttsx3 is sensitive
        # to threading and loop context if not handled carefully.
        pass

    def synthesize_wav(self, text: str, voice: str = "default") -> bytes:
        """Synthesize text to WAV bytes using the Windows SAPI5 engine.

        The voice parameter accepts a voice id, a name fragment, or one of the
        friendly aliases heart/sky/adam (mapped to Zira/Hazel/David). Returns
        the rendered WAV file bytes.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()

        try:
            engine = pyttsx3.init()
            if voice and voice != "default":
                try:
                    voices: list[Any] = list(cast("list[Any] | None", engine.getProperty("voices")) or [])
                    target_id = None
                    for v in voices:
                        vid = getattr(v, "id", "") or ""
                        vname = getattr(v, "name", "") or ""
                        if voice == vid or voice.lower() in vname.lower() or voice.lower() in vid.lower():
                            target_id = vid
                            break
                    if not target_id:
                        alias_map = {"heart": "zira", "sky": "hazel", "adam": "david"}
                        alias = alias_map.get(voice.lower())
                        if alias:
                            for v in voices:
                                if alias in (getattr(v, "name", "") or "").lower():
                                    target_id = getattr(v, "id", "")
                                    break
                    if not target_id and voices:
                        idx = abs(hash(voice)) % len(voices)
                        target_id = getattr(voices[idx], "id", None)
                    if target_id:
                        engine.setProperty("voice", target_id)
                except Exception:
                    logger.debug("SAPI5 voice match failed, using default voice")
            engine.save_to_file(text, tmp.name)
            engine.runAndWait()

            # Allow engine to finalize File I/O
            with open(tmp.name, "rb") as f:
                data = f.read()
            return data
        except Exception as e:
            logger.error(f"Windows TTS synthesis failed: {e}")
            raise
        finally:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
