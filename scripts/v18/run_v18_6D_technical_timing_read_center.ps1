param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$RunFreshTechnical
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6D TECHNICAL TIMING READ CENTER START ==="
Write-Host "ROOT: $Root"
Write-Host "RUN_FRESH_TECHNICAL: $RunFreshTechnical"

Set-Location $Root

if ($RunFreshTechnical) {
    $freshGuard = Join-Path $Root "scripts\v18\run_v18_6C_R1_technical_timing_forward_tracker_freshness_guard.ps1"
    if (!(Test-Path $freshGuard)) {
        throw "Missing V18.6C-R1 freshness guard script: $freshGuard"
    }

    Write-Host ""
    Write-Host "STEP 1: run V18.6C-R1 freshness guard with V18.6A refresh"
    powershell -NoProfile -ExecutionPolicy Bypass -File $freshGuard -RunTechnical
}

$py = Join-Path $Root "scripts\v18\v18_6D_technical_timing_read_center.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

Write-Host ""
Write-Host "STEP 2: compile V18.6D Python"
python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

Write-Host ""
Write-Host "STEP 3: build technical timing read center"
python $py --root $Root

Write-Host ""
Write-Host "=== V18.6D TECHNICAL TIMING READ CENTER DONE ==="
