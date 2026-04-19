import os
import sys
import tempfile
import winsound

sys.path.insert(0, 'src')
from speech_mcp.providers.gemini import GeminiProvider


def run():
    print("Synthesizing Dramatic Scene with Gemini 3.1...")
    p = GeminiProvider()

    text = """[in the style of a late-night radio host, warm and unhurried]
    Good evening, Vienna.
    [pause]
    The servers are humming. The RTX 4090 is warm.
    [softly]
    And somewhere in the night, a German Shepherd named Benny is asleep on the couch.
    [wry smile in voice]
    Sin temor y sin esperanza."""

    wav = p.synthesize_wav(text, voice_name='Charon')

    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.write(wav)
    tmp.close()

    print(f"Scene demo: {len(wav)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)

    os.remove(tmp.name)
    print("OK")

if __name__ == "__main__":
    run()
