param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MinCount = 20,
    [double]$TopFraction = 0.30
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.10B FACTOR EFFECTIVENESS BACKTEST START ==="
Write-Host "ROOT: $Root"
Write-Host "MIN_COUNT: $MinCount"
Write-Host "TOP_FRACTION: $TopFraction"

$Py = Join-Path $Root "scripts\v18\v18_10B_factor_effectiveness_backtest.py"

if (-not (Test-Path $Py)) {
    throw "Missing Python script: $Py"
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $Python = $VenvPy
} else {
    $Python = "python"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

& $Python $Py --root $Root --min-count $MinCount --top-fraction $TopFraction
if ($LASTEXITCODE -ne 0) {
    throw "V18.10B_RUN_FAILED"
}

Write-Host ""
Write-Host "=== V18.10B DONE ==="
