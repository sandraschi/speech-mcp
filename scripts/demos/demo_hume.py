import os
import sys
import tempfile
import winsound

sys.path.insert(0, "src")
from hume import HumeClient
from hume.tts import FormatWav, PostedUtterance


def run():
    print("Synthesizing with Hume AI Octave...")
    api_key = os.environ.get("HUME_API_KEY")
    if not api_key:
        print("Error: HUME_API_KEY environment variable not set.")
        sys.exit(1)

    client = HumeClient(api_key=api_key)

    text = "Beauty is no quality in things themselves. It exists merely in the mind which contemplates them."
    description = "Middle-aged scholarly voice, measured pace, warm but slightly melancholic"

    utterance = PostedUtterance(text=text, description=description)

    audio = bytearray()
    print("Fetching audio from Hume API...")
    for chunk in client.tts.synthesize_file(utterances=[utterance], format=FormatWav(), strip_headers=False):
        audio.extend(chunk)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio)
    tmp.close()

    print(f"Hume Octave: {len(audio)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)

    os.remove(tmp.name)
    print("OK")


if __name__ == "__main__":
    run()
