param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply,
    [int]$KeepLatestOutputs = 3,
    [int]$KeepLatestLogs = 10,
    [int]$KeepLatestStableSnapshots = 5,
    [bool]$CompressOldStableSnapshots = $false,
    [bool]$DeletePyCache = $true,
    [bool]$DeleteTempFiles = $true,
    [bool]$DeleteOldGeneratedOutputs = $true,
    [bool]$DeleteProviderTempCache = $true,
    [bool]$DeleteOldLogs = $true,
    [bool]$DeleteOldStableSnapshots = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18A STORAGE SLIMMING AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18A_storage_slimming_cleanup.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18A Python script: $Script"
}

$argsList = @(
    "--root", $Root,
    "--keep-latest-outputs", $KeepLatestOutputs,
    "--keep-latest-logs", $KeepLatestLogs,
    "--keep-latest-stable-snapshots", $KeepLatestStableSnapshots,
    "--compress-old-stable-snapshots", $CompressOldStableSnapshots.ToString(),
    "--delete-pycache", $DeletePyCache.ToString(),
    "--delete-temp-files", $DeleteTempFiles.ToString(),
    "--delete-old-generated-outputs", $DeleteOldGeneratedOutputs.ToString(),
    "--delete-provider-temp-cache", $DeleteProviderTempCache.ToString(),
    "--delete-old-logs", $DeleteOldLogs.ToString(),
    "--delete-old-stable-snapshots", $DeleteOldStableSnapshots.ToString()
)
if ($Apply) {
    $argsList += "--apply"
}

& $Python $Script @argsList
exit $LASTEXITCODE
