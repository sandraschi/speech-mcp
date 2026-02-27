# Speech-MCP SOTA Dual-Server Launcher
# Port 10760: FastAPI Backend + MCP SSE (webapp mode)
# Port 10761: Vite Frontend

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendPort = 10760
$FrontendPort = 10761
$VenvPython = "$ProjectRoot\.venv\Scripts\python.exe"

Write-Host "--- Speech-MCP SOTA Launcher ---" -ForegroundColor Cyan
Write-Host "Backend:  http://localhost:$BackendPort" -ForegroundColor DarkGray
Write-Host "Frontend: http://localhost:$FrontendPort" -ForegroundColor DarkGray

# 1. Kill zombies on reserved ports
Write-Host "Cleaning up ports $BackendPort and $FrontendPort..." -ForegroundColor Yellow

$BackendJob = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if ($BackendJob) {
    $BackendJob | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Host "Cleared port $BackendPort" -ForegroundColor DarkYellow
}

$FrontendJob = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
if ($FrontendJob) {
    $FrontendJob | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    Write-Host "Cleared port $FrontendPort" -ForegroundColor DarkYellow
}

# 2. Start Backend (webapp mode: FastAPI + MCP SSE)
if (-not (Test-Path $VenvPython)) {
    Write-Host "ERROR: .venv not found at $VenvPython" -ForegroundColor Red
    Write-Host "Run: uv sync" -ForegroundColor Yellow
    exit 1
}

Write-Host "Launching Backend (webapp) on port $BackendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "`$env:PYTHONPATH='$ProjectRoot\src'; & '$VenvPython' -m speech_mcp.webapp"

Start-Sleep -Seconds 2

# 3. Start Frontend
Write-Host "Launching Frontend on port $FrontendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "Set-Location '$ProjectRoot\web'; npm run dev"

Write-Host "Both servers are starting. Open http://localhost:$FrontendPort" -ForegroundColor Cyan
