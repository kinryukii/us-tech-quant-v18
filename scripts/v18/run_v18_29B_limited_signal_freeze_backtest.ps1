[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_29B_limited_signal_freeze_backtest.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_29B_READ_FIRST.txt"

Write-Host "=== START V18.29B LIMITED HISTORICAL SIGNAL-FREEZE BACKTEST ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: LIMITED_HISTORICAL_SIGNAL_FREEZE_BACKTEST"
Write-Host "CURRENT_RECOMMENDATION_TIERS_USED_HISTORICALLY: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.29B limited signal-freeze backtest failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.29B LIMITED HISTORICAL SIGNAL-FREEZE BACKTEST ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
