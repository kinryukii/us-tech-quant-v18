param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20G VERIFIED LEGACY ARCHIVE APPLY START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: APPLY_ARCHIVE_ONLY"
Write-Host "DELETED_COUNT: 0"
Write-Host "MOVED_COUNT: 0"
Write-Host "ORIGINAL_DELETED_COUNT: 0"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20G_verified_legacy_archive_apply.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20G Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
