[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [double]$AccountSizeUsd = 2000,
    [double]$CashUsd = -1,
    [double]$CashReservePct = 15,
    [string]$AccountStateFile = "",
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_32A_manual_account_state_validator.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_32A_READ_FIRST.txt"
$guidePath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_MANUAL_ACCOUNT_STATE_GUIDE.md"

Write-Host "=== START V18.32A MANUAL ACCOUNT STATE VALIDATOR ==="
Write-Host "ROOT: $Root"
Write-Host "ACCOUNT_SIZE_USD: $AccountSizeUsd"
Write-Host "CASH_USD: $CashUsd"
Write-Host "CASH_RESERVE_PCT: $CashReservePct"
Write-Host "ACCOUNT_STATE_FILE: $AccountStateFile"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: MANUAL_ACCOUNT_STATE_VALIDATOR"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"
Write-Host "EXTERNAL_DATA_FETCH: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--account-size-usd", $AccountSizeUsd,
    "--cash-reserve-pct", $CashReservePct
)
if ($CashUsd -ne -1) {
    $argsList += "--cash-usd"
    $argsList += $CashUsd
}
if ($AccountStateFile -ne "") {
    $argsList += "--account-state-file"
    $argsList += $AccountStateFile
}
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($Strict.IsPresent) {
    $argsList += "--strict"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.32A MANUAL ACCOUNT STATE VALIDATOR ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "GUIDE: $guidePath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
