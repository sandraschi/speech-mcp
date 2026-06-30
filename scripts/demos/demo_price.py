import os
import sys
import tempfile
import winsound

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")
from hume import HumeClient
from hume.tts import FormatWav, PostedUtterance


def run():
    print("Synthesizing 'The Vincent Price Experience' with Hume AI Octave...")
    api_key = os.environ.get("HUME_API_KEY")
    if not api_key:
        print("Error: HUME_API_KEY environment variable not set in .env.")
        sys.exit(1)

    client = HumeClient(api_key=api_key)

    # The Vincent Price prompt — Refined for clarity and to eliminate excessive bass
    text = "Deep into that darkness peering, long I stood there wondering, fearing, Doubting, dreaming dreams no mortal ever dared to dream before."
    description = "A voice that sounds like Vincent Price: sophisticated, articulate, and elegantly sinister, with a cultured mid-Atlantic accent and a crisp, theatrical clarity."

    utterance = PostedUtterance(text=text, description=description)

    audio = bytearray()
    print("Fetching audio from Hume API... (This may take a few seconds)")
    try:
        for chunk in client.tts.synthesize_file(utterances=[utterance], format=FormatWav(), strip_headers=False):
            audio.extend(chunk)
    except Exception as e:
        print(f"Hume API Error: {e}")
        sys.exit(1)

    if not audio:
        print("Error: Received empty audio from Hume.")
        sys.exit(1)

    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp.write(audio)
    tmp.close()

    print(f"Vincent Price demo: {len(audio)} bytes, playing...")
    # Prepend [pause] [pause] logic is handled by the driver sync usually,
    # but Hume's audio timing is very precise.
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)

    os.remove(tmp.name)
    print("OK")


if __name__ == "__main__":
    run()
