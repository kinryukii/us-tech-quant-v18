param(
    [string]$ProjectRoot = "D:\us-tech-quant",
    [switch]$WriteCurrent,
    [switch]$Strict,
    [switch]$VerboseLog
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
if (-not (Test-Path $ProjectRoot)) {
    $ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $AltPython = "$ProjectRoot.venv\Scripts\python.exe"
    if (Test-Path $AltPython) {
        $Python = $AltPython
    }
    else {
        $Python = "python"
    }
}

$Script = Join-Path $ProjectRoot "scripts\v18\v18_49A_factor_weight_buy_sell_policy_backtest.py"
$ReadFirst = Join-Path $ProjectRoot "outputs\v18\ops\V18_49A_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.49A-R1"
Write-Host "PATCH_NAME: POINT_IN_TIME_EVIDENCE_AND_EXIT_DATE_REPAIR"
Write-Host "READ_ONLY: TRUE"
Write-Host "OFFICIAL_RANKING_CHANGED: FALSE"
Write-Host "FACTOR_WEIGHTS_CHANGED: FALSE"
Write-Host "OFFICIAL_BUY_PERMISSION_CHANGED: FALSE"
Write-Host "OFFICIAL_SELL_PERMISSION_CHANGED: FALSE"
Write-Host "REAL_TRADE_EXECUTION_ALLOWED: FALSE"
Write-Host "OPTIONS_TRADE_EXECUTION_ALLOWED: FALSE"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "ORDER_EXECUTION_USED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args49A = @("--project-root", $ProjectRoot)
if ($WriteCurrent) {
    $Args49A += "--write-current"
}
if ($VerboseLog) {
    Write-Host "PYTHON: $Python"
    Write-Host "ARGS: $($Args49A -join ' ')"
}

& $Python $Script @Args49A
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.49A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if ($Strict -and (Test-Path $ReadFirst)) {
    $StatusLine = Get-Content -Path $ReadFirst | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
    if ($StatusLine -like "STATUS: WARN_V18_49A_INSUFFICIENT_BACKTEST_EVIDENCE*" -or
        $StatusLine -like "STATUS: WARN_V18_49A_MISSING_PRICE_HISTORY*" -or
        $StatusLine -like "STATUS: WARN_V18_49A_MISSING_CANDIDATE_HISTORY*") {
        exit 2
    }
}

exit 0
