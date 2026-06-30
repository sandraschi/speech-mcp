import os
import sys
import tempfile
import winsound

sys.path.insert(0, "src")
from speech_mcp.providers.gemini import GeminiProvider


def run():
    print("Synthesizing with Gemini 3.1 (Plain)...")
    p = GeminiProvider()

    text = "The reductionist universe has no room for miracles, but it has plenty of room for wonder."
    wav = p.synthesize_wav(text, voice_name="Kore")

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(wav)
    tmp.close()

    print(f"Gemini TTS: {len(wav)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)

    os.remove(tmp.name)
    print("OK")


if __name__ == "__main__":
    run()
