# Troubleshooting — speech-mcp

## Backend won't start / port busy

```
Get-NetTCPConnection -LocalPort 10909 -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force }
```

Port 10909 must be free before the backend binds. Same for frontend 10908 and the
FunASR sidecar 10914.

## Webapp shows "Backend offline"

1. Backend running? `just backend` or `just start` (delegates to `web/start.ps1`).
2. Health check: `Invoke-RestMethod http://127.0.0.1:10909/api/v1/health` — expect
   `status: healthy`.
3. Vite proxy: the webapp calls `/api` which `web/vite.config.ts` proxies to 10909.
   In the built Tauri app the backend must be spawned by the native shell
   (`native/src/backend.rs` — see `%LOCALAPPDATA%\ai.fleet.speech-mcp\backend-spawn.log`).
4. Auth: if `SPEECH_MCP_AUTH_TOKEN` is set, API calls need the
   `X-Speech-MCP-Auth` header (the webapp stores it in localStorage).

## TTS silent / no sound

- Provider status: `GET /api/v1/health` → `providers` map. `windows` is always
  available (SAPI5); others need their API key.
- Try the Windows provider first: `just speak text="hello"` (defaults to windows).
- Check the server speaker/audio device — the app plays audio on the HOST speaker.

## FunASR STT not available

- `GET /api/v1/health` → `funasr.available: false`.
- Native mode needs `uv sync --extra funasr` + `FUNASR_ENABLED=true`.
- Or use the sidecar: `uv run python scripts/start_funasr_sidecar.py` (port 10914)
  and set `FUNASR_OPENAI_URL=http://127.0.0.1:10914/v1`.
- Sidecar port 10914 is fleet-registered — do not revert to 10910 (rtorrent-mcp).

## Wake word doesn't trigger

- `configure_local_wake_word(action="status")` — listener thread alive?
- openWakeWord runs fully offline; check the mic is the default input device.
- Fleet bus mode: `FLEET_VOICE_DELEGATE=1` must be set before startup; the
  listener auto-starts unless `FLEET_VOICE_AUTOSTART=0`.

## CUA-NSIS smoke test fails

- The test installs the NSIS build silently. Prereqs: Tesseract OCR at
  `C:\Program Files\Tesseract-OCR\tesseract.exe`, pywinauto + Pillow +
  pytesseract in the venv.
- `GET /api/v1/diagnostics` must return 200 with the tool list (phase 6).
- Nav walk needs `nav_routes` in `scripts/cua-nsis-config.json` — matches the
  real sidebar labels. Screenshots land in `cua-reports/`.

## Native build problems

- `just build-native` runs the full pipeline. Gates: `tsc --noEmit` must pass
  (frontend dir is `web/`), backend exe must be >= 5 MB (PyInstaller size gate),
  `run_server.py` must exist.
- `native/resources/` is populated by the build script — a bare `cargo check`
  fails without the staged backend exe; run `native/build.ps1` instead.
- Backend spawn log: `%LOCALAPPDATA%\ai.fleet.speech-mcp\backend-spawn.log`.

## Diagnostics

`GET /api/v1/diagnostics` — status, version, uptime, tool count, tools, system.

## Logs

- Live log stream: `web/src/components/SystemLogs.tsx` → `ws://127.0.0.1:10909/ws/logs`
- Query in-chat: `query_logs(level="ERROR")` (aiwatcher-style ring buffer).
