param(
    [ValidateSet("Rolling", "Full")]
    [string]$RefreshMode = "Rolling",
    [string]$Root = "D:\us-tech-quant"
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

$Script = Join-Path $Root "scripts\v18\v18_45A_current_ranked_candidate_freshness_audit.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_CURRENT_RANKED_CANDIDATE_FRESHNESS_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.45A"
Write-Host "REFRESH_MODE: $RefreshMode"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

& $Python $Script --root $Root --refresh-mode $RefreshMode
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.45A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
