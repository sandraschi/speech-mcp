import os
import sys

import anyio
from dotenv import load_dotenv

# Ensure we can import from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))


async def run_demo():
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Error: GOOGLE_API_KEY not found in .env")
        return

    from google import genai
    from google.genai import types

    print("Initializing Gemini 3.1 Live Session...")
    client = genai.Client(api_key=api_key)

    # Minimal config for a quick turn
    model = "gemini-3.1-flash-live-preview"
    config = types.LiveConnectConfig(
        response_modalities=["AUDIO"],
        system_instruction="You are a helpful assistant. Keep your response very brief (under 10 words).",
        thinking_config=types.ThinkingConfig(thinking_level="minimal"),
    )

    try:
        async with client.aio.live.connect(model=model, config=config) as session:
            print(f"Connected to {model}")

            # Send a text message to trigger an audio response
            message = "Hello! Say 'Gemini Live is operational' clearly."
            print(f"Sending: {message}")

            await session.send_realtime_input(text=message)

            print("Waiting for response audio...")
            audio_count = 0
            async for response in session.receive():
                if response.server_content:
                    sc = response.server_content

                    # Check for transcripts
                    if sc.output_transcription:
                        print(f"Model Transcript: {sc.output_transcription.text}")

                    # Check for audio parts
                    if sc.model_turn:
                        for part in sc.model_turn.parts:
                            if part.inline_data:
                                audio_count += 1

                    if sc.turn_complete:
                        print(f"Turn complete. Received {audio_count} audio chunks.")
                        break

    except Exception as e:
        print(f"Session Error: {e}")


if __name__ == "__main__":
    anyio.run(run_demo)
