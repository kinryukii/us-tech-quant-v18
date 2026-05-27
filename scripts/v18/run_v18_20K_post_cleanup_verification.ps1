param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20K POST CLEANUP VERIFICATION START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN_VERIFY_ONLY"
Write-Host "DELETED_COUNT: 0"
Write-Host "MOVED_COUNT: 0"
Write-Host "ARCHIVED_COUNT: 0"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20K_post_cleanup_verification.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20K Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
