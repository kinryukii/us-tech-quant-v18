param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply,
    [bool]$ArchiveLargeCurrentDetails = $false,
    [switch]$DeleteOriginalAfterVerifiedArchive,
    [double]$LargeCurrentFileThresholdMB = 25,
    [bool]$KeepLightweightSummary = $true,
    [string]$ArchiveRoot = "archive/generated_outputs_compressed/technical_timing_backtest_current_details"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18F TECHNICAL TIMING CURRENT DETAIL SLIMMING START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply -and $ArchiveLargeCurrentDetails -and $DeleteOriginalAfterVerifiedArchive) { 'APPLY_DELETE_VERIFIED_ORIGINALS' } elseif ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "ARCHIVE_LARGE_CURRENT_DETAILS: $($ArchiveLargeCurrentDetails.ToString().ToUpper())"
Write-Host "DELETE_ORIGINAL_AFTER_VERIFIED_ARCHIVE: $($DeleteOriginalAfterVerifiedArchive.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18F_technical_timing_current_detail_slimming.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18F Python script: $Script"
}

$argsList = @(
    "--root", $Root,
    "--archive-large-current-details", $ArchiveLargeCurrentDetails.ToString(),
    "--large-current-file-threshold-mb", $LargeCurrentFileThresholdMB,
    "--keep-lightweight-summary", $KeepLightweightSummary.ToString(),
    "--archive-root", $ArchiveRoot
)
if ($Apply) {
    $argsList += "--apply"
}
if ($DeleteOriginalAfterVerifiedArchive) {
    $argsList += "--delete-original-after-verified-archive"
}

& $Python $Script @argsList
exit $LASTEXITCODE
