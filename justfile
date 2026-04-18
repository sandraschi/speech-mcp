set windows-shell := ["pwsh.exe", "-NoLogo", "-Command"]
set shell := ["pwsh.exe", "-NoLogo", "-Command"]
set dotenv-load := true

# ── Dashboard ──────────────────────────────────────────────────────────────────

# Show all available recipes
default:
    @$lines = Get-Content '{{justfile()}}'; \
    Write-Host '  speech-mcp industrial console' -ForegroundColor White -BackgroundColor DarkBlue -NoNewline; \
    Write-Host ' (SOTA)' -ForegroundColor Cyan -BackgroundColor DarkBlue; \
    Write-Host ''; \
    $currentCategory = ''; \
    foreach ($line in $lines) { \
        if ($line -match '^# ── ([^─]+) ─') { \
            $currentCategory = $matches[1].Trim(); \
            Write-Host "`n  $currentCategory" -ForegroundColor Cyan; \
            Write-Host ('  ' + ('─' * 45)) -ForegroundColor DarkGray; \
        } elseif ($line -match '^# ([^─].+)') { \
            $desc = $matches[1].Trim(); \
            $idx = [array]::IndexOf($lines, $line); \
            if ($idx -lt $lines.Count - 1) { \
                $nextLine = $lines[$idx + 1]; \
                if ($nextLine -match '^([a-z0-9_-]+):') { \
                    $recipe = $matches[1]; \
                    $pad = ' ' * [math]::Max(2, (22 - $recipe.Length)); \
                    Write-Host "    $recipe" -ForegroundColor White -NoNewline; \
                    Write-Host "$pad$desc" -ForegroundColor Gray; \
                } \
            } \
        } \
    } \
    Write-Host ''

# ── Dev ────────────────────────────────────────────────────────────────────────

# Install / sync all dependencies
install:
    Set-Location '{{justfile_directory()}}'
    uv sync

# Start the FastAPI webapp backend (port 10918)
backend:
    Set-Location '{{justfile_directory()}}'
    uv run uvicorn speech_mcp.server:app --host 127.0.0.1 --port 10918 --reload

# Start the Vite frontend (port 10917)
frontend:
    Set-Location '{{justfile_directory()}}\web'
    npm run dev

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

# List all available built-in Porcupine keywords
demo-wake-keywords:
    Set-Location '{{justfile_directory()}}'
    uv run python -c "import pvporcupine; print('Available keywords:'); [print(f'  {k}') for k in sorted(pvporcupine.KEYWORDS)]"

# Start wake word listener for 30 seconds — say "computer" to trigger
demo-wake-word keyword="computer":
    Set-Location '{{justfile_directory()}}'
    uv run python -c " \
    import sys, os, time, threading; sys.path.insert(0, 'src'); \
    from dotenv import load_dotenv; load_dotenv(); \
    import pvporcupine, pyaudio; \
    key = os.environ.get('PICOVOICE_API_KEY', ''); \
    if not key: print('Set PICOVOICE_API_KEY in .env'); exit(1); \
    detected = threading.Event(); \
    def run(): \
        p = pvporcupine.create(access_key=key, keywords=['{{keyword}}'], sensitivities=[0.5]); \
        pa = pyaudio.PyAudio(); \
        st = pa.open(rate=p.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=p.frame_length); \
        print(f'Listening for \"{{keyword}}\" for 30s... say it!'); \
        deadline = time.time() + 30; \
        while time.time() < deadline and not detected.is_set(): \
            pcm_b = st.read(p.frame_length, exception_on_overflow=False); \
            pcm = [int.from_bytes(pcm_b[i:i+2], 'little', signed=True) for i in range(0, len(pcm_b), 2)]; \
            if p.process(pcm) >= 0: print('DETECTED: {{keyword}}!'); detected.set(); \
        st.stop_stream(); st.close(); pa.terminate(); p.delete(); \
    t = threading.Thread(target=run, daemon=True); t.start(); t.join(31); \
    print('Done.' if detected.is_set() else 'Timeout — no detection.')"

# Live weather for Vienna via wttr.in
demo-weather:
    @uv run python scripts/demos/demo_weather.py

# Semantic search over the RAG knowledge base
demo-rag:
    @uv run python scripts/demos/demo_rag.py

# Social-engineering safety validator demo
demo-safety:
    @uv run python scripts/demos/demo_safety.py

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
    Get-ChildItem -Recurse -Filter '*.bak' | Remove-Item -Force
    Get-ChildItem -Recurse -Filter '__pycache__' -Directory | Remove-Item -Recurse -Force
    Get-ChildItem -Recurse -Filter '*.pyc' | Remove-Item -Force
