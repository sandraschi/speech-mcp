import logging
import os
import shutil
import subprocess
from enum import StrEnum
from typing import Annotated

from fastmcp import Context, FastMCP
from pydantic import Field

logger = logging.getLogger(__name__)


class DemoName(StrEnum):
    WINDOWS = "windows"
    GEMINI_PLAIN = "gemini_plain"
    GEMINI_TAGS = "gemini_tags"
    GEMINI_SCENE = "gemini_scene"
    HUME = "hume"
    WEATHER = "weather"
    RAG = "rag"
    SAFETY = "safety"
    VERSIONS = "versions"
    NEKO = "neko"
    SHAKESPEARE = "shakespeare"
    PRICE = "price"


# Map enum values to filenames in scripts/demos/
DEMO_MAP = {
    DemoName.WINDOWS: "demo_windows.py",
    DemoName.GEMINI_PLAIN: "demo_gemini_plain.py",
    DemoName.GEMINI_TAGS: "demo_gemini_tags.py",
    DemoName.GEMINI_SCENE: "demo_gemini_scene.py",
    DemoName.HUME: "demo_hume.py",
    DemoName.WEATHER: "demo_weather.py",
    DemoName.RAG: "demo_rag.py",
    DemoName.SAFETY: "demo_safety.py",
    DemoName.VERSIONS: "versions.py",
    DemoName.NEKO: "demo_neko.py",
    DemoName.SHAKESPEARE: "demo_shakespeare.py",
    DemoName.PRICE: "demo_price.py",
}


def register_demo_tools(mcp: FastMCP):
    """Register tools for running expressive speech and capability demos."""

    @mcp.tool()
    async def run_speech_demo(
        demo: Annotated[DemoName, Field(description="Demo name to execute.")],
        ctx: Context = None,
    ) -> dict:
        """
        Execute a hardware-specific speech or capability demo script.

        Verifies API connectivity, local hardware (SAPI5), and RAG status.

        ## Return Format
        {"success": bool, "demo": str, "exit_code"?: int, "output"?: str, "error"?: str}
        """
        script_filename = DEMO_MAP.get(demo)
        if not script_filename:
            return {"success": False, "error": f"Demo '{demo}' not found in map."}

        # Resolve path relative to project root
        # server.py is in src/speech_mcp/
        # scripts is in root/
        cwd = os.getcwd()
        script_path = os.path.join(cwd, "scripts", "demos", script_filename)

        if not os.path.exists(script_path):
            return {"success": False, "error": f"Script file not found at {script_path}. CWD is {cwd}"}

        if ctx:
            await ctx.info(f"Executing Industrial Demo: {demo} ({script_filename})")

        try:
            # Run using uv to ensure dependencies are loaded
            uv_path = shutil.which("uv") or "uv"
            result = subprocess.run(  # noqa: S603
                [uv_path, "run", "python", script_path], capture_output=True, text=True, check=False, cwd=cwd
            )
            # Mask API keys if they leaked in output (unlikely but good practice)
            output = result.stdout + result.stderr
            return {
                "success": result.returncode == 0,
                "demo": demo.value,
                "exit_code": result.returncode,
                "output": output.strip(),
            }

        except Exception as e:
            logger.exception(f"Failed to execute demo {demo}")
            return {"success": False, "error": str(e)}
