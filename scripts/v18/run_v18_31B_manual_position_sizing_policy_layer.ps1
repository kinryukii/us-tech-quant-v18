[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [double]$AccountSizeUsd = 2000,
    [double]$CashReservePct = 15,
    [int]$MaxActivePositions = 8,
    [int]$MaxSpeculativePositions = 2,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31B_manual_position_sizing_policy_layer.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31B_READ_FIRST.txt"

Write-Host "=== START V18.31B MANUAL POSITION SIZING POLICY LAYER ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "ACCOUNT_SIZE_USD: $AccountSizeUsd"
Write-Host "CASH_RESERVE_PCT: $CashReservePct"
Write-Host "MAX_ACTIVE_POSITIONS: $MaxActivePositions"
Write-Host "MAX_SPECULATIVE_POSITIONS: $MaxSpeculativePositions"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: MANUAL_POSITION_SIZING_POLICY_LAYER"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN,
    "--account-size-usd", $AccountSizeUsd,
    "--cash-reserve-pct", $CashReservePct,
    "--max-active-positions", $MaxActivePositions,
    "--max-speculative-positions", $MaxSpeculativePositions
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($Strict.IsPresent) {
    $argsList += "--strict"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.31B MANUAL POSITION SIZING POLICY LAYER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
