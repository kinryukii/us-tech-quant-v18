param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.21A-R4 ADVISORY FULL-HISTORY BACKFILL PLAN START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: ADVISORY_ONLY"
Write-Host "PATCH_MODE: FULL_HISTORY_BACKFILL_PLAN_ONLY"
Write-Host "POLICY_APPLIED: FALSE"
Write-Host "HISTORY_BACKFILL_APPLIED: FALSE"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "PRICE_CACHE_MODIFIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "CURRENT_DAILY_MODIFIED: FALSE"
Write-Host "STATE_MODIFIED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "PROMOTION_DEMOTION_MODIFIED: FALSE"
Write-Host "MANUAL_STATE_MODIFIED: FALSE"
Write-Host "BROKER_EXECUTION_MODIFIED: FALSE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_21A_R4_advisory_full_history_backfill_plan.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_21A_R4_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_21A_R4_CURRENT_ADVISORY_BACKFILL_PLAN_REPORT.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.21A-R4 Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.21A-R4 ADVISORY FULL-HISTORY BACKFILL PLAN END ==="

exit $ExitCode
