[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [ValidateSet("REPLACE","SKIP","APPEND_EXPLICIT")]
    [string]$SameDayPolicy = "REPLACE",
    [string]$SignalDateOverride = "",
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31E_daily_trade_plan_snapshot_ledger.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31E_READ_FIRST.txt"

Write-Host "=== START V18.31E DAILY TRADE PLAN SNAPSHOT LEDGER ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "SAME_DAY_POLICY: $SameDayPolicy"
Write-Host "SIGNAL_DATE_OVERRIDE: $SignalDateOverride"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: DAILY_TRADE_PLAN_SNAPSHOT_LEDGER"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN,
    "--same-day-policy", $SameDayPolicy
)
if ($SignalDateOverride -ne "") {
    $argsList += "--signal-date-override"
    $argsList += $SignalDateOverride
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

Write-Host "=== END V18.31E DAILY TRADE PLAN SNAPSHOT LEDGER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
