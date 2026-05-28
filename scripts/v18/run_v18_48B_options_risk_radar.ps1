param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$WriteCurrent
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
if (-not (Test-Path $Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_48B_options_risk_radar.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_48B_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.48B"
Write-Host "PATCH_NAME: Options Risk Radar"
Write-Host "READ_ONLY: TRUE"
Write-Host "OFFICIAL_RANKING_CHANGED: FALSE"
Write-Host "FACTOR_WEIGHTS_CHANGED: FALSE"
Write-Host "OFFICIAL_BUY_PERMISSION_CHANGED: FALSE"
Write-Host "OFFICIAL_SELL_PERMISSION_CHANGED: FALSE"
Write-Host "OPTIONS_TRADE_RECOMMENDATION_CREATED: FALSE"
Write-Host "OPTIONS_TRADE_EXECUTION_ALLOWED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args48B = @("--root", $Root)
if ($WriteCurrent) {
    $Args48B += "--write-current"
}

& $Python $Script @Args48B
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.48B READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
