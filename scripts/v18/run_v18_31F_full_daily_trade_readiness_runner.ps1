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
    [string]$BrokerProfile = "MOOMOO_JP_US_STOCK_BASIC",
    [double]$CommissionRatePct = 0.132,
    [double]$CommissionMinUsd = 0.00,
    [double]$CommissionCapUsd = 22.00,
    [double]$FxFeeJpyPerUsd = 0.00,
    [double]$ConservativeFxFeeJpyPerUsd = 0.25,
    [double]$MinEffectiveTradeNotionalUsd = 50,
    [double]$CostSafetyMultiple = 2.0,
    [ValidateSet("REPLACE","SKIP","APPEND_EXPLICIT")]
    [string]$SameDayPolicy = "REPLACE",
    [switch]$DryRun,
    [switch]$SkipR30E,
    [switch]$SkipR31E,
    [switch]$Strict,
    [switch]$StopOnWarn
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31F_full_daily_trade_readiness_runner.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31F_READ_FIRST.txt"
$dailyHomePath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_TRADE_READINESS.md"

Write-Host "=== START V18.31F FULL DAILY TRADE-READINESS RUNNER ==="
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
Write-Host "BROKER_PROFILE: $BrokerProfile"
Write-Host "MIN_EFFECTIVE_TRADE_NOTIONAL_USD: $MinEffectiveTradeNotionalUsd"
Write-Host "SAME_DAY_POLICY: $SameDayPolicy"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "SKIP_R30E: $($SkipR30E.IsPresent)"
Write-Host "SKIP_R31E: $($SkipR31E.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "STOP_ON_WARN: $($StopOnWarn.IsPresent)"
Write-Host "MODE: FULL_DAILY_TRADE_READINESS_RUNNER"
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
    "--min-cash-after-trade-usd", $MinCashAfterTradeUsd,
    "--broker-profile", $BrokerProfile,
    "--commission-rate-pct", $CommissionRatePct,
    "--commission-min-usd", $CommissionMinUsd,
    "--commission-cap-usd", $CommissionCapUsd,
    "--fx-fee-jpy-per-usd", $FxFeeJpyPerUsd,
    "--conservative-fx-fee-jpy-per-usd", $ConservativeFxFeeJpyPerUsd,
    "--min-effective-trade-notional-usd", $MinEffectiveTradeNotionalUsd,
    "--cost-safety-multiple", $CostSafetyMultiple,
    "--same-day-policy", $SameDayPolicy
)
if ($CashUsd -ne -1) {
    $argsList += "--cash-usd"
    $argsList += $CashUsd
}
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($SkipR30E.IsPresent) {
    $argsList += "--skip-r30e"
}
if ($SkipR31E.IsPresent) {
    $argsList += "--skip-r31e"
}
if ($Strict.IsPresent) {
    $argsList += "--strict"
}
if ($StopOnWarn.IsPresent) {
    $argsList += "--stop-on-warn"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.31F FULL DAILY TRADE-READINESS RUNNER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "DAILY_HOME: $dailyHomePath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
