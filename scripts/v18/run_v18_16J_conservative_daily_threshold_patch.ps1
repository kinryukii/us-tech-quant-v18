param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16J CONSERVATIVE DAILY THRESHOLD PATCH START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: CONSERVATIVE_DAILY_THRESHOLD_PATCH"
Write-Host "TRUE_5DAY_UNIQUE_WARNING_PRESERVED: REQUIRED"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16J_conservative_daily_threshold_patch.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16J Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
