[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [int]$MaxTickers = 36
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R23E_rolling_ledger_update_after_price_integration.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R23E_READ_FIRST.txt"

Write-Host "=== START V18.25A-R23E ROLLING LEDGER UPDATE AFTER PRICE INTEGRATION ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_ROLLING_LEDGER_UPDATE_PLAN_ONLY' } else { 'APPLY_ROLLING_LEDGER_UPDATE_AFTER_PRICE_INTEGRATION' })"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R23E rolling ledger update failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R23E ROLLING LEDGER UPDATE AFTER PRICE INTEGRATION ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
