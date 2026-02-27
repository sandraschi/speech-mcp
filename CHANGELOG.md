# Changelog - Speech-MCP

All notable changes to this project will be documented in this file.

## [0.3.0] - 2026-02-27

### Added
- **Hume AI EVI & Octave**: Deep integration for expressive vocal interaction and SOTA TTS.
- **RAG Layer**: Integrated LanceDB + FastEmbed for semantic documentation search.
- **SEP-1577 Sampling**: Enabled iterative AI sampling for agentic workflows.
- **Agentic Tools**: Added `agentic_conversation_workflow` and `orchestrate_alexa_pattern`.
- **RAG Tools**: Added `search_docs` and `ask_docs` (grounded Q&A).
- **Safety Layer**: Added `check_vocal_safety` for intent risk analysis.
- **Real-time Weather**: Integrated `manage_domestic_utility` with `wttr.in` for live async weather fetching.
- **Transparency Layer**: Refined tool returns to provide honest orchestration stubs (e.g., `trigger_action` as proxy).

### Fixed
- **SOTA Quality Assurance**: Performed complete Ruff cleanup, resolving over 60 linting/formatting errors.
- **Route Mappings**: Fixed 'Under Construction' pages; mapped EVI and Octave UI routes.
- **Dashboard Utility**: Connected action cards to functional page navigation.
- **Navigational Cleanliness**: Removed duplicate links and fixed scoping errors in Dashboard navigation.

## [0.2.0-alpha] - 2026-02-27

### Added
- ElevenLabs roadmap integration.
- Multi-provider gateway architecture preparation.
- SOTA UI classes for Tools and Voices pages.
- Service Linkage Hub (Apps Hub) for central fleet discovery.
- Card-based layouts for `InteractionLab.tsx` and `CreativeLabs.tsx`.
- Alexa-style domestic utility logic (timers, weather, IoT) in Interaction Lab.

### Fixed
- React purity lints in `App.tsx` (stable `WAVE_DATA` generation).
- Inline CSS styles refactoring to `index.css`.
- PowerShell syntax for zombie process cleanup in `start.ps1`.
- Backend startup `PYTHONPATH` configuration.

## [0.1.0] - 2026-02-27

### Added
- Initial Hume AI integration (Octave v1, EVI v2/v3).
- FastMCP server implementation with `text_to_speech`, `start_evi_session`, and `manage_voice_clones`.
- SOTA Webapp baseline with premium glassmorphism aesthetics.
- Git repository initialization and GitHub remote setup.
