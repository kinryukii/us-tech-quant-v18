[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [int]$MaxTickers = 36,
    [bool]$RequireFullHistoryOnly = $true
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R23D_official_price_cache_integration_full_history.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R23D_READ_FIRST.txt"

Write-Host "=== START V18.25A-R23D OFFICIAL PRICE CACHE INTEGRATION FULL HISTORY ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "REQUIRE_FULL_HISTORY_ONLY: $RequireFullHistoryOnly"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_OFFICIAL_PRICE_INTEGRATION_PLAN_ONLY' } else { 'APPLY_OFFICIAL_PRICE_CACHE_INTEGRATION_FULL_HISTORY_ONLY' })"
if (-not $RequireFullHistoryOnly) {
    Write-Host "R23D refuses partial-history integration. Partial-history policy must be handled separately."
}

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($RequireFullHistoryOnly) {
    $argsList += "--require-full-history-only"
} else {
    $argsList += "--no-require-full-history-only"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R23D official price cache integration failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R23D OFFICIAL PRICE CACHE INTEGRATION FULL HISTORY ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
