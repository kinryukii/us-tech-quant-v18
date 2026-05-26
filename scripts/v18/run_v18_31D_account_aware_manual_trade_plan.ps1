[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [double]$AccountSizeUsd = 2000,
    [double]$CashUsd = -1,
    [double]$CashReservePct = 15,
    [int]$MaxActivePositions = 8,
    [int]$MaxSpeculativePositions = 2,
    [double]$MaxSinglePositionPct = 12,
    [double]$MaxThemeExposurePct = 35,
    [double]$MaxHighRiskTotalExposurePct = 25,
    [int]$MaxNewBuysPerDay = 3,
    [double]$MinCashAfterTradeUsd = 100,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31D_account_aware_manual_trade_plan.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31D_READ_FIRST.txt"

Write-Host "=== START V18.31D ACCOUNT-AWARE MANUAL TRADE PLAN ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "ACCOUNT_SIZE_USD: $AccountSizeUsd"
Write-Host "CASH_USD: $CashUsd"
Write-Host "CASH_RESERVE_PCT: $CashReservePct"
Write-Host "MAX_ACTIVE_POSITIONS: $MaxActivePositions"
Write-Host "MAX_SPECULATIVE_POSITIONS: $MaxSpeculativePositions"
Write-Host "MAX_SINGLE_POSITION_PCT: $MaxSinglePositionPct"
Write-Host "MAX_THEME_EXPOSURE_PCT: $MaxThemeExposurePct"
Write-Host "MAX_HIGH_RISK_TOTAL_EXPOSURE_PCT: $MaxHighRiskTotalExposurePct"
Write-Host "MAX_NEW_BUYS_PER_DAY: $MaxNewBuysPerDay"
Write-Host "MIN_CASH_AFTER_TRADE_USD: $MinCashAfterTradeUsd"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: ACCOUNT_AWARE_MANUAL_TRADE_PLAN_LAYER"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN,
    "--account-size-usd", $AccountSizeUsd,
    "--cash-reserve-pct", $CashReservePct,
    "--max-active-positions", $MaxActivePositions,
    "--max-speculative-positions", $MaxSpeculativePositions,
    "--max-single-position-pct", $MaxSinglePositionPct,
    "--max-theme-exposure-pct", $MaxThemeExposurePct,
    "--max-high-risk-total-exposure-pct", $MaxHighRiskTotalExposurePct,
    "--max-new-buys-per-day", $MaxNewBuysPerDay,
    "--min-cash-after-trade-usd", $MinCashAfterTradeUsd
)
if ($CashUsd -ne -1) {
    $argsList += "--cash-usd"
    $argsList += $CashUsd
}
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

Write-Host "=== END V18.31D ACCOUNT-AWARE MANUAL TRADE PLAN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
