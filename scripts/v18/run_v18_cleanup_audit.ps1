param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Py = Join-Path $Root "scripts\v18\v18_cleanup_audit.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Py)) {
    throw "MISSING_CLEANUP_AUDIT_SCRIPT: $Py"
}

Write-Host ""
Write-Host "=== V18 CLEANUP AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRY_RUN"
Write-Host "DELETE_ENABLED: False"
Write-Host "MOVE_ENABLED: False"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"
Write-Host ""

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

& $Python $Py
if ($LASTEXITCODE -ne 0) {
    throw "V18_CLEANUP_AUDIT_FAILED"
}

Write-Host ""
Write-Host "=== V18 CLEANUP AUDIT DONE ==="
