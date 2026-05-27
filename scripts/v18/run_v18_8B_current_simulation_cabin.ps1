param(
    [double]$InitialCashUSD = 2000.0,
    [int]$MaxNewPositions = 3
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_8B_current_simulation_cabin.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host ""
Write-Host "=== V18.8B CURRENT SIMULATION CABIN START ==="
Write-Host "ROOT: $Root"
Write-Host "PY: $Py"
Write-Host "INITIAL_CASH_USD: $InitialCashUSD"
Write-Host "MAX_NEW_POSITIONS: $MaxNewPositions"
Write-Host ""

Write-Host "=== PYTHON COMPILE CHECK ==="
& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAIL: $Py"
}
Write-Host "OK_PY_COMPILE: $Py"

Write-Host ""
Write-Host "=== RUN SIMULATION CABIN ==="
& $Python $Py --root $Root --initial-cash-usd $InitialCashUSD --max-new-positions $MaxNewPositions
if ($LASTEXITCODE -ne 0) {
    throw "RUN_FAIL: V18.8B simulation cabin"
}

Write-Host "=== V18.8B CURRENT SIMULATION CABIN DONE ==="
