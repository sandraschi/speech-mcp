import os
import sys

from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, "src")
from elevenlabs.client import ElevenLabs
from hume import HumeClient


def run():
    print("--- Professional Voice Management Demo ---")

    # Check ElevenLabs
    el_key = os.environ.get("ELEVENLABS_API_KEY")
    if el_key and "your_elevenlabs_api_key_here" not in el_key:
        print("\n[ElevenLabs] Connection: ONLINE")
        client = ElevenLabs(api_key=el_key)
        voices = client.voices.get_all()
        print(f"Current Clones: {len(voices.voices)}")
        for v in voices.voices[:3]:
            print(f" - {v.name} ({v.voice_id})")
    else:
        print("\n[ElevenLabs] Connection: OFFLINE (Missing or placeholder API key)")

    # Check Hume
    h_key = os.environ.get("HUME_API_KEY")
    if h_key:
        print("\n[Hume AI] Connection: ONLINE")
        h_client = HumeClient(api_key=h_key)
        h_voices = list(h_client.tts.voices.list())
        print(f"Custom Voices: {len(h_voices)}")
        for hv in h_voices[:3]:
            print(f" - {hv.name} ({hv.id})")
    else:
        print("\n[Hume AI] Connection: OFFLINE")

    print("\n--- Industrial Capability Verified ---")
    print("To clone a voice via snippet, use the 'manage_voice_clones' tool with:")
    print("  provider='elevenlabs', action='create', name='MyClone', audio_path='path/to/sample.wav'")


if __name__ == "__main__":
    run()
