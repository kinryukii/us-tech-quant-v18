param(
    [switch]$UseYFinance,
    [switch]$AllowLocalApprox,
    [switch]$Overwrite,
    [int]$MaxReportRows = 40
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Py = Join-Path $Root "scripts\v18\v18_9B_forward_return_filler.py"
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    $Python = "python"
}

Write-Host ""
Write-Host "=== V18.9B FORWARD RETURN FILLER START ==="
Write-Host "ROOT: $Root"
Write-Host "PY: $Py"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "ALLOW_LOCAL_APPROX: $AllowLocalApprox"
Write-Host "OVERWRITE: $Overwrite"
Write-Host "MAX_REPORT_ROWS: $MaxReportRows"
Write-Host ""

Write-Host "=== PYTHON COMPILE CHECK ==="
& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAIL: $Py"
}
Write-Host "OK_PY_COMPILE: $Py"

$argsList = @(
    "--root", $Root,
    "--max-report-rows", $MaxReportRows
)

if ($UseYFinance) {
    $argsList += "--use-yfinance"
}

if ($AllowLocalApprox) {
    $argsList += "--allow-local-approx"
}

if ($Overwrite) {
    $argsList += "--overwrite"
}

Write-Host ""
Write-Host "=== RUN FORWARD RETURN FILLER ==="
& $Python $Py @argsList
if ($LASTEXITCODE -ne 0) {
    throw "RUN_FAIL: V18.9B forward return filler"
}

Write-Host "=== V18.9B FORWARD RETURN FILLER DONE ==="
