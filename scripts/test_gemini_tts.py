import os
from dotenv import load_dotenv
from speech_mcp.providers.gemini import GeminiProvider

load_dotenv()

def test_gemini_tts():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not set")
        return

    print("Initializing GeminiProvider...")
    try:
        provider = GeminiProvider(api_key=api_key)
        text = "Hello, this is a test of the Gemini TTS industrial stack."
        print(f"Synthesizing: {text}")
        wav_bytes = provider.synthesize_wav(text)
        print(f"Generated {len(wav_bytes)} bytes of WAV data.")
        
        # Save to file for manual check if needed
        with open("test_gemini.wav", "wb") as f:
            f.write(wav_bytes)
        print("Saved to test_gemini.wav")
        
    except Exception as e:
        print(f"Failure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_tts()
