set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
set shell := ["pwsh.exe", "-NoLogo", "-Command"]
set dotenv-load := true

# ── Dashboard ──────────────────────────────────────────────────────────────────

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# ── Dev ────────────────────────────────────────────────────────────────────────

# Install / sync all dependencies
install:
    Set-Location '{{justfile_directory()}}'
    uv sync

# Start the FastAPI webapp backend (port 10909)
backend:
    Set-Location '{{justfile_directory()}}'
    $env:SPEECH_MCP_PORT = '10909'; uv run python -m speech_mcp.webapp

# Start the Vite frontend (port 10908)
frontend:
    Set-Location '{{justfile_directory()}}\web'
    npm run dev -- --port 10908

# Start both backend and frontend (two tabs)
start:
    Set-Location '{{justfile_directory()}}'
    .\start.ps1

# ── Demo — TTS ─────────────────────────────────────────────────────────────────

# Quick sanity check: Windows SAPI5 speaks immediately, no API key needed
demo-windows:
    @uv run python scripts/demos/demo_windows.py

# Gemini 3.1 Flash TTS — Dramatic Shakespeare monologue (Hamlet)
demo-shakespeare:
    @uv run python scripts/demos/demo_shakespeare.py

# Gemini 3.1 Flash TTS — Japanese literary reading (Neko)
demo-neko:
    @uv run python scripts/demos/demo_neko.py

# Gemini 3.1 Flash TTS — plain voice, no tags (requires GOOGLE_API_KEY in .env)
demo-gemini-plain:
    @uv run python scripts/demos/demo_gemini_plain.py

# Gemini 3.1 Flash TTS — audio tags demo (excited + whisper)
demo-gemini-tags:
    @uv run python scripts/demos/demo_gemini_tags.py

# Gemini 3.1 Flash TTS — dramatic scene-direction prompt
demo-gemini-scene:
    @uv run python scripts/demos/demo_gemini_scene.py

# Hume AI Octave TTS — dynamic voice with description (requires HUME_API_KEY in .env)
demo-hume:
    @uv run python scripts/demos/demo_hume.py

# Hume AI Octave TTS — "Vincent Price" style description
demo-price:
    @uv run python scripts/demos/demo_price.py

# ElevenLabs TTS — play with a named voice (requires ELEVENLABS_API_KEY + voice ID)
demo-elevenlabs voice_id="":
    Set-Location '{{justfile_directory()}}'
    uv run python -c " \
    import sys, os; sys.path.insert(0, 'src'); \
    from dotenv import load_dotenv; load_dotenv(); \
    from elevenlabs.client import ElevenLabs; \
    import tempfile, subprocess; \
    vid = '{{voice_id}}' or os.environ.get('EL_DEFAULT_VOICE', ''); \
    if not vid: print('Usage: just demo-elevenlabs voice_id=<id>  (get IDs from: just demo-el-list)'); exit(1); \
    client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY']); \
    audio = bytearray([c for chunk in client.text_to_speech.convert(voice_id=vid, text='The reductionist universe has no room for miracles, but plenty of room for wonder.', output_format='mp3_44100_128') for c in chunk]); \
    tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False); tmp.write(audio); tmp.close(); \
    print(f'ElevenLabs TTS: {len(audio)} bytes, playing...'); \
    subprocess.run(['wmplayer.exe', '/play', '/close', tmp.name]); \
    import os as _os; _os.remove(tmp.name); print('OK')"

# ElevenLabs — list all voices in your account
demo-el-list:
    Set-Location '{{justfile_directory()}}'
    uv run python -c " \
    import sys, os; sys.path.insert(0, 'src'); \
    from dotenv import load_dotenv; load_dotenv(); \
    from elevenlabs.client import ElevenLabs; \
    client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY']); \
    voices = client.voices.get_all(); \
    print(f'{len(voices.voices)} voices:'); \
    [print(f'  {v.voice_id}  {v.name}  ({getattr(v, \"category\", \"\")}') for v in sorted(voices.voices, key=lambda v: v.name)]"

# ElevenLabs IVC — instant voice clone from an audio file
# Usage: just demo-el-clone name="Benny" file="C:/path/to/sample.wav"
demo-el-clone name="" file="":
    Set-Location '{{justfile_directory()}}'
    uv run python -c " \
    import sys, os; sys.path.insert(0, 'src'); \
    from dotenv import load_dotenv; load_dotenv(); \
    name = '{{name}}'; path = '{{file}}'; \
    if not name or not path: print('Usage: just demo-el-clone name=\"MyVoice\" file=\"C:/path/to/audio.wav\"'); exit(1); \
    from elevenlabs.client import ElevenLabs; \
    client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY']); \
    with open(path, 'rb') as f: result = client.voices.ivc.create(name=name, files=[f]); \
    print(f'Cloned! voice_id={result.voice_id}  name={name}'); \
    print(f'Use: just demo-elevenlabs voice_id={result.voice_id}')"

# ElevenLabs text_to_dialogue — two voices in a natural conversation
# Requires two voice IDs from your account
demo-el-dialogue v1="" v2="":
    Set-Location '{{justfile_directory()}}'
    uv run python -c " \
    import sys, os; sys.path.insert(0, 'src'); \
    from dotenv import load_dotenv; load_dotenv(); \
    v1 = '{{v1}}'; v2 = '{{v2}}'; \
    if not v1 or not v2: print('Usage: just demo-el-dialogue v1=<voice_id> v2=<voice_id>'); exit(1); \
    from elevenlabs.client import ElevenLabs; from elevenlabs import DialogueInput; \
    import tempfile, subprocess; \
    client = ElevenLabs(api_key=os.environ['ELEVENLABS_API_KEY']); \
    inputs = [ \
        DialogueInput(text='Have you tried that new Gemini TTS model yet?', voice_id=v1), \
        DialogueInput(text='Yes! The audio tags are genuinely impressive. [excited] I had it whisper philosophy at me.', voice_id=v2), \
        DialogueInput(text='[laughs] That sounds exactly like something Sandra would do.', voice_id=v1), \
        DialogueInput(text='[softly] Sin temor y sin esperanza.', voice_id=v2), \
    ]; \
    audio = bytearray([c for chunk in client.text_to_dialogue.convert(inputs=inputs, output_format='mp3_44100_128') for c in chunk]); \
    tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False); tmp.write(audio); tmp.close(); \
    print(f'Dialogue: {len(audio)} bytes, {len(inputs)} lines, playing...'); \
    subprocess.run(['wmplayer.exe', '/play', '/close', tmp.name]); \
    import os as _os; _os.remove(tmp.name); print('OK')"
    just demo-windows
    just demo-gemini-plain
    just demo-hume

# ── Demo — Wake word ───────────────────────────────────────────────────────────

# List available openWakeWord keywords
demo-wake-keywords:
    @Write-Host 'openWakeWord keywords: "computer", "alexa", "hey_jarvis", "hey_google"' -ForegroundColor Cyan
    @Write-Host 'Use the configure_local_wake_word MCP tool in a Claude session to activate.' -ForegroundColor Gray

# Run the interactive weather demo with Gemini voice (Optional city parameter)
# Usage: just demo-weather city="London"
demo-weather city="Vienna":
    @uv run python scripts/demos/demo_weather.py "{{city}}"

# Interactive weather demo that asks for a city first
demo-weather-ask:
    @pwsh -Command "$city = Read-Host 'Which city do you want to check?'; just demo-weather $city"

# Semantic search over the RAG knowledge base
demo-rag:
    @uv run python scripts/demos/demo_rag.py

# Social-engineering safety validator demo
demo-safety:
    @uv run python scripts/demos/demo_safety.py

# ── Demo — Gemini Live ────────────────────────────────────────────────────────

# Gemini Live 3.1 — CLI-based interaction test
demo-live:
    @uv run python scripts/demos/demo_gemini_live.py

# Gemini Live 3.1 — Instructions for high-fidelity UI demo
demo-live-ui:
    @Write-Host 'To run the Gemini Live UI Demo:' -ForegroundColor Cyan
    @Write-Host '1. Run `just start` to launch backend and frontend' -ForegroundColor White
    @Write-Host '2. Navigate to http://localhost:10908/voice-chat' -ForegroundColor White
    @Write-Host '3. Select a voice (e.g., Kore) and click "Start Session"' -ForegroundColor White
    @Write-Host '4. Speak into your mic or inject text for low-latency barge-in.' -ForegroundColor White

# ── Distribution (MCPB + Tauri) ───────────────────────────────────────────────

# Build Vite webapp only (dev proxy; Tauri sets VITE_API_BASE in build.ps1)
build-webapp:
    Set-Location '{{justfile_directory()}}\web'
    npm install
    npm run build

# MCPB bundle for Claude Desktop (drag-and-drop install)
mcpb-pack:
    Set-Location '{{justfile_directory()}}'
    npx -y @anthropic-ai/mcpb pack . dist/speech-mcp-v0.6.3.mcpb

# Full local release (wheel + mcpb + Tauri) — upload to GitHub Releases
publish-release-local tag="v0.6.3":
    Set-Location '{{justfile_directory()}}'
    pwsh -NoLogo -File scripts/publish-release-local.ps1 -Tag "{{tag}}"

# Tauri native installer (Windows NSIS + MSI) — web + PyInstaller sidecar + bundle
build-native:
    Set-Location '{{justfile_directory()}}'
    pwsh -NoLogo -File native/build.ps1

build-native-debug:
    Set-Location '{{justfile_directory()}}\native'
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npx @tauri-apps/cli build --debug

# ── Quality ────────────────────────────────────────────────────────────────────

# Lint everything (Python + Justfile)
lint:
    Set-Location '{{justfile_directory()}}'
    just --fmt --check
    just --list > $null
    uv run ruff check src/

# Biome lint (Web)
lint-web:
    Set-Location '{{justfile_directory()}}\web'
    npx -y @biomejs/biome check src/

# Ruff format + autofix
fix:
    Set-Location '{{justfile_directory()}}'
    uv run ruff check src/ --fix --unsafe-fixes
    uv run ruff format src/

# Biome format + fix
fix-web:
    Set-Location '{{justfile_directory()}}\web'
    npx -y @biomejs/biome check --write src/

# Run mock-based test suite (suitable for GitHub CI)
test:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/ -v -m "not live"

# Run high-fidelity audio integration tests (Local only, produces sound)
verify-speech:
    Set-Location '{{justfile_directory()}}'
    uv run pytest tests/live/ -s -v --live

# ── Orchestration ─────────────────────────────────────────────────────────────

# Run the hardware probe to detect monitors, microphones, and cameras
probe:
    @uv run python scripts/utils/hardware_probe.py

# Optimized launch for multi-screen workflows (app defaults to blender)
# Usage: just dual-launch app="blender" monitor=1
dual-launch app="blender" monitor="1":
    @uv run python scripts/utils/orchestrator.py --app "{{app}}" --monitor {{monitor}}

# ── Maintenance ────────────────────────────────────────────────────────────────

# Re-index the RAG knowledge base from docs/
reindex:
    Set-Location '{{justfile_directory()}}'
    uv run python scripts/reindex_docs.py

# Wipe and rebuild the LanceDB vector store
reindex-clean:
    Set-Location '{{justfile_directory()}}'
    Remove-Item -Recurse -Force data\lancedb -ErrorAction SilentlyContinue
    uv run python scripts/reindex_docs.py

# Show installed dependency versions relevant to TTS
versions:
    @uv run python scripts/demos/versions.py

# Clean build artefacts and backup files
clean:
    Set-Location '{{justfile_directory()}}'
    Get-ChildItem -Recurse -Filter '*.bak' | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter '__pycache__' -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter '*.pyc' | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter '*.tmp' | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Recurse -Filter 'venv' -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host 'Workspace purged of ephemeral artifacts.' -ForegroundColor Green

# ── Speech ────────────────────────────────────────────────────────────────

# Speak some text via TTS
speak text="Hello from the fleet":
    curl -s -X POST http://127.0.0.1:10909/api/v1/tts -H "Content-Type: application/json" -d '{"text":"{{text}}"}' | python -c "import sys,json; d=json.load(sys.stdin); print('Spoken' if d.get('success') else d.get('error',''))"

# List available voices
voices:
    curl -s http://127.0.0.1:10909/api/v1/voices | python -c "import sys,json; d=json.load(sys.stdin); [print(f'  {v}') for v in (d if isinstance(d,list) else d.get('voices',[]))]"

# Show TTS status
tts-status:
    curl -s http://127.0.0.1:10909/api/v1/stats | python -c "import sys,json; d=json.load(sys.stdin); [print(f'{k}: {v}') for k,v in d.items()]"

