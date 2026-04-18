import pytest
import os
import winsound
import io
import wave
from speech_mcp.providers.gemini import GeminiProvider
from speech_mcp.providers.windows import WindowsProvider

@pytest.mark.live
@pytest.mark.skipif(not os.getenv("GOOGLE_API_KEY"), reason="GOOGLE_API_KEY not set")
def test_gemini_audio_fidelity(request):
    """
    Exercise Gemini TTS and play the result locally.
    Requires --live flag to be passed to pytest.
    """
    if not request.config.getoption("--live"):
        pytest.skip("Use --live to run real audio playback tests")

    print("\n[LIVE] Initializing Gemini TTS Fidelity Test...")
    p = GeminiProvider()
    
    text = "SOTA, Gemini audio integration test, passed. Audio fidelity is nominal."
    wav_bytes = p.synthesize_wav(text, voice_name="Kore")
    
    assert len(wav_bytes) > 0, "Gemini produced empty audio"
    
    print(f"[LIVE] Playing {len(wav_bytes)} bytes via winsound...")
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
    print("[LIVE] Gemini Playback OK")

@pytest.mark.live
def test_windows_audio_fidelity(request, mock_ctx):
    """
    Exercise Windows SAPI5 TTS and play the result locally.
    """
    if not request.config.getoption("--live"):
        pytest.skip("Use --live to run real audio playback tests")

    print("\n[LIVE] Initializing Windows SAPI5 Fidelity Test...")
    p = WindowsProvider()
    
    text = "SOTA, Windows audio test, successful."
    wav_bytes = p.synthesize_wav(text)
    
    assert len(wav_bytes) > 0, "Windows TTS produced empty audio"
    
    print(f"[LIVE] Playing {len(wav_bytes)} bytes via winsound...")
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
    print("[LIVE] Windows Playback OK")
