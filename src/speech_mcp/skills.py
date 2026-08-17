"""Fleet skill surface: MCP resources (skill://) + helpers for the REST /api/skills.

Skills live in ``src/speech_mcp/skills/{name}/SKILL.md``. Exposing them as MCP
resources lets Cursor/Claude/opencode read them via ``skill://{name}``, and the
REST endpoints feed the webapp Skills page.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).resolve().parent / "skills"


def list_skills() -> list[dict]:
    """Return [{name, description, path}] for every installed skill."""
    out: list[dict] = []
    if not SKILLS_DIR.is_dir():
        return out
    for entry in sorted(SKILLS_DIR.iterdir()):
        skill_md = entry / "SKILL.md"
        if not skill_md.is_file():
            continue
        out.append(
            {
                "name": entry.name,
                "description": _frontmatter_description(skill_md),
                "path": str(skill_md),
            }
        )
    return out


def get_skill(name: str) -> str | None:
    """Return SKILL.md content for a skill name, or None."""
    skill_md = SKILLS_DIR / name / "SKILL.md"
    if not skill_md.is_file():
        return None
    return skill_md.read_text(encoding="utf-8")


def _frontmatter_description(skill_md: Path) -> str:
    """Best-effort extract of the YAML frontmatter description."""
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return ""
    if text.startswith("---"):
        end = text.find("---", 3)
        if end > 0:
            for line in text[3:end].splitlines():
                if line.startswith("description:"):
                    return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def register_skill_resources(mcp: FastMCP) -> None:
    """Register each skill as an MCP resource: skill://{name}."""

    @mcp.resource("skill://{skill_name}")
    def skill_resource(skill_name: str) -> str:
        content = get_skill(skill_name)
        if content is None:
            raise ValueError(f"Unknown skill: {skill_name}")
        return content
