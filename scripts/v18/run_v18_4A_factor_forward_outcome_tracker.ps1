$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_4A_factor_forward_outcome_tracker.py"
$Cockpit = Join-Path $Root "scripts\v18\run_v18_3E_daily_cockpit_wrapper.ps1"
$OpsDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$CockpitLog = Join-Path $OpsDir ("V18_4A_upstream_cockpit_" + $Stamp + ".log")

Write-Host ""
Write-Host "=== V18.4A FACTOR FORWARD OUTCOME TRACKER START ==="
Write-Host ("ROOT: " + $Root)
Write-Host ("PYTHON: " + $Python)
Write-Host ("SCRIPT: " + $Script)
Write-Host ""

if (-not (Test-Path $Python)) {
    throw "Python not found: $Python"
}

if (-not (Test-Path $Script)) {
    throw "Tracker script not found: $Script"
}

if (Test-Path $Cockpit) {
    Write-Host "STEP 1: run upstream V18.3E cockpit quietly"
    $OutText = & powershell -NoProfile -ExecutionPolicy Bypass -File $Cockpit 2>&1
    $OutText | Set-Content -LiteralPath $CockpitLog -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        throw "Upstream cockpit failed. Log: $CockpitLog"
    }
} else {
    Write-Host "STEP 1: upstream cockpit not found; use existing current outputs"
}

Write-Host "STEP 2: update forward outcome tracker"
& $Python $Script

if ($LASTEXITCODE -ne 0) {
    throw "V18.4A tracker failed"
}

Write-Host ""
Write-Host "UPSTREAM_COCKPIT_LOG: $CockpitLog"
Write-Host "=== V18.4A FACTOR FORWARD OUTCOME TRACKER DONE ==="