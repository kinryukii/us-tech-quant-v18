param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20B DEEP CLEANUP TRIAGE REPORT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20B_deep_cleanup_triage_report.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20B Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
