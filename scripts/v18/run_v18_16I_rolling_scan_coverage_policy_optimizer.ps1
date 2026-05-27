param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16I ROLLING SCAN COVERAGE POLICY OPTIMIZER START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN_POLICY_OPTIMIZER"
Write-Host "POLICY_APPLIED: FALSE"
Write-Host "PRICE_UPDATE_MODIFIED: FALSE"
Write-Host "YFINANCE_ENABLED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16I_rolling_scan_coverage_policy_optimizer.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Script)) {
    throw "Missing V18.16I Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
