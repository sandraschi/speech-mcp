import logging
import os
import tempfile

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

    def synthesize_wav(self, text: str) -> bytes:
        """
        Synthesize text to WAV bytes using the Windows SAPI5 engine.

        Args:
            text: The text to speak.

        Returns:
            WAV file bytes.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()

        try:
            engine = pyttsx3.init()
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
