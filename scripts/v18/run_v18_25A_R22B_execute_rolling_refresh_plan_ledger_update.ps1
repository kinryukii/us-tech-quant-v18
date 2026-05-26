[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [int]$MaxTickers = 65,
    [string]$PlanPath = "outputs\v18\rolling_coverage\V18_25A_R22_CURRENT_MULTI_RUN_REFRESH_PLAN.csv",
    [string]$LedgerPath = "state\v18\rolling_coverage\V18_23B_ROLLING_SCAN_LEDGER.csv"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R22B_execute_rolling_refresh_plan_ledger_update.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R22B_READ_FIRST.txt"

Write-Host "=== START V18.25A-R22B EXECUTE ROLLING REFRESH PLAN LEDGER UPDATE ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "PLAN_PATH: $PlanPath"
Write-Host "LEDGER_PATH: $LedgerPath"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_LOCAL_VALIDATION_ONLY' } else { 'APPLY_LEDGER_UPDATE_LOCAL_ONLY' })"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers,
    "--plan-path", $PlanPath,
    "--ledger-path", $LedgerPath
)

if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R22B executor failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R22B EXECUTE ROLLING REFRESH PLAN LEDGER UPDATE ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
