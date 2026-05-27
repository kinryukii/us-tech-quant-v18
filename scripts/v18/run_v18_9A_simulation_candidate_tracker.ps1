param(
    [int]$MaxReportRows = 40
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_9A_simulation_candidate_tracker.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host ""
Write-Host "=== V18.9A SIMULATION CANDIDATE TRACKER START ==="
Write-Host "ROOT: $Root"
Write-Host "PY: $Py"
Write-Host "MAX_REPORT_ROWS: $MaxReportRows"
Write-Host ""

Write-Host "=== PYTHON COMPILE CHECK ==="
& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAIL: $Py"
}
Write-Host "OK_PY_COMPILE: $Py"

Write-Host ""
Write-Host "=== RUN CANDIDATE TRACKER ==="
& $Python $Py --root $Root --max-report-rows $MaxReportRows
if ($LASTEXITCODE -ne 0) {
    throw "RUN_FAIL: V18.9A simulation candidate tracker"
}

Write-Host "=== V18.9A SIMULATION CANDIDATE TRACKER DONE ==="
