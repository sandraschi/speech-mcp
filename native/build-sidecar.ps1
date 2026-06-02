#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== speech-mcp sidecar build ===" -ForegroundColor Cyan
Push-Location $Root
try {
    $pi = uv run pyinstaller --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        uv pip install pyinstaller
    }
    Remove-Item -Recurse -Force "$Root\build\speech-mcp-backend" -ErrorAction SilentlyContinue
    Remove-Item -Force "$Root\dist\speech-mcp-backend.exe" -ErrorAction SilentlyContinue
    uv run pyinstaller speech-mcp-backend.spec --clean --noconfirm
    if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }
    $triple = "x86_64-pc-windows-msvc"
    $src = "$Root\dist\speech-mcp-backend.exe"
    $dstDir = "$Root\native\binaries"
    $dst = "$dstDir\speech-mcp-backend-$triple.exe"
    if (-not (Test-Path $src)) { throw "Missing $src" }
    New-Item -ItemType Directory -Path $dstDir -Force | Out-Null
    Copy-Item $src $dst -Force
    Write-Host "Sidecar: $dst" -ForegroundColor Green
} finally {
    Pop-Location
}
