import os
import winsound


def test_playback(filename):
    if not os.path.exists(filename):
        print(f"File not found: {filename}")
        return

    print(f"Testing playback of {filename} via winsound...")
    try:
        # SND_FILENAME = 131072
        # SND_NODEFAULT = 2
        winsound.PlaySound(filename, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
        print("Playback call finished.")
    except Exception as e:
        print(f"Playback failed: {e}")


if __name__ == "__main__":
    test_playback("test_gemini.wav")
