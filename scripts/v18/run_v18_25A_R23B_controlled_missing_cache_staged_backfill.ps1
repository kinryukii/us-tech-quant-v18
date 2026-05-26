[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 58,
    [string]$Provider = "yfinance",
    [switch]$DryRun,
    [switch]$AllowExternalFetch
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R23B_controlled_missing_cache_staged_backfill.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R23B_READ_FIRST.txt"

Write-Host "=== START V18.25A-R23B CONTROLLED MISSING-CACHE STAGED BACKFILL ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "PROVIDER: $Provider"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "ALLOW_EXTERNAL_FETCH: $($AllowExternalFetch.IsPresent)"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_NO_FETCH' } else { 'CONTROLLED_STAGED_BACKFILL_EXECUTION' })"
if ((-not $DryRun.IsPresent) -and (-not $AllowExternalFetch.IsPresent)) {
    Write-Host "External fetch is not authorized. R23B will write WARN audit outputs and will not fetch."
}

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers,
    "--provider", $Provider
)

if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($AllowExternalFetch.IsPresent) {
    $argsList += "--allow-external-fetch"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R23B controlled staged backfill failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R23B CONTROLLED MISSING-CACHE STAGED BACKFILL ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
