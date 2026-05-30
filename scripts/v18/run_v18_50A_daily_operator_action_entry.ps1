param(
    [string]$ProjectRoot = "D:\us-tech-quant",
    [switch]$WriteCurrent,
    [switch]$Strict,
    [switch]$VerboseLog,
    [switch]$WriteRealPositionBookFromUploads
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

$Script = Join-Path $ProjectRoot "scripts\v18\v18_50A_daily_operator_action_entry.py"
$Script50B = Join-Path $ProjectRoot "scripts\v18\v18_50B_current_alias_authoritative_source_repair.py"
$ReadFirst = Join-Path $ProjectRoot "outputs\v18\ops\V18_50A_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.50A"
Write-Host "PATCH_NAME: DAILY_OPERATOR_ACTION_ENTRY"
Write-Host "READ_ONLY_ORCHESTRATION: TRUE"
Write-Host "WRITE_REAL_POSITION_BOOK_FROM_UPLOADS: $($WriteRealPositionBookFromUploads.ToString().ToUpper())"
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
if (-not (Test-Path $Script50B)) {
    throw "Missing V18.50B-R2 validation script: $Script50B"
}

Write-Host "RUNNING_V18_50B_R2_PRE_PACKET_VALIDATION: TRUE"
& $Python $Script50B --project-root $ProjectRoot
if ($LASTEXITCODE -ne 0) {
    Write-Host "V18_50B_R2_PRE_PACKET_VALIDATION_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    exit $LASTEXITCODE
}

$Args50A = @("--project-root", $ProjectRoot)
if ($WriteCurrent) {
    $Args50A += "--write-current"
}
if ($WriteRealPositionBookFromUploads) {
    $Args50A += "--write-real-position-book-from-uploads"
}
if ($VerboseLog) {
    Write-Host "PYTHON: $Python"
    Write-Host "ARGS: $($Args50A -join ' ')"
}

& $Python $Script @Args50A
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.50A READ_FIRST ---"
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
