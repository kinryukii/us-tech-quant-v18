param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.17A RANKING FACTOR PROVENANCE AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_RANKING_PROVENANCE_AUDIT"
Write-Host "PRICE_UPDATE_EXECUTED: FALSE"
Write-Host "EVENT_UPDATE_EXECUTED: FALSE"
Write-Host "FULL_DAILY_EXECUTED: FALSE"
Write-Host "YFINANCE_USED: FALSE"
Write-Host "ROLLING_SCAN_EXECUTED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_17A_ranking_factor_provenance_audit.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.17A Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
