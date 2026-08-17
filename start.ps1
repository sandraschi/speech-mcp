# Fleet unified launcher - delegates to web/start.ps1 (webapp stack).
# Keep the fleet switches here so `just start` / cua-webapp-test work identically.
param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser,
    [switch]$ReuseIfRunning
)

$webStart = Join-Path $PSScriptRoot 'web\start.ps1'
if (-not (Test-Path -LiteralPath $webStart)) {
    Write-Host "ERROR: web launcher missing: $webStart" -ForegroundColor Red
    exit 1
}
& $webStart @PSBoundParameters
exit $LASTEXITCODE
