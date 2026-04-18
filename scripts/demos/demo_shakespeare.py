import sys
from dotenv import load_dotenv
load_dotenv()
import winsound
import tempfile
import os

sys.path.insert(0, 'src')
from speech_mcp.providers.gemini import GeminiProvider

def run():
    print("Synthesizing Shakespeare Monologue with Gemini 3.1...")
    p = GeminiProvider()
    
    # Hamlet - To be, or not to be
    # Using triple pause for audio driver sync
    text = """
    [pause] [pause] [pause]
    To be, or not to be, that is the question:
    Whether 'tis nobler in the mind to suffer
    The slings and arrows of outrageous fortune,
    Or to take arms against a sea of troubles
    And by opposing end them. To die—to sleep,
    No more; and by a sleep to say we end
    The heart-ache and the thousand natural shocks
    That flesh is heir to: 'tis a consummation
    Devoutly to be wish'd. To die, to sleep;
    To sleep, perchance to dream—ay, there's the rub.
    """
    
    # 'Charon' is excellent for deep, dramatic readings
    wav = p.synthesize_wav(text, voice_name='Charon')
    
    tmp = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
    tmp.write(wav)
    tmp.close()
    
    print(f"Shakespeare demo: {len(wav)} bytes, playing...")
    winsound.PlaySound(tmp.name, winsound.SND_FILENAME)
    
    os.remove(tmp.name)
    print("OK")

if __name__ == "__main__":
    run()
