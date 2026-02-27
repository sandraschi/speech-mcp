$WebPort = 10761
npx --yes kill-port $WebPort 2>$null

Write-Host "Starting Speech-MCP Webapp on port $WebPort..." -ForegroundColor Cyan

# Install dependencies if node_modules is missing
if (-not (Test-Path "node_modules")) {
    npm install
}

# Run dev server on specific port
$env:PORT = $WebPort
npm run dev -- --port $WebPort --host
