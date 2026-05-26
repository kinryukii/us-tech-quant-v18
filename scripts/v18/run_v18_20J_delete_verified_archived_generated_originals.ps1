param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$Mode = if ($Apply) { "APPLY" } else { "DRYRUN" }

Write-Host "=== V18.20J VERIFIED ARCHIVED GENERATED ORIGINALS DELETE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $Mode"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20J_delete_verified_archived_generated_originals.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20J Python script: $Script"
}

$Args = @("--root", $Root)
if ($Apply) {
    $Args += "--apply"
}

& $Python $Script @Args
exit $LASTEXITCODE
