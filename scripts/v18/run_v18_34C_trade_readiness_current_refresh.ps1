[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$ApplyRefresh
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_34C_trade_readiness_current_refresh.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$reportPath = Join-Path $Root "outputs\v18\read_center\V18_34C_TRADE_READINESS_REFRESH_REPORT.md"
$readinessPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_TRADE_READINESS.md"
$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_34C_READ_FIRST.txt"

Write-Host "=== START V18.34C TRADE READINESS CURRENT REFRESH ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "APPLY_REFRESH: $($ApplyRefresh.IsPresent)"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @($scriptPath, "--root", $Root)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($ApplyRefresh.IsPresent) {
    $argsList += "--apply-refresh"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
$backupLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
    $backupLine = (Select-String -Path $readFirstPath -Pattern '^BACKUP_PATH:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.34C TRADE READINESS CURRENT REFRESH ==="
Write-Host $statusLine
Write-Host $backupLine
Write-Host "REPORT: $reportPath"
Write-Host "READINESS: $readinessPath"
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
