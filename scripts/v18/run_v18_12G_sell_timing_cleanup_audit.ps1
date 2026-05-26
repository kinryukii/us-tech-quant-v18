param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.12G SELL TIMING CLEANUP AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN_ONLY"
Write-Host "DELETE_EXECUTED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

$Py = Join-Path $Root "scripts\v18\v18_12G_sell_timing_cleanup_audit.py"
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
    throw "V18_12G_SELL_TIMING_CLEANUP_AUDIT_FAILED"
}

$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_12G_READ_FIRST.txt"

Write-Host ""
Write-Host "=== V18.12G SELL TIMING CLEANUP AUDIT DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.12G READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
