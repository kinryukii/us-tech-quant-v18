param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.21E EVENT RISK COEFFICIENT ENGINE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: ADVISORY_ONLY"
Write-Host "PATCH_MODE: EVENT_RISK_COEFFICIENT_ENGINE_ONLY"
Write-Host "POLICY_APPLIED: FALSE"
Write-Host "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BUY_PERMISSION_MODIFIED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "CURRENT_DAILY_MODIFIED: FALSE"
Write-Host "STATE_MODIFIED: FALSE"
Write-Host "PRICE_CACHE_MODIFIED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "SIGNAL_SNAPSHOT_MODIFIED: FALSE"
Write-Host "SIMULATION_POSITION_MODIFIED: FALSE"
Write-Host "FORWARD_TRACKER_MODIFIED: FALSE"
Write-Host "PROMOTION_DEMOTION_MODIFIED: FALSE"
Write-Host "MANUAL_STATE_MODIFIED: FALSE"
Write-Host "BROKER_EXECUTION_MODIFIED: FALSE"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "EFFECT_CLAIM_ALLOWED_COUNT: 0"
Write-Host "WEIGHT_CHANGE_ALLOWED_COUNT: 0"
Write-Host "PRODUCTION_PROMOTION_ALLOWED_COUNT: 0"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_21E_event_risk_coefficient_engine.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_21E_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_21E_CURRENT_EVENT_RISK_COEFFICIENT_REPORT.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.21E event risk coefficient Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.21E EVENT RISK COEFFICIENT ENGINE END ==="

exit $ExitCode
