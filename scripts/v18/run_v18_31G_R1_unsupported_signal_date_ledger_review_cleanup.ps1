[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [string]$CleanupDate = "",
    [switch]$ApplyCleanup,
    [string]$LatestSupportedSignalDate = "",
    [switch]$AllowCleanupNonWeekend,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31G_R1_unsupported_signal_date_ledger_review_cleanup.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31G_R1_READ_FIRST.txt"
$reportPath = Join-Path $Root "outputs\v18\read_center\V18_31G_R1_UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW_REPORT.md"

Write-Host "=== START V18.31G-R1 UNSUPPORTED SIGNAL-DATE LEDGER REVIEW ==="
Write-Host "ROOT: $Root"
Write-Host "CLEANUP_DATE: $CleanupDate"
Write-Host "APPLY_CLEANUP: $($ApplyCleanup.IsPresent)"
Write-Host "LATEST_SUPPORTED_SIGNAL_DATE: $LatestSupportedSignalDate"
Write-Host "ALLOW_CLEANUP_NON_WEEKEND: $($AllowCleanupNonWeekend.IsPresent)"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: UNSUPPORTED_SIGNAL_DATE_LEDGER_REVIEW"
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
if ($CleanupDate -ne "") {
    $argsList += "--cleanup-date"
    $argsList += $CleanupDate
}
if ($ApplyCleanup.IsPresent) {
    $argsList += "--apply-cleanup"
}
if ($LatestSupportedSignalDate -ne "") {
    $argsList += "--latest-supported-signal-date"
    $argsList += $LatestSupportedSignalDate
}
if ($AllowCleanupNonWeekend.IsPresent) {
    $argsList += "--allow-cleanup-non-weekend"
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

Write-Host "=== END V18.31G-R1 UNSUPPORTED SIGNAL-DATE LEDGER REVIEW ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "REPORT: $reportPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
