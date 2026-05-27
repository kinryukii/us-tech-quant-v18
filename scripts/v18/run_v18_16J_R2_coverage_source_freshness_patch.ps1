param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16J-R2 COVERAGE SOURCE FRESHNESS PATCH START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: COVERAGE_SOURCE_FRESHNESS_PATCH"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16J_R2_coverage_source_freshness_patch.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16J-R2 Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
