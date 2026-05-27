param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyEmptyDirsOnly
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20H EMPTY FOLDER AND ORPHAN OUTPUT CLEANUP START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN"
Write-Host "DELETED_FILE_COUNT: 0"
Write-Host "DELETED_DIR_COUNT: 0"
Write-Host "MOVED_COUNT: 0"
Write-Host "ARCHIVED_COUNT: 0"
Write-Host "ZIP_CREATED_COUNT: 0"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if ($ApplyEmptyDirsOnly) {
    Write-Host "APPLY_EMPTY_DIRS_ONLY: RESERVED_FOR_LATER"
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20H_empty_folder_orphan_output_cleanup.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20H Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
