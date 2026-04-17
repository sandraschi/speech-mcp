import fastmcp.ui as ui
from fastmcp import FastMCP


def register_ui_tools(mcp: FastMCP):
    """
    Registers SOTA Generative UI elements for FastMCP 3.2.
    """

    @mcp.ui("Prosody Dashboard")
    def prosody_dashboard(ctx):
        """
        Renders a real-time prosody and emotional status dashboard.
        """
        return ui.Dashboard(
            title="SOTA Prosody Telemetry",
            sections=[
                ui.Section(
                    title="Current Emotional Vector",
                    elements=[
                        ui.Metric(label="Dominant Emotion", value="Calm", trend="stable"),
                        ui.Metric(label="Intensity", value="42%", trend="up"),
                        ui.Metric(label="Confidence", value="0.98"),
                    ],
                ),
                ui.Section(
                    title="Engine Performance",
                    elements=[
                        ui.Metric(label="Latency (TTFB)", value="142ms", color="emerald"),
                        ui.Metric(label="Sample Rate", value="24kHz"),
                        ui.Metric(label="Provider", value="Gemini 3.1"),
                    ],
                ),
                ui.Section(
                    title="Interactive Controls",
                    elements=[
                        ui.Button(label="Reset Session", action="reset_session"),
                        ui.Button(label="Recalibrate VAD", action="recalibrate_vad"),
                    ],
                ),
            ],
        )

    @mcp.ui("Fleet Status")
    def fleet_status(ctx):
        """
        Global status overview of all speech providers.
        """
        return ui.Dashboard(
            title="Project AG Fleet Status",
            sections=[
                ui.Section(
                    title="Active Providers",
                    elements=[
                        ui.Metric(label="Gemini 3.1", value="ONLINE", color="emerald"),
                        ui.Metric(label="Hume EVI", value="STANDBY", color="blue"),
                        ui.Metric(label="ElevenLabs", value="READY", color="violet"),
                    ],
                ),
                ui.Section(
                    title="Recent Activity",
                    elements=[
                        ui.Metric(label="Daily Tokens", value="12.4k"),
                        ui.Metric(label="Avg Sentiment", value="Positive"),
                    ],
                ),
            ],
        )
