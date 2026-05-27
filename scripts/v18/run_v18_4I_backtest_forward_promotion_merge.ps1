$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_4I_backtest_forward_promotion_merge.py"

Write-Host ""
Write-Host "=== V18.4I BACKTEST-FORWARD PROMOTION MERGE START ==="

if (!(Test-Path $Py)) {
    throw "Python file not found: $Py"
}

python $Py

if ($LASTEXITCODE -ne 0) {
    throw "V18.4I backtest-forward promotion merge failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V18.4I BACKTEST-FORWARD PROMOTION MERGE DONE ==="
Write-Host "READ:"
Write-Host "D:\us-tech-quant\outputs\v18\promotion_merge\V18_4I_CURRENT_BACKTEST_FORWARD_PROMOTION_REPORT.md"
Write-Host "CURRENT:"
Write-Host "D:\us-tech-quant\outputs\v18\promotion_merge\V18_CURRENT_BACKTEST_FORWARD_PROMOTION.md"