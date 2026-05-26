[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$ApplyRepair,
    [string]$SignalDateOverride = ""
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_32D_latest_supported_signal_date_freeze_repair.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_32D_READ_FIRST.txt"
$reportPath = Join-Path $Root "outputs\v18\read_center\V18_32D_FREEZE_REPAIR_REPORT.md"
$currentPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_FREEZE_COVERAGE_REPAIR.md"

Write-Host "=== START V18.32D LATEST SUPPORTED SIGNAL-DATE FREEZE REPAIR ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "APPLY_REPAIR: $($ApplyRepair.IsPresent)"
Write-Host "SIGNAL_DATE_OVERRIDE: $SignalDateOverride"
Write-Host "MODE: LATEST_SUPPORTED_SIGNAL_DATE_FREEZE_REPAIR"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"
Write-Host "EXTERNAL_FETCH: NOT_EXECUTED"
Write-Host "BACKTEST_EXECUTED: FALSE"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($ApplyRepair.IsPresent) {
    $argsList += "--apply-repair"
}
if ($SignalDateOverride -ne "") {
    $argsList += "--signal-date-override"
    $argsList += $SignalDateOverride
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.32D LATEST SUPPORTED SIGNAL-DATE FREEZE REPAIR ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "REPORT: $reportPath"
Write-Host "CURRENT: $currentPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
