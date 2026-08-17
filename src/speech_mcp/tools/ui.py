import logging

from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Column, Heading, Metric, Row, Separator, Text
from prefab_ui.components.charts import BarChart, ChartSeries

logger = logging.getLogger(__name__)

PROVIDER_LABELS = {
    "hume": "Hume AI (EVI/Octave)",
    "elevenlabs": "ElevenLabs",
    "gemini": "Gemini 3.1",
    "gemma": "Gemma 4 (local)",
    "funasr": "FunASR (local STT)",
    "windows": "Windows SAPI5",
}


def register_ui_tools(mcp: FastMCP, providers: dict[str, bool] | None = None) -> None:
    """Register Prefab UI cards showing REAL provider availability.

    ``providers`` maps provider id -> configured (bool), derived from the same
    env state the health endpoint reports. No fabricated telemetry.
    """
    state = {
        "hume": bool(providers and providers.get("hume")),
        "elevenlabs": bool(providers and providers.get("elevenlabs")),
        "gemini": bool(providers and providers.get("gemini")),
        "gemma": bool(providers and providers.get("gemma", True)),
        "funasr": bool(providers and providers.get("funasr")),
        "windows": True,
    }

    @mcp.tool(app=True)
    def prosody_dashboard() -> PrefabApp:
        """Voice provider status: which speech providers are configured."""
        with Column(gap=4) as view:
            Heading("Voice Provider Status")
            Text("Configuration state reported by the backend (set API keys in .env).")
            Separator()
            for pid, label in PROVIDER_LABELS.items():
                ok = state[pid]
                with Row(gap=4):
                    Text(label)
                    Badge(
                        "configured" if ok else "missing key",
                        variant="success" if ok else "secondary",
                    )

        return PrefabApp(title="Voice Provider Status", view=view)

    @mcp.tool(app=True)
    def speech_activity_chart() -> PrefabApp:
        """Session activity: interaction counts by provider from this session's history."""
        from speech_mcp.state import _history

        counts: dict[str, int] = {}
        for entry in _history:
            prov = entry.get("provider", "unknown")
            counts[prov] = counts.get(prov, 0) + 1

        data = [{"session": k, "tokens": v} for k, v in sorted(counts.items())]

        with Column(gap=4) as view:
            Heading("Session Activity")
            Text(f"{len(_history)} interactions recorded this session.")
            if data:
                BarChart(
                    data=data,
                    series=[ChartSeries(data_key="tokens", label="Interactions")],
                    x_axis="session",
                )
            else:
                Text("No TTS/STT activity recorded yet this session.")

        return PrefabApp(title="Session Activity", view=view)

    @mcp.tool(app=True)
    def fleet_health_overview() -> PrefabApp:
        """Fleet voice health: configured providers, RAG sources, active timers."""
        from speech_mcp.state import _timers, get_store

        try:
            rag_sources = len(get_store().list_sources())
        except Exception as e:
            logger.warning("RAG source count failed: %s", e)
            rag_sources = 0

        with Column(gap=4) as view:
            Heading("Fleet Voice Health")
            with Row(gap=6):
                Metric(label="Providers Configured", value=f"{sum(state.values())}/{len(state)}")
                Metric(label="RAG Sources", value=str(rag_sources))
                Metric(label="Active Timers", value=str(len(_timers)))
            Separator()
            Heading("Provider Details", level=3)
            for pid, label in PROVIDER_LABELS.items():
                ok = state[pid]
                with Row(gap=4):
                    Text(label)
                    Badge(
                        "configured" if ok else "missing key",
                        variant="success" if ok else "secondary",
                    )

        return PrefabApp(title="Fleet Voice Health", view=view)

    @mcp.tool(app=True)
    def latency_benchmark_view() -> PrefabApp:
        """Latency is not measured by this server - honest status."""
        with Column(gap=4) as view:
            Heading("Latency")
            Text(
                "Latency measurements are not captured by this server. "
                "Use GET /api/v1/health for live connectivity status."
            )

        return PrefabApp(title="Latency", view=view)

    @mcp.tool(app=True)
    def provider_capability_matrix() -> PrefabApp:
        """Which providers support which capabilities (static, factual)."""
        with Column(gap=4) as view:
            Heading("Provider Capabilities")
            with Column(gap=2):
                Heading("TTS", level=3)
                Text("windows (SAPI5), gemini, hume, elevenlabs, gemma")
            with Column(gap=2):
                Heading("STT", level=3)
                Text("funasr (local), gemini, gemma")
            with Column(gap=2):
                Heading("Realtime streaming", level=3)
                Text("hume EVI (WebSocket), gemini live")
            with Column(gap=2):
                Heading("Voice cloning", level=3)
                Text("elevenlabs (Instant Voice Clone)")
            with Column(gap=2):
                Heading("Wake word", level=3)
                Text("openWakeWord (offline, local)")

        return PrefabApp(title="Capabilities", view=view)
