param(
    [string]$ProjectRoot = "D:\us-tech-quant",
    [switch]$WriteCurrent,
    [switch]$Strict,
    [switch]$VerboseLog,
    [switch]$CreateRealPositionTemplate
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
    $Python = "python"
}

$Script = Join-Path $ProjectRoot "scripts\v18\v18_49C_dual_book_buy_sell_action_planner.py"
$ReadFirst = Join-Path $ProjectRoot "outputs\v18\ops\V18_49C_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.49C"
Write-Host "PATCH_NAME: DUAL_BOOK_BUY_SELL_ACTION_PLANNER"
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

$Args49C = @("--project-root", $ProjectRoot)
if ($WriteCurrent) {
    $Args49C += "--write-current"
}
if ($CreateRealPositionTemplate) {
    $Args49C += "--create-real-position-template"
}
if ($VerboseLog) {
    Write-Host "PYTHON: $Python"
    Write-Host "ARGS: $($Args49C -join ' ')"
}

& $Python $Script @Args49C
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.49C READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if ($Strict -and (Test-Path $ReadFirst)) {
    $StatusLine = Get-Content -Path $ReadFirst | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
    if ($StatusLine -like "STATUS: WARN_*") {
        exit 2
    }
}

exit 0
