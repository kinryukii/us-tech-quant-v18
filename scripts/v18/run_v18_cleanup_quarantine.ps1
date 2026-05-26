param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Quarantine,
    [switch]$DeleteGeneratedOnly
)

$ErrorActionPreference = "Stop"

$Py = Join-Path $Root "scripts\v18\v18_cleanup_quarantine.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

if (-not (Test-Path $Py)) {
    throw "MISSING_CLEANUP_QUARANTINE_SCRIPT: $Py"
}

if ($Quarantine -and $DeleteGeneratedOnly) {
    throw "Choose only one mode: -Quarantine or -DeleteGeneratedOnly"
}

$Mode = "DRY_RUN"
if ($Quarantine) {
    $Mode = "QUARANTINE"
}
if ($DeleteGeneratedOnly) {
    $Mode = "DELETE_GENERATED_ONLY"
}

Write-Host ""
Write-Host "=== V18 CLEANUP QUARANTINE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $Mode"
Write-Host "QUARANTINE_ENABLED: $([bool]$Quarantine)"
Write-Host "DELETE_ENABLED: $([bool]$DeleteGeneratedOnly)"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"
Write-Host ""

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

$ArgsList = @($Py)
if ($Quarantine) {
    $ArgsList += "--quarantine"
}
if ($DeleteGeneratedOnly) {
    $ArgsList += "--delete-generated-only"
}

& $Python @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "V18_CLEANUP_QUARANTINE_FAILED"
}

Write-Host ""
Write-Host "=== V18 CLEANUP QUARANTINE DONE ==="
