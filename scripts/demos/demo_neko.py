import sys
from dotenv import load_dotenv
load_dotenv()
import winsound
import tempfile
import os

sys.path.insert(0, 'src')
from speech_mcp.providers.gemini import GeminiProvider

def run():
    print("Synthesizing 'Wagahai wa Neko de Aru' (Japanese) with Gemini 3.1...")
    p = GeminiProvider()
    
    # Natsume Soseki - I Am a Cat (Opening lines)
    # Adding triple [pause] to decisively prevent audio clipping on start
    text = """
    [pause] [pause] [pause] 吾輩は猫である。名前はまだ無い。
    どこで生れたかとんと見当がつかぬ。
    何でも薄暗いじめじめした所でニャーニャー泣いていた事だけは記憶している。
    """
    
    # Using 'Aoede' or 'Charon' might work, but 'Kore' is safe for multi-lingual tasks.
    # We will let the provider handle the language detection or specify if needed.
    wav = p.synthesize_wav(text, voice_name='Aoede')
    
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.write(wav)
    tmp.close()
    
    print(f"Neko demo: {len(wav)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)
    
    os.remove(tmp.name)
    print("OK")

if __name__ == "__main__":
    run()
