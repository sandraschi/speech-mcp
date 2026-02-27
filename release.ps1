# release.ps1 - SOTA Release Orchestrator
# Automates versioning, tagging, and deployment triggers

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("patch", "minor", "major")]
    [string]$Type,

    [Parameter(Mandatory = $false)]
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Starting Release Orchestration ($Type)..." -ForegroundColor Cyan

# 1. Ensure working directory is clean
$status = git status --porcelain
if ($status) {
    Write-Error "Git working directory is not clean. Commit or stash changes first."
}

# 2. Get current version from pyproject.toml
$content = Get-Content pyproject.toml -Raw
if ($content -match 'version = "(\d+\.\d+\.\d+)"') {
    $currentVersion = $matches[1]
    Write-Host "Current version: $currentVersion" -ForegroundColor Yellow
}
else {
    Write-Error "Could not find version in pyproject.toml"
}

# 3. Calculate new version
$v = [version]$currentVersion
$newVersion = ""
if ($Type -eq "patch") { $newVersion = "$($v.Major).$($v.Minor).$($v.Build + 1)" }
elseif ($Type -eq "minor") { $newVersion = "$($v.Major).$($v.Minor + 1).0" }
elseif ($Type -eq "major") { $newVersion = "$($v.Major + 1).0.0" }

Write-Host "New version: $newVersion" -ForegroundColor Green

# 4. Update pyproject.toml
$newContent = $content -replace "version = `"$currentVersion`"", "version = `"$newVersion`""
Set-Content pyproject.toml $newContent -NoNewline

# 5. Update uv.lock
Write-Host "Updating uv.lock..." -ForegroundColor Gray
uv lock

# 6. Commit and Tag
if (-not $Message) { $Message = "release: v$newVersion" }

git add pyproject.toml uv.lock
git commit -m $Message
git tag -a "v$newVersion" -m $Message

Write-Host "✅ Release prepared locally: v$newVersion" -ForegroundColor Green
Write-Host "To push and trigger CI/CD:" -ForegroundColor Gray
Write-Host "  git push origin main --tags" -ForegroundColor Cyan
