param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$RunTechnical
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6C TECHNICAL TIMING FORWARD TRACKER START ==="
Write-Host "ROOT: $Root"
Write-Host "RUN_TECHNICAL_FIRST: $RunTechnical"

Set-Location $Root

if ($RunTechnical) {
    $tech = Join-Path $Root "scripts\v18\run_v18_6A_technical_timing_shadow.ps1"
    if (!(Test-Path $tech)) {
        throw "Missing V18.6A technical timing script: $tech"
    }
    Write-Host ""
    Write-Host "STEP 1: run V18.6A technical timing shadow"
    powershell -NoProfile -ExecutionPolicy Bypass -File $tech
}

$py = Join-Path $Root "scripts\v18\v18_6C_technical_timing_forward_tracker.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

Write-Host ""
Write-Host "STEP 2: compile V18.6C Python"
python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

Write-Host ""
Write-Host "STEP 3: update technical timing forward tracker"
python $py --root $Root

Write-Host ""
Write-Host "=== V18.6C TECHNICAL TIMING FORWARD TRACKER DONE ==="
