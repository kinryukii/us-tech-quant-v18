param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MinCount = 20,
    [string]$AsOfDate = ""
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.10B-R1 FORWARD RETURN MATURITY MONITOR START ==="
Write-Host "ROOT: $Root"
Write-Host "MIN_COUNT: $MinCount"
Write-Host "AS_OF_DATE: $AsOfDate"

$Py = Join-Path $Root "scripts\v18\v18_10B_R1_forward_return_maturity_monitor.py"

if (-not (Test-Path $Py)) {
    throw "Missing Python script: $Py"
}

$VenvPy = Join-Path $Root ".venv\Scripts\python.exe"
if (Test-Path $VenvPy) {
    $Python = $VenvPy
} else {
    $Python = "python"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Py"

& $Python -m py_compile $Py
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $Py"
}

$ArgsList = @(
    $Py,
    "--root", $Root,
    "--min-count", "$MinCount"
)

if ($AsOfDate -ne "") {
    $ArgsList += @("--as-of-date", $AsOfDate)
}

& $Python @ArgsList
if ($LASTEXITCODE -ne 0) {
    throw "V18.10B_R1_RUN_FAILED"
}

Write-Host ""
Write-Host "=== V18.10B-R1 DONE ==="
