import logging

from fastmcp import FastMCP
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Column, Heading, Metric, Row, Separator, Text
from prefab_ui.components.charts import BarChart, ChartSeries

logger = logging.getLogger(__name__)

# FastMCP tool annotations (TOOL_DESIGN_STANDARDS §9) - dict format works with all 3.x.
_README_ONLY = {"readonly": True}

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

    @mcp.tool(app=True, annotations=_README_ONLY)
    def prosody_dashboard() -> PrefabApp:
        """Voice provider status: which speech providers are configured.

        ## Return Format
        ``PrefabApp`` - a Prefab UI card listing each provider with a
        ``configured`` / ``missing key`` badge.

        ## Examples
        ``prosody_dashboard()`` -> Prefab card showing provider config state.
        """
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

    @mcp.tool(app=True, annotations=_README_ONLY)
    def speech_activity_chart() -> PrefabApp:
        """Session activity: interaction counts by provider from this session's history.

        ## Return Format
        ``PrefabApp`` - a bar chart of TTS/STT interactions per provider this
        session, or a "no activity" message.

        ## Examples
        ``speech_activity_chart()`` -> Prefab bar chart of this session's
        provider activity.
        """
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
                BarChart(  # type: ignore[call-arg]
                    data=data,
                    series=[ChartSeries(data_key="tokens", label="Interactions")],  # type: ignore[call-arg]
                    x_axis="session",  # type: ignore[call-arg]
                )
            else:
                Text("No TTS/STT activity recorded yet this session.")

        return PrefabApp(title="Session Activity", view=view)

    @mcp.tool(app=True, annotations=_README_ONLY)
    def fleet_health_overview() -> PrefabApp:
        """Fleet voice health: configured providers, RAG sources, active timers.

        ## Return Format
        ``PrefabApp`` - a card with provider-count, RAG-source and active-timer
        metrics plus a per-provider configured/missing badge list.

        ## Examples
        ``fleet_health_overview()`` -> Prefab health card for all speech
        providers.
        """
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

    @mcp.tool(app=True, annotations=_README_ONLY)
    def latency_benchmark_view() -> PrefabApp:
        """Measured synthesis latency per provider (real telemetry)."""

        from speech_mcp.storage import analytics_prune, analytics_summary

        analytics_prune()
        summary = analytics_summary(hours=24)
        providers = summary.get("providers", {})

        with Column(gap=4) as view:
            Heading("Latency (24h)")
            Text(
                f"{summary.get('total_calls', 0)} calls recorded across "
                f"{len(providers)} providers in the last 24 hours."
            )
            if providers:
                Separator()
                for name, p in providers.items():
                    with Row(gap=4):
                        Text(name)
                        Badge(
                            f"{p.get('avg_latency_ms', '-')}ms avg",
                            variant="info",
                        )
                        Badge(
                            f"p95 {p.get('p95_latency_ms', '-')}ms",
                            variant="info",
                        )
                        Badge(
                            f"{int((p.get('success_rate', 1)) * 100)}% ok",
                            variant="success" if p.get("success_rate", 1) > 0.9 else "warning",
                        )
            else:
                Text("No speech activity recorded yet - run a TTS/readout call to populate.")

        return PrefabApp(title="Latency", view=view)

    @mcp.tool(app=True, annotations=_README_ONLY)
    def provider_capability_matrix() -> PrefabApp:
        """Which providers support which capabilities (static, factual).

        ## Return Format
        ``PrefabApp`` - a capability matrix card (TTS/STT/streaming/cloning/wake
        word per provider).

        ## Examples
        ``provider_capability_matrix()`` -> Prefab capability matrix.
        """
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
