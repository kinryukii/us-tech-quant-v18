param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UseYFinance
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.11 CALENDAR / VWAP PROXY / RV SHADOW FACTORS START ==="
Write-Host "ROOT: $Root"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_WEIGHT_CHANGE: DISABLED"
Write-Host "AUTO_PROMOTION: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

$Py = Join-Path $Root "scripts\v18\v18_11_calendar_vwap_rv_shadow_factors.py"
if (-not (Test-Path $Py)) {
    throw "Missing Python script: $Py"
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $Python = $VenvPy
}
else {
    $Python = "python"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

$ArgsList = @($Py, "--root", $Root)
if ($UseYFinance) {
    $ArgsList += "--use-yfinance"
}

& $Python @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "V18_11_SHADOW_FACTORS_FAILED"
}

Write-Host ""
Write-Host "=== V18.11 CALENDAR / VWAP PROXY / RV SHADOW FACTORS DONE ==="
