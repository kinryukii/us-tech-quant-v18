$ErrorActionPreference = "Stop"
chcp 65001 > $null

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
  $Python = "python"
}

$PyScript = Join-Path $Root "scripts\run_v17_1_factor_effectiveness_tracker.py"

Write-Host ""
Write-Host "=== V17.1 FACTOR EFFECTIVENESS TRACKER START ==="
Write-Host "ROOT: $Root"
Write-Host ""

Write-Host "=== PYTHON PARSE CHECK ==="
& $Python -m py_compile $PyScript
if ($LASTEXITCODE -ne 0) {
  throw "Python parse check failed: $PyScript"
}
Write-Host "PARSE_CHECK_OK"
Write-Host ""

& $Python $PyScript --root $Root
if ($LASTEXITCODE -ne 0) {
  throw "V17.1 factor effectiveness tracker failed."
}

Write-Host ""
Write-Host "=== V17.1 READ FIRST ==="
$ReadFirst = Join-Path $Root "outputs\v17\factor_effectiveness\V17_1_READ_FIRST.txt"
if (Test-Path $ReadFirst) {
  Get-Content $ReadFirst
} else {
  Write-Host "READ_FIRST_MISSING: $ReadFirst"
}

Write-Host ""
Write-Host "=== V17.1 FACTOR EFFECTIVENESS TRACKER DONE ==="
