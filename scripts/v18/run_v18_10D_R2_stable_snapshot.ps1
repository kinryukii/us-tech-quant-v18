param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.10D-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"

$Py = Join-Path $Root "scripts\v18\v18_10D_R2_stable_snapshot.py"

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
    throw "V18.10D_R2_STABLE_SNAPSHOT_FAILED"
}

Write-Host ""
Write-Host "=== V18.10D-R2 DONE ==="
