[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [string]$BrokerProfile = "MOOMOO_JP_US_STOCK_BASIC",
    [double]$CommissionRatePct = 0.132,
    [double]$CommissionMinUsd = 0.00,
    [double]$CommissionCapUsd = 22.00,
    [double]$FxFeeJpyPerUsd = 0.00,
    [double]$ConservativeFxFeeJpyPerUsd = 0.25,
    [double]$MinEffectiveTradeNotionalUsd = 50,
    [double]$CostSafetyMultiple = 2.0,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31C_moomoo_cost_slippage_constraint_layer.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31C_READ_FIRST.txt"

Write-Host "=== START V18.31C MOOMOO COST / SLIPPAGE CONSTRAINT LAYER ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "BROKER_PROFILE: $BrokerProfile"
Write-Host "COMMISSION_RATE_PCT: $CommissionRatePct"
Write-Host "COMMISSION_MIN_USD: $CommissionMinUsd"
Write-Host "COMMISSION_CAP_USD: $CommissionCapUsd"
Write-Host "FX_FEE_JPY_PER_USD: $FxFeeJpyPerUsd"
Write-Host "CONSERVATIVE_FX_FEE_JPY_PER_USD: $ConservativeFxFeeJpyPerUsd"
Write-Host "MIN_EFFECTIVE_TRADE_NOTIONAL_USD: $MinEffectiveTradeNotionalUsd"
Write-Host "COST_SAFETY_MULTIPLE: $CostSafetyMultiple"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: MOOMOO_COST_SLIPPAGE_CONSTRAINT_LAYER"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN,
    "--broker-profile", $BrokerProfile,
    "--commission-rate-pct", $CommissionRatePct,
    "--commission-min-usd", $CommissionMinUsd,
    "--commission-cap-usd", $CommissionCapUsd,
    "--fx-fee-jpy-per-usd", $FxFeeJpyPerUsd,
    "--conservative-fx-fee-jpy-per-usd", $ConservativeFxFeeJpyPerUsd,
    "--min-effective-trade-notional-usd", $MinEffectiveTradeNotionalUsd,
    "--cost-safety-multiple", $CostSafetyMultiple
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

Write-Host "=== END V18.31C MOOMOO COST / SLIPPAGE CONSTRAINT LAYER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
