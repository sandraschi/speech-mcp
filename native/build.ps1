#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== speech-mcp Tauri release build ===" -ForegroundColor Cyan

Write-Host "[1/3] web (VITE_API_BASE for Tauri)" -ForegroundColor Yellow
Push-Location "$Root\web"
try {
    $env:VITE_API_BASE = "http://127.0.0.1:10909"
    npm install
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "Vite build failed" }
} finally { Pop-Location }

Write-Host "[2/3] PyInstaller sidecar" -ForegroundColor Yellow
pwsh -NoLogo -File "$Root\native\build-sidecar.ps1"

Write-Host "[3/3] Tauri bundle" -ForegroundColor Yellow
Push-Location "$Root\native"
try {
    $env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
    npm install
    if (-not (Test-Path "icons\icon.ico")) {
        pwsh -NoLogo -File "$Root\native\ensure-icons.ps1"
    }
    npx @tauri-apps/cli build
    if ($LASTEXITCODE -ne 0) { throw "Tauri build failed" }
} finally { Pop-Location }

Write-Host "Done. Installers: native\target\release\bundle\" -ForegroundColor Green
