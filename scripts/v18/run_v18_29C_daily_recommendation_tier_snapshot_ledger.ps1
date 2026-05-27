[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_29C_daily_recommendation_tier_snapshot_ledger.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_29C_READ_FIRST.txt"

Write-Host "=== START V18.29C DAILY RECOMMENDATION TIER SNAPSHOT LEDGER ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DAILY_RECOMMENDATION_TIER_SNAPSHOT_LEDGER"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.29C daily recommendation tier snapshot ledger failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.29C DAILY RECOMMENDATION TIER SNAPSHOT LEDGER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
