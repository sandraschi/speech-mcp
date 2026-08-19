from speech_mcp.tools.agentic import register_agentic_tools
from speech_mcp.tools.demos import register_demo_tools
from speech_mcp.tools.monitoring import register_monitoring_tools
from speech_mcp.tools.rag import register_rag_tools
from speech_mcp.tools.revise import register_revise_tools
from speech_mcp.tools.runtime import register_runtime_tools
from speech_mcp.tools.safety import register_safety_tools
from speech_mcp.tools.speech import register_speech_tools
from speech_mcp.tools.stt import register_stt_tools
from speech_mcp.tools.ui import register_ui_tools
from speech_mcp.tools.utility import register_utility_tools
from speech_mcp.tools.wake_word import register_wake_word_tools

__all__ = [
    "register_agentic_tools",
    "register_demo_tools",
    "register_monitoring_tools",
    "register_rag_tools",
    "register_revise_tools",
    "register_runtime_tools",
    "register_safety_tools",
    "register_speech_tools",
    "register_stt_tools",
    "register_ui_tools",
    "register_utility_tools",
    "register_wake_word_tools",
]
