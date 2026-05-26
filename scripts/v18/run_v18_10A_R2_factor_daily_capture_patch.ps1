param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UseYFinance,
    [double]$CashUsd = 2000.0,
    [double]$PriceBufferPct = 0.02,
    [double]$MaxSingleOrderCashPct = 0.40,
    [string]$DefaultBenchmark = "QQQ"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.10A-R2 FACTOR DAILY CAPTURE PATCH START ==="
Write-Host "ROOT: $Root"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "DEFAULT_BENCHMARK: $DefaultBenchmark"

$Py = Join-Path $Root "scripts\v18\v18_10A_R2_factor_daily_capture_patch.py"

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

$ArgsList = @(
    $Py,
    "--root", $Root,
    "--cash-usd", "$CashUsd",
    "--price-buffer-pct", "$PriceBufferPct",
    "--max-single-order-cash-pct", "$MaxSingleOrderCashPct",
    "--default-benchmark", "$DefaultBenchmark"
)

if ($UseYFinance) {
    $ArgsList += "--use-yfinance"
}

& $Python @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "V18.10A_R2_RUN_FAILED"
}

Write-Host ""
Write-Host "=== V18.10A-R2 DONE ==="
