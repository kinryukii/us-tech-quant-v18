param(
    [int]$LookbackDays = 756,
    [int]$HoldDays = 5,
    [int]$TopN = 10,
    [int]$BottomN = 10,
    [double]$CostBps = 10.0,
    [string]$StartDate = "",
    [string]$EndDate = ""
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_4H_factor_rolling_backtest.py"

Write-Host ""
Write-Host "=== V18.4H FACTOR ROLLING BACKTEST START ==="

if (!(Test-Path $Py)) {
    throw "Python file not found: $Py"
}

$ArgList = @(
    "--lookback-days", "$LookbackDays",
    "--hold-days", "$HoldDays",
    "--top-n", "$TopN",
    "--bottom-n", "$BottomN",
    "--cost-bps", "$CostBps"
)

if ($StartDate -ne "") {
    $ArgList += @("--start-date", "$StartDate")
}

if ($EndDate -ne "") {
    $ArgList += @("--end-date", "$EndDate")
}

python $Py @ArgList

if ($LASTEXITCODE -ne 0) {
    throw "V18.4H factor rolling backtest failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V18.4H FACTOR ROLLING BACKTEST DONE ==="
Write-Host "READ:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_CURRENT_FACTOR_BACKTEST_REPORT.md"
Write-Host "SUMMARY:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_CURRENT_FACTOR_BACKTEST_SUMMARY.csv"