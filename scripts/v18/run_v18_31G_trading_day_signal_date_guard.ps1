[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [string]$CandidateSignalDate = "",
    [switch]$AllowNonTradingDate,
    [switch]$AllowUnknownPriceDate,
    [switch]$ApplyCleanup,
    [string]$CleanupDate = "",
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31G_trading_day_signal_date_guard.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31G_READ_FIRST.txt"
$reportPath = Join-Path $Root "outputs\v18\read_center\V18_31G_TRADING_DAY_SIGNAL_DATE_GUARD_REPORT.md"

Write-Host "=== START V18.31G TRADING-DAY SIGNAL-DATE GUARD ==="
Write-Host "ROOT: $Root"
Write-Host "CANDIDATE_SIGNAL_DATE: $CandidateSignalDate"
Write-Host "ALLOW_NON_TRADING_DATE: $($AllowNonTradingDate.IsPresent)"
Write-Host "ALLOW_UNKNOWN_PRICE_DATE: $($AllowUnknownPriceDate.IsPresent)"
Write-Host "APPLY_CLEANUP: $($ApplyCleanup.IsPresent)"
Write-Host "CLEANUP_DATE: $CleanupDate"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: TRADING_DAY_SIGNAL_DATE_GUARD"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"
Write-Host "EXTERNAL_DATA_FETCH: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($CandidateSignalDate -ne "") {
    $argsList += "--candidate-signal-date"
    $argsList += $CandidateSignalDate
}
if ($AllowNonTradingDate.IsPresent) {
    $argsList += "--allow-non-trading-date"
}
if ($AllowUnknownPriceDate.IsPresent) {
    $argsList += "--allow-unknown-price-date"
}
if ($ApplyCleanup.IsPresent) {
    $argsList += "--apply-cleanup"
}
if ($CleanupDate -ne "") {
    $argsList += "--cleanup-date"
    $argsList += $CleanupDate
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

Write-Host "=== END V18.31G TRADING-DAY SIGNAL-DATE GUARD ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "REPORT: $reportPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
