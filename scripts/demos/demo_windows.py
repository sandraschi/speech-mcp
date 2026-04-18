import asyncio
import sys
import tempfile
import os
import pyttsx3
import anyio

sys.path.insert(0, 'src')
from speech_mcp.tools.speech import _play_wav_file

async def run():
    print("Initializing Windows SAPI5...")
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.close()
    
    e = pyttsx3.init()
    e.save_to_file('Hello from speech-mcp. Windows SAPI5 is working.', tmp.name)
    e.runAndWait()
    
    print(f"Playing SAPI5 output: {tmp.name}")
    await _play_wav_file(tmp.name)
    
    os.remove(tmp.name)
    print("Windows TTS: OK")

if __name__ == "__main__":
    anyio.run(run)
