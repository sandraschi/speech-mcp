# Voice Clone Bank + Talk-To Mode — Plan (2026-09-17)

Private-local goal: a tested **Voice Bank** (favorite actors, dad, whoever comes next)
where each profile can speak any text or *converse* through a paired persona.
Fully offline-capable, private by default, one-click from the webapp.

Status: plan only. Phase 1+2 start on go-ahead. No commits without Sandra's word.

## Background (agreed 2026-09-17)

- VoiceStudio sidecar provider scaffolded, disabled by default (`VOICESTUDIO_ENABLED`).
  See `docs/providers/voicestudio.md`. AGPL code never embedded; HTTP/MCP boundary only.
- Voices page: ElevenLabs/VoiceStudio switch + transcript field + per-engine hints.
- Reference-audio rules: ElevenLabs IVC 30 s–3 min clean single-speaker (5 s minimum,
  gains flatten past ~5 min); VoiceStudio 3–10 s sweet spot (+ transcript, max 20 s
  with transcript, 75 s auto-search without).
- No identity parameter exists anywhere: `clone_voice` takes ref audio only; `name`
  is our label. VoiceStudio does not ask who the speaker is; it clones whatever
  dominates the clip (multi-speaker/score = muddy clone, not an error).
- Cloud caveat: ElevenLabs/Hume run identity fingerprinting and may gate or review
  famous voices — see `docs/CLONING_GUARDRAILS.md` (Burton is near-certain to trip
  it; Werner may). **This is the practical reason the actor bank defaults to the
  local VoiceStudio path**, with ElevenLabs reserved for voices that pass or for
  original (dad) material.
- Text copyright vs voice: Shakespeare's Richard III text is public domain; an
  actor's recorded *performance* is not. Private study on own disk is the boundary;
  never publish clones of performers.
- Dad's voice: keep untouched copies of all source audio; first playback on neutral
  text; boundaries file before first session.

## Phase 0 — Inventory (Sandra, ~30 min, no code)

1. Bank list: actor → film(s) → scene(s), one line each. (Werner, Burton confirmed.)
2. Dad's material: format, total minutes, single-speaker vs cross-talk, phone vs room.
3. Primary engine pick. Recommendation: VoiceStudio default, ElevenLabs for 1–2
   crown-jewel voices that clear its guardrails.
4. Dad boundaries sketch: what he may/may not say.

## Phase 1 — Bank data model + backup (backend, ~1/2 day)

Extend `voice_bank` entries (storage.py + `manage_voice_bank`): `engine`
(elevenlabs/voicestudio), `profile_id`, `ref_clip` (cleaned reference kept under
`data/voice-bank/<name>/`), `transcript`, `origin` (free text, e.g.
"Fahrenheit 451 interrogation scene"), `private: true` default, `created` date.

New `manage_voice_bank(operation="export"|"import")`: whole bank (profiles + clips)
to one zip. Voices that cannot be re-recorded must survive disk failure — this is
the highest-value half-day in the plan.

Docs: `docs/voice-bank.md` (bank contract: stored what/where, private-by-default).
Tests: register → export → delete → import → speak round-trip with temp dirs.

## Phase 2 — Cleaning chain (one script, ~1/2 day)

New `scripts/prepare_clone_clip.py`, three skippable stages:

1. **Isolate** — VoiceStudio vocal isolation when the scene has score; pass-through
   for dry material (voicemail).
2. **Select** — energy segmentation (reuse `detect_sound_events` logic) proposes the
   cleanest single-speaker window (10 s VoiceStudio / 60 s ElevenLabs); human
   confirms timestamps.
3. **Normalize** — mono, 16 kHz+, strip silence, peak-normalize; writes `ref.wav` +
   `ref.txt` (transcript template, FunASR pre-fill for correction).

Verify: output clip shows one `speech_like` event, no `loud_event` music beds.

## Phase 3 — Clone + quality gate (wiring, mostly exists)

Post-clone test on the Voices page: one click synthesizes the fixed pangram in the
new voice, plays it, prompts keep/re-cut. Optional advisory speaker-similarity
score (embedding cosine ref vs render), never a gate, declared in docs.

Verify: clone → pangram → keep, one actor end-to-end.

## Phase 4 — Talk-to mode (the feature, ~1–2 days)

1. `voice_personas`: `{name, bank_voice, system_prompt, provider}` stored beside the
   bank; `manage_voice_personas` tool + REST.
2. `chat_message(..., speak_as: "dad")`: reply auto-synthesized in the paired bank
   voice and played. Full-reply playback only in v1 (no streaming word-by-word);
   stop via existing emergency-stop pattern.
3. Web "Talk" view: pick persona, thread UI, text + auto-played audio, visible stop,
   no autoplay surprises (soft chime + "ready" first state).

Verify: mocked LLM+TTS scripted test (voice id equals pairing); manual stop-mid-reply.

## Phase 5 — Dad's grounding corpus (content, together, ongoing)

`data/voice-personas/dad/grounding.md` (his phrases, opinions, anecdotes; system
prompt rule: never invent memories, deflect unknowns as he would) +
`boundaries.md` (written before first use, shown in UI). Probe tests: known story
told right, unknown deflected, out-of-bounds refused.

## Phase 6 — Hardening (~1/2 day)

Docs (`voice-bank.md`, `voice-personas.md`, tools-reference, private-voices note),
gates (`pytest -m "not live"`, ruff, biome, tsc), `.gitignore` for
`data/voice-bank/` + `data/voice-personas/` verified via `git status`, backup drill.

## Sequencing

Phase 1+2 first (unblock everything, touch nothing in daily use) → 3 → 4 → 5
alongside → 6. Max 5 files per change, `.bak` guards, no commits unasked.

## Mirror + memory

- Fleet mirror: `mcp-central-docs/projects/speech-mcp/docs_VOICE_CLONE_BANK_PLAN.md`.
- memops note: FAILED to write 2026-09-17 — memops embedding backend down
  (`cudnn64_9.dll` missing, ONNX CUDA provider). Retry `adn_notes write` later;
  content above is the source of truth until then.
