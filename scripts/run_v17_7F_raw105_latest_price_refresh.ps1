$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7F RAW105 LATEST PRICE REFRESH START ==="

$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$PyScript = Join-Path $Root "scripts\run_v17_7F_raw105_latest_price_refresh.py"

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found: $PythonExe"
}

if (-not (Test-Path $PyScript)) {
    throw "Python script not found: $PyScript"
}

Write-Host ""
Write-Host "=== PYTHON PARSE CHECK ==="
& $PythonExe -m py_compile $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "Python parse check failed."
}
Write-Host "PARSE_CHECK_OK"

Write-Host ""
Write-Host "=== RUN RAW105 LATEST PRICE REFRESH ==="
& $PythonExe $PyScript
$Code = $LASTEXITCODE

if ($Code -ne 0) {
    throw "V17.7F raw105 latest price refresh returned nonzero exit code $Code"
}

Write-Host ""
Write-Host "=== V17.7F RAW105 LATEST PRICE REFRESH DONE ==="
