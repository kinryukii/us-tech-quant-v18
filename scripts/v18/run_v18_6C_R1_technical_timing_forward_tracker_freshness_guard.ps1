param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$RunTechnical,
    [double]$MinCoverageRatio = 0.80,
    [int]$MinDateCount = 50
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6C-R1 TECHNICAL TIMING FRESHNESS GUARD START ==="
Write-Host "ROOT: $Root"
Write-Host "RUN_TECHNICAL_FIRST: $RunTechnical"
Write-Host "MIN_COVERAGE_RATIO: $MinCoverageRatio"
Write-Host "MIN_DATE_COUNT: $MinDateCount"

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

$py = Join-Path $Root "scripts\v18\v18_6C_R1_technical_timing_forward_tracker_freshness_guard.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

Write-Host ""
Write-Host "STEP 2: compile V18.6C-R1 Python"
python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

Write-Host ""
Write-Host "STEP 3: run freshness guard"
python $py --root $Root --min-coverage-ratio $MinCoverageRatio --min-date-count $MinDateCount

Write-Host ""
Write-Host "=== V18.6C-R1 TECHNICAL TIMING FRESHNESS GUARD DONE ==="
