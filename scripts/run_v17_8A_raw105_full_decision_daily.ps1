$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.8A RAW105 FULL DECISION DAILY START ==="

$Upstream = Join-Path $Root "scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1"
$PythonExe = Join-Path $Root ".venv\Scripts\python.exe"
$PyScript = Join-Path $Root "scripts\run_v17_8A_raw105_full_decision_daily.py"

if (-not (Test-Path $PythonExe)) {
    throw "Python venv not found: $PythonExe"
}
if (-not (Test-Path $PyScript)) {
    throw "Python script not found: $PyScript"
}
if (-not (Test-Path $Upstream)) {
    throw "Upstream V17.7G-R1 script not found: $Upstream"
}

Write-Host ""
Write-Host "=== PYTHON PARSE CHECK ==="
& $PythonExe -m py_compile $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "Python parse check failed."
}
Write-Host "PARSE_CHECK_OK"

Write-Host ""
Write-Host "=== RUN UPSTREAM: V17.7G-R1 FROM SCRATCH ==="
powershell -NoProfile -ExecutionPolicy Bypass -File $Upstream
if ($LASTEXITCODE -ne 0) {
    throw "Upstream V17.7G-R1 failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== RUN RAW105 FULL DECISION ==="
& $PythonExe $PyScript
if ($LASTEXITCODE -ne 0) {
    throw "V17.8A raw105 full decision failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== V17.8A RAW105 FULL DECISION DAILY DONE ==="
