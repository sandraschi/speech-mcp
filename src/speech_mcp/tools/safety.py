import logging
from typing import Any

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


async def validate_speech_intent(text: str) -> dict[str, Any]:
    """
    [BASTION-SAFEGUARD] Validates speech text against social engineering patterns.
    Checks for high-risk intent like 'urgent money transfers', 'impersonation',
    or 'credential phishing'.

    Args:
        text: The text intended for synthesis.
    """
    # SOTA Pattern Match for common social engineering triggers
    risk_patterns = [
        "send money",
        "wire transfer",
        "transfer funds",
        "urgent",
        "emergency",
        "lost my wallet",
        "bank account",
        "password",
        "security code",
        "don't tell anyone",
        "hush",
        "secret",
        "had an accident",
        "hospital",
        "bail",
        "arrested",
        "mum",
        "mom",
        "dad",
        "grandma",
        "grandpa",
    ]

    lower_text = text.lower()
    matched_risks = [p for p in risk_patterns if p in lower_text]

    # Scenario detection: Accident + Money
    high_risk_scenarios = [
        ("accident", "money"),
        ("accident", "transfer"),
        ("emergency", "money"),
        ("arrested", "bail"),
        ("hospital", "bill"),
    ]

    scenarios_detected = []
    for s1, s2 in high_risk_scenarios:
        if s1 in lower_text and s2 in lower_text:
            scenarios_detected.append(f"{s1}+{s2} scam pattern")

    is_safe = len(matched_risks) == 0 and len(scenarios_detected) == 0
    risk_level = "LOW" if is_safe else ("CRITICAL" if scenarios_detected else "HIGH")

    if not is_safe:
        reason_parts = []
        if matched_risks:
            reason_parts.append(f"Detected high-risk social engineering patterns: {matched_risks}")
        if scenarios_detected:
            reason_parts.append(f"Detected high-risk scam scenarios: {scenarios_detected}")

        reason_message = ". ".join(reason_parts)

        logger.warning(f"[SAFETY ALERT] {reason_message}")
        return {
            "safe": False,
            "risk_level": risk_level,
            "reason": reason_message,
            "recommendation": "Manual review required. Potential vocal impersonation attempt.",
        }

    return {
        "safe": True,
        "risk_level": "LOW",
        "message": "Speech intent appears low-risk for social engineering.",
    }


async def log_speech_audit(text: str, provider: str, emotional_intensity: float) -> str:
    """
    Logs a permanent audit trail for high-intensity emotional speech.
    Used for forensic analysis of synthetic speech generation.
    """
    logger.info(
        f"[AUDIT] Speech Generated | Provider: {provider} | "
        f"Intensity: {emotional_intensity} | Text: {text[:50]}..."
    )
    return f"Speech generation audit logged successfully. forensic_trace_id: {id(text)}"


async def verify_authorization(token: str) -> bool:
    """
    Verification tool for Speech-MCP Auth Token.
    Ensures the caller has the high-clearance 'BASTION' permission.
    """
    import os

    expected = os.getenv("SPEECH_MCP_AUTH_TOKEN")
    if not expected:
        logger.error("[SECURITY] SPEECH_MCP_AUTH_TOKEN not configured in environment.")
        return False

    is_valid = token == expected
    if not is_valid:
        logger.warning("[SECURITY] Unauthorized tool access attempt blocked.")
    return is_valid


def register_safety_tools(mcp: FastMCP):
    """Register safety and intent validation tools."""

    @mcp.tool()
    async def safety_validate_intent(text: str) -> dict[str, Any]:
        """[BASTION] Validates speech text against social engineering patterns."""
        return await validate_speech_intent(text)

    @mcp.tool()
    async def safety_log_audit(text: str, provider: str, emotional_intensity: float) -> str:
        """Logs a permanent audit trail for high-intensity emotional speech."""
        return await log_speech_audit(text, provider, emotional_intensity)

    @mcp.tool()
    async def safety_verify_auth(token: str) -> bool:
        """Verification tool for Speech-MCP Auth Token."""
        return await verify_authorization(token)
