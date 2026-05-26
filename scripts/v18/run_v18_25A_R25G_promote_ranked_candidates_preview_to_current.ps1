[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [bool]$RequireR25FPreviewValid = $true,
    [switch]$AllowPromotion
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25G_promote_ranked_candidates_preview_to_current.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25G_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25G PROMOTE RANKED CANDIDATES PREVIEW TO CURRENT ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "REQUIRE_R25F_PREVIEW_VALID: $RequireR25FPreviewValid"
Write-Host "ALLOW_PROMOTION: $($AllowPromotion.IsPresent)"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT' } else { 'APPLY_PROMOTE_RANKED_CANDIDATES_PREVIEW_TO_CURRENT' })"

$argsList = @(
    $scriptPath,
    "--root", $Root
)

if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($RequireR25FPreviewValid) {
    $argsList += "--require-r25f-preview-valid"
}
if ($AllowPromotion.IsPresent) {
    $argsList += "--allow-promotion"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25G ranked candidates promotion failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25G PROMOTE RANKED CANDIDATES PREVIEW TO CURRENT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
