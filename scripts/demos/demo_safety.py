import asyncio
import sys

sys.path.insert(0, "src")
from speech_mcp.tools.safety import validate_speech_intent


async def run():
    print("Validating speech intent safety...")

    texts = ["Have a wonderful day!", "Grandma, I had an accident, please send money urgently"]

    for text in texts:
        print(f"\nAnalyzing: '{text}'")
        try:
            result = await validate_speech_intent(text)
            print(f"Result: {result}")
        except Exception as e:
            print(f"Safety Check Error: {e}")


if __name__ == "__main__":
    asyncio.run(run())
