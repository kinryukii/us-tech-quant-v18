param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16K-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SNAPSHOT_ONLY"
Write-Host "SNAPSHOT_ONLY: TRUE"
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
Write-Host "STABLE_SNAPSHOT_MODIFIED: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16K_R2_stable_snapshot.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_16K_R2_STABLE_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\ops\V18_16K_R2_CURRENT_STABLE_SNAPSHOT_REPORT.md"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Script)) {
    throw "Missing V18.16K-R2 stable snapshot Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"
Write-Host "=== V18.16K-R2 STABLE SNAPSHOT END ==="

exit $ExitCode
