param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply,
    [int]$KeepLatestStableSnapshots = 5
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18C DELETE VERIFIED COMPRESSED STABLE ORIGINALS START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18C_delete_verified_compressed_stable_originals.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18C Python script: $Script"
}

$argsList = @(
    "--root", $Root,
    "--keep-latest-stable-snapshots", $KeepLatestStableSnapshots
)
if ($Apply) {
    $argsList += "--apply"
}

& $Python $Script @argsList
exit $LASTEXITCODE
