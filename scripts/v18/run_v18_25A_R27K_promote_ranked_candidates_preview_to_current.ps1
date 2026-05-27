[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27K_promote_ranked_candidates_preview_to_current.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27K_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27K PROMOTE RANKED CANDIDATES PREVIEW TO CURRENT ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_REQUESTED: $($Apply.IsPresent)"
Write-Host "MODE: $(if ($Apply.IsPresent) { 'APPLY_RANKED_CANDIDATES_PROMOTION_WITH_BACKUP' } else { 'DRYRUN_RANKED_CANDIDATES_PROMOTION_PLAN_ONLY' })"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($Apply.IsPresent) {
    $argsList += "--apply"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R27K ranked candidates promotion failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27K PROMOTE RANKED CANDIDATES PREVIEW TO CURRENT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
