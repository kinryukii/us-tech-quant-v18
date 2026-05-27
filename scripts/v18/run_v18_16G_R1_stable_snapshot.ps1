param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16G-R1 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "FULL_DAILY: NOT_RUN"
Write-Host "YFINANCE: NOT_USED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16G_R1_stable_snapshot.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16G-R1 Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
