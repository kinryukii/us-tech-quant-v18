[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 93,
    [switch]$RunExistingSafeWrappers,
    [switch]$PreviewOnly,
    [switch]$UpdateCurrentCandidates
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25F_safe_downstream_refresh_ranked_candidate_regeneration.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25F_READ_FIRST.txt"
$effectivePreviewOnly = $true
if ($UpdateCurrentCandidates.IsPresent -and -not $PreviewOnly.IsPresent) {
    $effectivePreviewOnly = $false
}

Write-Host "=== START V18.25A-R25F SAFE DOWNSTREAM REFRESH RANKED CANDIDATE REGENERATION ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "RUN_EXISTING_SAFE_WRAPPERS: $($RunExistingSafeWrappers.IsPresent)"
Write-Host "PREVIEW_ONLY: $effectivePreviewOnly"
Write-Host "UPDATE_CURRENT_CANDIDATES: $($UpdateCurrentCandidates.IsPresent)"
Write-Host "MODE: SAFE_DOWNSTREAM_REFRESH_NO_FETCH"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)

if ($RunExistingSafeWrappers.IsPresent) {
    $argsList += "--run-existing-safe-wrappers"
}
if ($effectivePreviewOnly) {
    $argsList += "--preview-only"
}
if ($UpdateCurrentCandidates.IsPresent) {
    $argsList += "--update-current-candidates"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25F safe downstream refresh failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25F SAFE DOWNSTREAM REFRESH RANKED CANDIDATE REGENERATION ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
