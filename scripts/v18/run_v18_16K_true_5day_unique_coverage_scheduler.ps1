param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16K TRUE 5-DAY UNIQUE COVERAGE SCHEDULER AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: ADVISORY_ONLY"
Write-Host "POLICY_APPLIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "CURRENT_DAILY_MODIFIED: FALSE"
Write-Host "STATE_MODIFIED: FALSE"
Write-Host "PRICE_CACHE_MODIFIED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "PROMOTION_DEMOTION_MODIFIED: FALSE"
Write-Host "MANUAL_STATE_MODIFIED: FALSE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16K_true_5day_unique_coverage_scheduler.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_16K_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_16K_CURRENT_TRUE_5DAY_COVERAGE_REPORT.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Script)) {
    throw "Missing V18.16K Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.16K TRUE 5-DAY UNIQUE COVERAGE SCHEDULER AUDIT END ==="

exit $ExitCode
