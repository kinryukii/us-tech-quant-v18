param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.13D-R1 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "COMMAND_CENTER_ONLY: TRUE"
Write-Host "SNAPSHOT_ONLY: TRUE"

$Py = Join-Path $Root "scripts\v18\v18_13D_R1_stable_snapshot.py"
if (-not (Test-Path $Py)) {
    throw "Missing Python script: $Py"
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Missing Python interpreter: $Python"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

& $Python $Py $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18_13D_R1_STABLE_SNAPSHOT_FAILED"
}

$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_13D_R1_READ_FIRST.txt"
if (-not (Test-Path $ReadFirst)) {
    throw "Missing read-first output: $ReadFirst"
}

Write-Host ""
Write-Host "=== V18.13D-R1 STABLE SNAPSHOT DONE ==="
Write-Host ""
Write-Host "=== V18.13D-R1 READ FIRST ==="
Get-Content -Path $ReadFirst -Encoding UTF8
