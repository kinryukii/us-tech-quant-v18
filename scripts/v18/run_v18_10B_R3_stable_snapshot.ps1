param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.10B-R3 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"

$Py = Join-Path $Root "scripts\v18\v18_10B_R3_stable_snapshot.py"

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
    throw "V18.10B_R3_STABLE_SNAPSHOT_FAILED"
}

Write-Host ""
Write-Host "=== V18.10B-R3 DONE ==="
