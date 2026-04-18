import asyncio
import httpx

async def run():
    print("Fetching weather for Vienna...")
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get('https://wttr.in/Vienna?format=3')
            r.raise_for_status()
            print('Weather:', r.text.strip())
        except Exception as e:
            print(f"Error fetching weather: {e}")

if __name__ == "__main__":
    asyncio.run(run())
