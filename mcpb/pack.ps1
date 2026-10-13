#Requires -Version 5.1
# DEPRECATED delegate: the canonical pack pipeline (fleet-mcpb-pack.ps1 in
# mcp-central-docs/scripts) is reached via the scripts/mcpb-pack.ps1 shim.
# This file stays only so old muscle-memory (`mcpb/pack.ps1`) keeps working;
# do not add logic here.
$shim = Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts\mcpb-pack.ps1'
if (-not (Test-Path -LiteralPath $shim)) { throw "Pack shim missing: $shim" }
& $shim @args
exit $LASTEXITCODE
