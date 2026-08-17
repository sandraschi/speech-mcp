# Per-repo fleet start config for speech-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'speech-mcp'
    BackendPort  = 10909
    FrontendPort = 10908
    HealthPath   = '/'
    WebRoot      = (Join-Path $PSScriptRoot 'web')
    Backend = @{
        Kind          = 'uvicorn'
        UvicornTarget = 'speech_mcp.server:app'
        Env           = @{ WEB_PORT = '10909' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
