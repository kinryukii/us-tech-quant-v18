param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$RunMainDaily,
    [switch]$RunFreshTechnical
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6E FINAL READ CENTER WITH TECHNICAL START ==="
Write-Host "ROOT: $Root"
Write-Host "RUN_MAIN_DAILY: $RunMainDaily"
Write-Host "RUN_FRESH_TECHNICAL: $RunFreshTechnical"

Set-Location $Root

if ($RunMainDaily) {
    $mainDaily = Join-Path $Root "scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"
    if (!(Test-Path $mainDaily)) {
        throw "Missing V18.4J final daily wrapper: $mainDaily"
    }

    Write-Host ""
    Write-Host "STEP 1: run V18.4J final daily read center wrapper"
    powershell -NoProfile -ExecutionPolicy Bypass -File $mainDaily
}

if ($RunFreshTechnical) {
    $tech = Join-Path $Root "scripts\v18\run_v18_6D_technical_timing_read_center.ps1"
    if (!(Test-Path $tech)) {
        throw "Missing V18.6D technical read center wrapper: $tech"
    }

    Write-Host ""
    Write-Host "STEP 2: run V18.6D technical timing read center with fresh technical"
    powershell -NoProfile -ExecutionPolicy Bypass -File $tech -RunFreshTechnical
}

$py = Join-Path $Root "scripts\v18\v18_6E_final_read_center_with_technical.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

Write-Host ""
Write-Host "STEP 3: compile V18.6E Python"
python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

Write-Host ""
Write-Host "STEP 4: build final read center with technical timing"
python $py --root $Root

Write-Host ""
Write-Host "=== V18.6E FINAL READ CENTER WITH TECHNICAL DONE ==="
