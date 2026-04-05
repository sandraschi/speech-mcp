# speech-mcp full fix & launch
# Run from repo root in PowerShell

$Root = "D:\Dev\repos\speech-mcp"
$VenvPy = "$Root\.venv\Scripts\python.exe"
$Temp = "D:\Dev\repos\temp"

Set-Location $Root
$env:PYTHONPATH = "$Root\src"

Write-Host "=== 1. Kill anything on ports 10760/10761 ===" -ForegroundColor Yellow
foreach ($port in 10760, 10761) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        $conn | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Host "  Cleared port $port"
    }
}

Write-Host "=== 2. uv sync (Python deps) ===" -ForegroundColor Yellow
$uvOut = "$Temp\uvsync_$(Get-Date -Format 'HHmmss').txt"
Start-Process -FilePath "uv" -ArgumentList "sync" `
    -WorkingDirectory $Root -Wait `
    -RedirectStandardOutput $uvOut `
    -RedirectStandardError "$uvOut.err" -WindowStyle Hidden
Get-Content $uvOut -Encoding UTF8 -ErrorAction SilentlyContinue
Get-Content "$uvOut.err" -Encoding UTF8 -ErrorAction SilentlyContinue

Write-Host "=== 3. npm install (adds lucide-react) ===" -ForegroundColor Yellow
$npmOut = "$Temp\npm_$(Get-Date -Format 'HHmmss').txt"
Start-Process -FilePath "npm.cmd" -ArgumentList "install" `
    -WorkingDirectory "$Root\web" -Wait `
    -RedirectStandardOutput $npmOut `
    -RedirectStandardError "$npmOut.err" -WindowStyle Hidden
Get-Content $npmOut -Encoding UTF8 -ErrorAction SilentlyContinue
Get-Content "$npmOut.err" -Encoding UTF8 -ErrorAction SilentlyContinue

Write-Host "=== 4. Starting backend (port 10760) ===" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "`$env:PYTHONPATH='$Root\src'; & '$VenvPy' -m speech_mcp.webapp"

Start-Sleep -Seconds 3

Write-Host "=== 5. Starting frontend (port 10761) ===" -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command",
    "Set-Location '$Root\web'; npm run dev"

Write-Host ""
Write-Host "Done. Open http://localhost:10761" -ForegroundColor Cyan
Write-Host "Backend health: http://localhost:10760/api/v1/health" -ForegroundColor Cyan
