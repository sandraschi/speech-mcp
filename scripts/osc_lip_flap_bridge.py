import argparse
import asyncio
import logging

from pythonosc import udp_client

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class LipFlapBridge:
    """
    Bridges speech activity to VRChat/Unity OSC parameters.
    Uses a simplified 'Anime Lip Flap' model (Open/Closed).
    """

    def __init__(self, host="127.0.0.1", port=9000):
        self.client = udp_client.SimpleUDPClient(host, port)
        self.mouth_param = "/avatar/parameters/MouthOpen"
        logger.info(f"Initialized OSC Bridge on {host}:{port}")

    def send_flap(self, value: float):
        """Sends a 0.0-1.0 float to the avatar's mouth parameter."""
        # Clamp value
        value = max(0.0, min(1.0, value))
        self.client.send_message(self.mouth_param, value)
        logger.debug(f"Sent Lip Flap: {value}")

    async def simulate_speech(self, duration=5.0):
        """Simulates a talking sequence for testing."""
        logger.info(f"Simulating speech for {duration}s...")
        steps = int(duration * 20)  # 20Hz update rate
        for i in range(steps):
            import random

            val = random.uniform(0.6, 1.0) if i % 2 == 0 else 0.0
            self.send_flap(val)
            await asyncio.sleep(0.05)
        self.send_flap(0.0)
        logger.info("Simulation complete.")


async def main():
    parser = argparse.ArgumentParser(description="Lip Flap OSC Bridge")
    parser.add_argument("--host", default="127.0.0.1", help="OSC Host")
    parser.add_argument("--port", type=int, default=9000, help="OSC Port")
    parser.add_argument("--simulate", action="store_true", help="Run simulation")

    args = parser.parse_args()
    bridge = LipFlapBridge(host=args.host, port=args.port)

    if args.simulate:
        await bridge.simulate_speech()
    else:
        logger.info("Bridge running. Integrate with Speech-MCP events to drive lip flaps.")
        # Future: Listen to Speech-MCP synthesis events via Redis or Direct API


if __name__ == "__main__":
    asyncio.run(main())
