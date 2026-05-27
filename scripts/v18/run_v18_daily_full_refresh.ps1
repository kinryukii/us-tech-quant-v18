param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$CommandCenter = Join-Path $Root "scripts\v18\run_v18_current_daily_command_center.ps1"
if (-not (Test-Path $CommandCenter)) {
    throw "Missing command center wrapper: $CommandCenter"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $CommandCenter -RefreshMode Full
exit $LASTEXITCODE
