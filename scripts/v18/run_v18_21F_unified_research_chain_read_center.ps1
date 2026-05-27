param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.21F UNIFIED RESEARCH CHAIN READ CENTER START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: ADVISORY_READ_CENTER_ONLY"
Write-Host "PATCH_MODE: UNIFIED_RESEARCH_CHAIN_READ_CENTER_ONLY"
Write-Host "POLICY_APPLIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BUY_PERMISSION_MODIFIED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "CURRENT_DAILY_MODIFIED: FALSE"
Write-Host "STATE_MODIFIED: FALSE"
Write-Host "PRICE_CACHE_MODIFIED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "SIGNAL_SNAPSHOT_MODIFIED: FALSE"
Write-Host "EVENT_CALENDAR_MODIFIED: FALSE"
Write-Host "SIMULATION_POSITION_MODIFIED: FALSE"
Write-Host "FORWARD_TRACKER_MODIFIED: FALSE"
Write-Host "PRICE_FACTOR_MODIFIED: FALSE"
Write-Host "TECHNICAL_TIMING_MODIFIED: FALSE"
Write-Host "PROMOTION_DEMOTION_MODIFIED: FALSE"
Write-Host "MANUAL_STATE_MODIFIED: FALSE"
Write-Host "BROKER_EXECUTION_MODIFIED: FALSE"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "EVENT_RISK_COEFFICIENT_APPLIED_TO_OFFICIAL_DECISION: FALSE"
Write-Host "FORWARD_RETURN_FILLED_COUNT: 0"
Write-Host "EFFECT_CLAIM_ALLOWED_COUNT: 0"
Write-Host "WEIGHT_CHANGE_ALLOWED_COUNT: 0"
Write-Host "PRODUCTION_PROMOTION_ALLOWED_COUNT: 0"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_21F_unified_research_chain_read_center.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_21F_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_21F_CURRENT_UNIFIED_RESEARCH_CHAIN_READ_CENTER.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.21F unified research chain read center Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.21F UNIFIED RESEARCH CHAIN READ CENTER END ==="

exit $ExitCode
