Param([switch]$Headless)
$SkipFrontend = $Headless

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

# Webapp Start - Standardized SOTA (Auto-Repaired V2.6)
$WebPort = 10908
$BackendPort = 10909
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 1. Kill any process squatting on the ports
Write-Host "Checking for port squatters on $WebPort and $BackendPort..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort $WebPort, $BackendPort -ErrorAction SilentlyContinue | Where-Object { $_.OwningProcess -gt 4 } | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($p in $pids) {
    Write-Host "Found squatter (PID: $p). Terminating..." -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { Write-Host "Warning: Could not terminate PID $p." -ForegroundColor Gray }
}

# 2. Setup
Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) { npm install }

# 3. Start the Python backend (Background) and WAIT for readiness
Write-Host "Starting Python backend on port $BackendPort ..." -ForegroundColor Cyan
$backendCmd = "`$env:PYTHONPATH = '$ProjectRoot;$ProjectRoot\src'; `$env:SPEECH_MCP_PORT = '$BackendPort'; Set-Location '$ProjectRoot'; uv run python -m speech_mcp.webapp"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd -WindowStyle Normal

Write-Host "Waiting for backend to come online..." -ForegroundColor Yellow
$backendReady = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $null = Invoke-WebRequest -Uri "http://127.0.0.1:${BackendPort}/api/v1/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        $backendReady = $true
        Write-Host "Backend ready on port $BackendPort." -ForegroundColor Green
        break
    } catch {
        Start-Sleep -Seconds 1
    }
}
if (-not $backendReady) {
    Write-Host "WARNING: Backend failed to respond within 30s. Starting frontend anyway..." -ForegroundColor Red
}

# 4. Start Vite dev server (foreground)
Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green

$frontendUrl = "http://127.0.0.1:$WebPort/"
$pollAndOpen = "for (`$i = 0; `$i -lt 40; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen

Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
if ($SkipFrontend) { return }
npm run dev -- --port $WebPort --host



