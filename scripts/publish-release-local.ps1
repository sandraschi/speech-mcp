#!/usr/bin/env pwsh
# Local release deliverables: wheel + mcpb + Tauri installers → GitHub Release
# Use when Actions runners are unavailable (no Windows job on GitHub).
param(
    [string]$Tag = "v0.6.3",
    [switch]$SkipTauri,
    [switch]$SkipPack
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path dist)) { New-Item -ItemType Directory -Path dist | Out-Null }

if (-not $SkipPack) {
    Write-Host "=== wheel + sdist ===" -ForegroundColor Cyan
    uv build
    Write-Host "=== MCPB ===" -ForegroundColor Cyan
    npx -y @anthropic-ai/mcpb pack . "dist/speech-mcp-$Tag.mcpb"
}

if (-not $SkipTauri) {
    Write-Host "=== Tauri (native/build.ps1) ===" -ForegroundColor Cyan
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    pwsh -NoLogo -File "$Root\native\build.ps1"
}

$uploads = @(
    "dist/speech_mcp-*.whl",
    "dist/speech_mcp-*.tar.gz",
    "dist/speech-mcp-*.mcpb",
    "native/target/release/bundle/nsis/*.exe",
    "native/target/release/bundle/msi/*.msi"
)
$files = foreach ($g in $uploads) { Get-Item $g -ErrorAction SilentlyContinue }
if (-not $files) { throw "No release files found under dist/ or native/target/..." }

Write-Host "=== Upload to $Tag ===" -ForegroundColor Cyan
foreach ($f in $files) {
    Write-Host "  $($f.FullName)"
    gh release upload $Tag $f.FullName --clobber
}

Write-Host "Done: https://github.com/sandraschi/speech-mcp/releases/tag/$Tag" -ForegroundColor Green
