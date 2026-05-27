param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$Mode = if ($Apply) { "APPLY" } else { "DRYRUN" }

Write-Host "=== V18.20I EMPTY DIRECTORY CLEANUP START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $Mode"
Write-Host "DELETED_FILE_COUNT: 0"
Write-Host "DELETED_DIR_COUNT: 0"
Write-Host "MOVED_COUNT: 0"
Write-Host "ARCHIVED_COUNT: 0"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20I_apply_empty_directory_cleanup.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20I Python script: $Script"
}

$Args = @("--root", $Root)
if ($Apply) {
    $Args += "--apply"
}

& $Python $Script @Args
exit $LASTEXITCODE
