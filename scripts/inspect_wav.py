import wave

def inspect_wav(filename):
    try:
        with wave.open(filename, "rb") as wf:
            print(f"Filename: {filename}")
            print(f"Channels: {wf.getnchannels()}")
            print(f"Sample Width: {wf.getsampwidth()}")
            print(f"Frame Rate: {wf.getframerate()}")
            print(f"Frames: {wf.getnframes()}")
            duration = wf.getnframes() / wf.getframerate()
            print(f"Duration: {duration:.2f} seconds")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_wav("test_gemini.wav")
