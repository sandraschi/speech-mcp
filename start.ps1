# SOTA Dual-Server Launcher
# Port 10760: FastAPI Backend + MCP SSE
# Port 10761: Vite Frontend

$BackendPort = 10760
$FrontendPort = 10761

Write-Host "--- SOTA Lifecycle Management: speech-mcp ---" -ForegroundColor Cyan

# 1. Kill zombies on reserved ports
Write-Host "Cleaning up ports $BackendPort and $FrontendPort..." -ForegroundColor Yellow
$BackendJob = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
if ($BackendJob) {
    $BackendJob | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

$FrontendJob = Get-NetTCPConnection -LocalPort $FrontendPort -ErrorAction SilentlyContinue
if ($FrontendJob) {
    $FrontendJob | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
}

# 2. Start Backend
Write-Host "Launching Backend on port $BackendPort..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m speech_mcp.server"

# 3. Start Frontend
Write-Host "Launching Frontend on port $FrontendPort..." -ForegroundColor Green
Set-Location web
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "Dual servers are spawning. Check the pop-out shells for logs." -ForegroundColor DarkCyan
