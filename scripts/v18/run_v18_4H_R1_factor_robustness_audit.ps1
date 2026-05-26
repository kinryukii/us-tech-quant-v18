param(
    [string]$LookbackDaysList = "756,1260",
    [string]$TopNList = "5,10,15,20",
    [string]$HoldDaysList = "3,5,10,20",
    [string]$CostBpsList = "10,25,50",
    [int]$MinNames = 20,
    [string]$EndDate = ""
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_4H_R1_factor_robustness_audit.py"

Write-Host ""
Write-Host "=== V18.4H-R1 FACTOR ROBUSTNESS AUDIT START ==="

if (!(Test-Path $Py)) {
    throw "Python file not found: $Py"
}

$ArgList = @(
    "--lookback-days-list", "$LookbackDaysList",
    "--top-n-list", "$TopNList",
    "--hold-days-list", "$HoldDaysList",
    "--cost-bps-list", "$CostBpsList",
    "--min-names", "$MinNames"
)

if ($EndDate -ne "") {
    $ArgList += @("--end-date", "$EndDate")
}

python $Py @ArgList

if ($LASTEXITCODE -ne 0) {
    throw "V18.4H-R1 factor robustness audit failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V18.4H-R1 FACTOR ROBUSTNESS AUDIT DONE ==="
Write-Host "READ:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_R1_CURRENT_FACTOR_ROBUSTNESS_REPORT.md"
Write-Host "CURRENT:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_CURRENT_FACTOR_ROBUSTNESS.md"