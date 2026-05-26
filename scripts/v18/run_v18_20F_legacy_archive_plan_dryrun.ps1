param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20F LEGACY ARCHIVE PLAN DRYRUN START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20F_legacy_archive_plan_dryrun.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20F Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
