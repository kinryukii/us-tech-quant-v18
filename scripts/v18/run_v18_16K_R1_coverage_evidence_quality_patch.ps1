param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16K-R1 COVERAGE EVIDENCE QUALITY PATCH START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: ADVISORY_ONLY"
Write-Host "PATCH_MODE: SOURCE_RECONCILIATION_AND_AUDIT_ONLY"
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
$Script = Join-Path $Root "scripts\v18\v18_16K_R1_coverage_evidence_quality_patch.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_16K_R1_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_16K_R1_CURRENT_COVERAGE_EVIDENCE_QUALITY_REPORT.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Script)) {
    throw "Missing V18.16K-R1 Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.16K-R1 COVERAGE EVIDENCE QUALITY PATCH END ==="

exit $ExitCode
