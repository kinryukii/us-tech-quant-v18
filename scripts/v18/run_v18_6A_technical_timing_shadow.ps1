param(
    [string]$Root = "D:\us-tech-quant",
    [int]$LookbackDays = 420
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6A TECHNICAL TIMING SHADOW START ==="
Write-Host "ROOT: $Root"
Write-Host "LOOKBACK_DAYS: $LookbackDays"

Set-Location $Root

$py = Join-Path $Root "scripts\v18\v18_6A_technical_timing_shadow.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

python $py --root $Root --lookback-days $LookbackDays

Write-Host ""
Write-Host "=== V18.6A TECHNICAL TIMING SHADOW DONE ==="
