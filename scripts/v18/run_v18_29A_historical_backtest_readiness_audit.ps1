[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_29A_historical_backtest_readiness_audit.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_29A_READ_FIRST.txt"

Write-Host "=== START V18.29A HISTORICAL BACKTEST READINESS AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_HISTORICAL_BACKTEST_READINESS_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.29A historical backtest readiness audit failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.29A HISTORICAL BACKTEST READINESS AUDIT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
