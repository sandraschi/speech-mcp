import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def run_agentic_mission():
    """
    Example of an Antigravity-aware agentic mission.
    """
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "speech_mcp.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # 1. Initialize mission
            print("🚀 Starting Agentic Mission...")
            mission = await session.call_tool(
                "agentic_conversation_workflow",
                {
                    "goal": "Explain the new FastMCP standards to the user",
                    "provider": "hume",
                },
            )

            print(f"Strategy: {mission.content[0].text['mission_strategy']}")

            # 2. Check for Dialogic next steps
            for step in mission.content[0].text["next_steps"]:
                print(f"📍 Next Step: {step}")

            # 3. Simulate high-bandwidth interaction
            if (
                "Initialize high-bandwidth stream"
                in mission.content[0].text["next_steps"]
            ):
                print(
                    "Connecting to WebSocket side-channel at ws://localhost:10760/ws/stream..."
                )


if __name__ == "__main__":
    asyncio.run(run_agentic_mission())
