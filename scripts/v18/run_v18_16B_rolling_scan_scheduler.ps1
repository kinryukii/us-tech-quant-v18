param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxEstimatedPlanCost = 300
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16B ROLLING SCAN SCHEDULER START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SCHEDULER_ONLY"
Write-Host "ROLLING_SCAN_ALWAYS_ON: TRUE"
Write-Host "PRICE_UPDATE_EXECUTED: FALSE"
Write-Host "EVENT_UPDATE_EXECUTED: FALSE"
Write-Host "ROLLING_SCAN_EXECUTED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16B_rolling_scan_scheduler.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16B Python script: $Script"
}

& $Python $Script --root $Root --max-estimated-plan-cost $MaxEstimatedPlanCost
exit $LASTEXITCODE
