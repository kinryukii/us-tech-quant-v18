param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply,
    [switch]$DeleteOriginalAfterVerifiedZip,
    [double]$LargeOutputThresholdMB = 25,
    [int]$KeepLatestPerFamily = 3,
    [bool]$KeepCurrentAliases = $true,
    [bool]$KeepReadCenter = $true,
    [bool]$KeepLatestOps = $true,
    [bool]$KeepRankingOutputs = $true,
    [bool]$KeepUniverseStateOutputs = $true,
    [bool]$KeepPriceCache = $true,
    [bool]$KeepManualState = $true
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18D LARGE GENERATED OUTPUT ARCHIVE CLEANUP START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply -and $DeleteOriginalAfterVerifiedZip) { 'APPLY_DELETE_VERIFIED_ORIGINALS' } elseif ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "DELETE_ORIGINAL_AFTER_VERIFIED_ZIP: $($DeleteOriginalAfterVerifiedZip.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18D_large_generated_output_archive_cleanup.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18D Python script: $Script"
}

$argsList = @(
    "--root", $Root,
    "--large-output-threshold-mb", $LargeOutputThresholdMB,
    "--keep-latest-per-family", $KeepLatestPerFamily,
    "--keep-current-aliases", $KeepCurrentAliases.ToString(),
    "--keep-read-center", $KeepReadCenter.ToString(),
    "--keep-latest-ops", $KeepLatestOps.ToString(),
    "--keep-ranking-outputs", $KeepRankingOutputs.ToString(),
    "--keep-universe-state-outputs", $KeepUniverseStateOutputs.ToString(),
    "--keep-price-cache", $KeepPriceCache.ToString(),
    "--keep-manual-state", $KeepManualState.ToString()
)
if ($Apply) {
    $argsList += "--apply"
}
if ($DeleteOriginalAfterVerifiedZip) {
    $argsList += "--delete-original-after-verified-zip"
}

& $Python $Script @argsList
exit $LASTEXITCODE
