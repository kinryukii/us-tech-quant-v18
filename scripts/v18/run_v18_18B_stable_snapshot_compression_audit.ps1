param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply,
    [int]$KeepLatestStableSnapshots = 5,
    [bool]$CompressOldStableSnapshots = $true,
    [switch]$DeleteOriginalAfterVerifiedZip,
    [bool]$ArchiveLargeOutputs = $false,
    [double]$LargeOutputThresholdMB = 25,
    [string]$OutputArchiveRoot = "archive/generated_outputs_compressed",
    [string]$StableZipRoot = "archive/stable_compressed"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18B STABLE SNAPSHOT COMPRESSION AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "DELETE_ORIGINAL_AFTER_VERIFIED_ZIP: $($DeleteOriginalAfterVerifiedZip.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18B_stable_snapshot_compression_audit.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18B Python script: $Script"
}

$argsList = @(
    "--root", $Root,
    "--keep-latest-stable-snapshots", $KeepLatestStableSnapshots,
    "--compress-old-stable-snapshots", $CompressOldStableSnapshots.ToString(),
    "--archive-large-outputs", $ArchiveLargeOutputs.ToString(),
    "--large-output-threshold-mb", $LargeOutputThresholdMB,
    "--output-archive-root", $OutputArchiveRoot,
    "--stable-zip-root", $StableZipRoot
)
if ($Apply) {
    $argsList += "--apply"
}
if ($DeleteOriginalAfterVerifiedZip) {
    $argsList += "--delete-original-after-verified-zip"
}

& $Python $Script @argsList
exit $LASTEXITCODE
