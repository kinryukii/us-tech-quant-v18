[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$ApplyClean,
    [int]$KeepLatestStable = 5,
    [int]$KeepLatestBackups = 5,
    [int]$KeepLatestOutputs = 3,
    [int]$MinAgeDays = 0,
    [switch]$AllowDeleteUncompressedSnapshots,
    [switch]$AllowDeleteCompressedArchives,
    [switch]$AllowDeleteOldBackups,
    [switch]$AllowDeleteOldOutputs,
    [switch]$AllowDeleteCaches
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_34A_storage_inventory_safe_cleanup.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$reportPath = Join-Path $Root "outputs\v18\read_center\V18_34A_STORAGE_CLEANUP_REPORT.md"
$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_34A_READ_FIRST.txt"

Write-Host "=== START V18.34A STORAGE INVENTORY SAFE CLEANUP ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "APPLY_CLEAN: $($ApplyClean.IsPresent)"
Write-Host "KEEP_LATEST_STABLE: $KeepLatestStable"
Write-Host "KEEP_LATEST_BACKUPS: $KeepLatestBackups"
Write-Host "KEEP_LATEST_OUTPUTS: $KeepLatestOutputs"
Write-Host "MIN_AGE_DAYS: $MinAgeDays"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--keep-latest-stable", $KeepLatestStable,
    "--keep-latest-backups", $KeepLatestBackups,
    "--keep-latest-outputs", $KeepLatestOutputs,
    "--min-age-days", $MinAgeDays
)
if ($DryRun.IsPresent) { $argsList += "--dry-run" }
if ($ApplyClean.IsPresent) { $argsList += "--apply-clean" }
if ($AllowDeleteUncompressedSnapshots.IsPresent) { $argsList += "--allow-delete-uncompressed-snapshots" }
if ($AllowDeleteCompressedArchives.IsPresent) { $argsList += "--allow-delete-compressed-archives" }
if ($AllowDeleteOldBackups.IsPresent) { $argsList += "--allow-delete-old-backups" }
if ($AllowDeleteOldOutputs.IsPresent) { $argsList += "--allow-delete-old-outputs" }
if ($AllowDeleteCaches.IsPresent) { $argsList += "--allow-delete-caches" }

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
$totalLine = ""
$candidateLine = ""
$estimatedLine = ""
$actualLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
    $totalLine = (Select-String -Path $readFirstPath -Pattern '^TOTAL_REPO_SIZE_MB_BEFORE:' | Select-Object -First 1).Line
    $candidateLine = (Select-String -Path $readFirstPath -Pattern '^DELETE_CANDIDATE_COUNT:' | Select-Object -First 1).Line
    $estimatedLine = (Select-String -Path $readFirstPath -Pattern '^ESTIMATED_RECLAIMABLE_MB:' | Select-Object -First 1).Line
    $actualLine = (Select-String -Path $readFirstPath -Pattern '^ACTUAL_RECLAIMED_MB:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.34A STORAGE INVENTORY SAFE CLEANUP ==="
Write-Host $statusLine
Write-Host $totalLine
Write-Host $candidateLine
Write-Host $estimatedLine
Write-Host $actualLine
Write-Host "REPORT: $reportPath"
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
