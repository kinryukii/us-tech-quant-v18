[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_34B_daily_output_freshness_guard.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$reportPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_OUTPUT_FRESHNESS.md"
$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_34B_READ_FIRST.txt"

Write-Host "=== START V18.34B DAILY OUTPUT FRESHNESS GUARD ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @($scriptPath, "--root", $Root)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
$summaryLine = ""
$gapLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
    $summaryLine = (Select-String -Path $readFirstPath -Pattern '^1\. ' | Select-Object -First 1).Line
    $gapLine = (Select-String -Path $reportPath -Pattern '^(- MAX_KEY_FILE_GAP_HOURS:|MAX_KEY_FILE_GAP_HOURS:)' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.34B DAILY OUTPUT FRESHNESS GUARD ==="
Write-Host $statusLine
Write-Host "REPORT: $reportPath"
Write-Host "READ_FIRST: $readFirstPath"
if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
