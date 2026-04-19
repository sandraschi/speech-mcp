import asyncio
import os
import sys
import winsound

import httpx
from dotenv import load_dotenv

# Ensure we can import from src
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(__file__), "../../src")))
from speech_mcp.providers.gemini import GeminiProvider

load_dotenv()

async def get_weather(city: str):
    async with httpx.AsyncClient() as client:
        try:
            # format=j1 gives raw JSON with more details
            r = await client.get(f'https://wttr.in/{city}?format=j1')
            r.raise_for_status()
            return r.json()
        except Exception:
            return None

def build_weather_prompt(city: str, data: dict, is_ahvaz: bool = False):
    if not data:
        return f"I'm sorry, I couldn't reach the weather service for {city}."

    current = data['current_condition'][0]
    temp = int(current['temp_C'])
    condition = current['weatherDesc'][0]['value'].lower()
    humidity = current['humidity']
    wind = current['windspeedKmph']

    if is_ahvaz:
        return f"[sighs] Meanwhile, in Ahvaz, Iran... the heat is staggering. It is currently {temp} degrees celsius, with {humidity} percent humidity. [dramatically] It's practically a blast furnace."

    # Atmospheric tags
    tags = ""
    if "rain" in condition or "shower" in condition:
        tags += "[rain splattering] "
    if int(wind) > 25:
        tags += "[wind howling] "

    shiver = ""
    if temp <= 0:
        shiver = "[shivers] Brrr! "

    return f"{tags}The current weather in {city} is {condition}. The temperature is {temp} degrees celsius. {shiver}Humidity stands at {humidity} percent, and winds are blowing at {wind} kilometers per hour."

async def run_weather_demo():
    city = sys.argv[1] if len(sys.argv) > 1 else "Vienna"
    print(f"[*] Fetching weather for {city}...")

    city_data = await get_weather(city)
    ahvaz_data = await get_weather("Ahvaz")

    try:
        provider = GeminiProvider()
    except Exception as e:
        print(f"Error: {e}")
        return

    # 1. Main Report
    main_prompt = build_weather_prompt(city, city_data)
    print(f"[Gemini] {main_prompt}")
    wav_main = provider.synthesize_wav(main_prompt, voice_name="Zephyr")
    winsound.PlaySound(wav_main, winsound.SND_MEMORY)

    # 2. Ahvaz Gag
    if ahvaz_data and city.lower() != "ahvaz":
        await asyncio.sleep(1) # Dramatic pause
        gag_prompt = build_weather_prompt("Ahvaz", ahvaz_data, is_ahvaz=True)
        print(f"[Gemini] {gag_prompt}")
        wav_gag = provider.synthesize_wav(gag_prompt, voice_name="Zephyr")
        winsound.PlaySound(wav_gag, winsound.SND_MEMORY)

if __name__ == "__main__":
    asyncio.run(run_weather_demo())
