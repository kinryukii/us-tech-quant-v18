param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.13A UNIFIED DAILY READ CENTER LINK START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_LINK_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

$Py = Join-Path $Root "scripts\v18\v18_13A_unified_daily_read_center_link.py"
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

& $Python $Py --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18_13A_UNIFIED_DAILY_READ_CENTER_LINK_FAILED"
}

$ReadFirst = Join-Path $Root "outputs\v18\read_center\V18_13A_READ_FIRST.txt"

Write-Host ""
Write-Host "=== V18.13A UNIFIED DAILY READ CENTER LINK DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.13A READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
