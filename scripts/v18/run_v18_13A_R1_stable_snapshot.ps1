param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.13A-R1 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SNAPSHOT_ONLY"
Write-Host "READ_LINK_ONLY: TRUE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

$Py = Join-Path $Root "scripts\v18\v18_13A_R1_stable_snapshot.py"
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

& $Python $Py $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18_13A_R1_STABLE_SNAPSHOT_FAILED"
}

$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_13A_R1_READ_FIRST.txt"

Write-Host ""
Write-Host "=== V18.13A-R1 STABLE SNAPSHOT DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.13A-R1 READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
