$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7 RAW UNIVERSE FULL SCREEN AUDIT START ==="

$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$PyScript = Join-Path $Root "scripts\run_v17_7_raw_universe_full_screen_audit.py"

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
Write-Host "=== RUN RAW UNIVERSE FULL AUDIT ==="
& $PythonExe $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "V17.7 raw universe full screen audit failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V17.7 RAW UNIVERSE FULL SCREEN AUDIT DONE ==="
