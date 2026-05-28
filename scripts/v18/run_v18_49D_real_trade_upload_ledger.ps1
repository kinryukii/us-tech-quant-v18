param(
    [string]$ProjectRoot = "D:\us-tech-quant",
    [switch]$WriteCurrent,
    [switch]$Strict,
    [switch]$VerboseLog,
    [switch]$CreateTemplate,
    [switch]$WriteRealPositionBook
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

$Script = Join-Path $ProjectRoot "scripts\v18\v18_49D_real_trade_upload_ledger.py"
$ReadFirst = Join-Path $ProjectRoot "outputs\v18\ops\V18_49D_READ_FIRST.txt"
$UploadDir = Join-Path $ProjectRoot "state\v18\manual\real_trade_uploads"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.49D"
Write-Host "PATCH_NAME: REAL_TRADE_UPLOAD_LEDGER_AND_POSITION_BOOK_UPDATE"
Write-Host "READ_ONLY_MANUAL_UPLOAD_WORKFLOW: TRUE"
Write-Host "UPLOAD_DIRECTORY: $UploadDir"
Write-Host "WRITE_REAL_POSITION_BOOK_REQUESTED: $($WriteRealPositionBook.ToString().ToUpper())"
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

$Args49D = @("--project-root", $ProjectRoot)
if ($WriteCurrent) {
    $Args49D += "--write-current"
}
if ($CreateTemplate) {
    $Args49D += "--create-template"
}
if ($WriteRealPositionBook) {
    $Args49D += "--write-real-position-book"
}
if ($VerboseLog) {
    Write-Host "PYTHON: $Python"
    Write-Host "ARGS: $($Args49D -join ' ')"
}

& $Python $Script @Args49D
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.49D READ_FIRST ---"
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
