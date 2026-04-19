import os
import sys
import tempfile
import winsound

sys.path.insert(0, 'src')
from speech_mcp.providers.gemini import GeminiProvider


def run():
    print("Synthesizing with Gemini 3.1 (Audio Tags)...")
    p = GeminiProvider()

    text = '[cheerfully] Welcome to speech-mcp! [pause] [whispers] Did you know this model was released just two days ago? [normal] Gemini 3.1 Flash TTS. Two hundred audio tags. Seventy languages.'

    wav = p.synthesize_wav(text, voice_name='Aoede')

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.write(wav)
    tmp.close()

    print(f"Gemini tags demo: {len(wav)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)

    os.remove(tmp.name)
    print("OK")

if __name__ == "__main__":
    run()
