import os
import sys

import pytest

if sys.platform != "win32":
    pytest.skip("Windows-only live audio tests", allow_module_level=True)

import winsound

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


@pytest.mark.live
def test_c922_hardware_presence(request):
    """
    Verify that the C922 camera and microphone are detected in the real workspace.
    """
    if not request.config.getoption("--live"):
        pytest.skip("Use --live to run real hardware detection tests")

    from scripts.utils.hardware_probe import get_cameras, get_microphones

    cams = get_cameras()
    mics = get_microphones()

    c922_cam = any("c922" in c.lower() for c in cams)
    c922_mic = any("c922" in m["name"].lower() for m in mics)

    print("\n[LIVE] Hardware Audit:")
    print(f"  C922 Camera: {'FOUND' if c922_cam else 'MISSING'}")
    print(f"  C922 Microphone: {'FOUND' if c922_mic else 'MISSING'}")

    # We don't fail the test if missing, but we report it.
    # The user mentioned C922 is always connected.
    assert c922_cam or c922_mic, "C922 hardware not detected in live environment"


@pytest.mark.live
def test_success_chime_haiku(request):
    """
    Synthesize and play the 'Testing Haiku' as a success chime.
    """
    if not request.config.getoption("--live"):
        pytest.skip("Use --live to run audio haiku tests")

    from speech_mcp.providers.windows import WindowsProvider

    p = WindowsProvider()

    # A professional yet interesting haiku for a successful test suite
    haiku = """
    Ancient pond remains,
    Code jumps in with silent grace,
    Sound of water flows.
    """

    print("\n[LIVE] Synthesizing Success Haiku...")
    print(haiku)

    wav_bytes = p.synthesize_wav(haiku)
    winsound.PlaySound(wav_bytes, winsound.SND_MEMORY)
    print("[LIVE] Haiku chime completed.")
