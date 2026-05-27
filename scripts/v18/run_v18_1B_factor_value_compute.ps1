$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$PyScript = "$Root\src\v18\factor_lab\compute_v18_1B_factor_values.py"
$VenvPython = "$Root\.venv\Scripts\python.exe"

Write-Host ""
Write-Host "=== V18.1B FACTOR VALUE COMPUTE WRAPPER START ==="
Write-Host ""

if (!(Test-Path $Root)) {
    throw "PROJECT_ROOT_NOT_FOUND: $Root"
}

if (!(Test-Path $PyScript)) {
    throw "PYTHON_SCRIPT_NOT_FOUND: $PyScript"
}

if (Test-Path $VenvPython) {
    $Python = $VenvPython
} else {
    $Python = "python"
}

Write-Host "PYTHON:"
Write-Host $Python
Write-Host ""

Write-Host "=== PYTHON PARSE CHECK ==="
& $Python -m py_compile $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "PYTHON_PARSE_CHECK_FAILED"
}
Write-Host "OK: $PyScript"
Write-Host ""

& $Python $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "V18_1B_FACTOR_VALUE_COMPUTE_FAILED"
}

Write-Host ""
Write-Host "=== V18.1B FACTOR VALUE COMPUTE WRAPPER DONE ==="