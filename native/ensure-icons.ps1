#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$Native = $PSScriptRoot
$IconIco = Join-Path $Native "icons\icon.ico"

if (Test-Path $IconIco) { exit 0 }

$iconPng = Join-Path $Native "icon-source.png"
Add-Type -AssemblyName System.Drawing
$size = 512
$bmp = New-Object System.Drawing.Bitmap $size, $size
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$brush = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(255, 124, 58, 237))
$g.FillRectangle($brush, 0, 0, $size, $size)
$g.Dispose()
$bmp.Save($iconPng, [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()

New-Item -ItemType Directory -Path (Join-Path $Native "icons") -Force | Out-Null
$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"
Push-Location $Native
try {
    npx @tauri-apps/cli icon $iconPng
} finally {
    Pop-Location
}

if (-not (Test-Path $IconIco)) { throw "icon.ico was not generated" }
Write-Host "Icons ready: $IconIco" -ForegroundColor Green
