$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_4H_R1A_factor_robustness_interpretation_patch.py"

Write-Host ""
Write-Host "=== V18.4H-R1A FACTOR ROBUSTNESS INTERPRETATION PATCH START ==="

if (!(Test-Path $Py)) {
    throw "Python file not found: $Py"
}

python $Py

if ($LASTEXITCODE -ne 0) {
    throw "V18.4H-R1A interpretation patch failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V18.4H-R1A FACTOR ROBUSTNESS INTERPRETATION PATCH DONE ==="
Write-Host "READ:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_4H_R1A_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md"
Write-Host "CURRENT:"
Write-Host "D:\us-tech-quant\outputs\v18\factor_backtest\V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md"