param(
    [string]$Root = "D:\us-tech-quant",
    [string]$TopNList = "5,10,15",
    [string]$HoldDaysList = "3,5,10,20",
    [double]$CostBps = 20.0
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6B-R1 TECHNICAL TIMING DIAGNOSTIC START ==="
Write-Host "ROOT: $Root"
Write-Host "TOPN_LIST: $TopNList"
Write-Host "HOLD_DAYS_LIST: $HoldDaysList"
Write-Host "COST_BPS: $CostBps"

Set-Location $Root

$py = Join-Path $Root "scripts\v18\v18_6B_R1_technical_timing_diagnostic_patch.py"

if (!(Test-Path $py)) {
    throw "Missing Python script: $py"
}

python -m py_compile $py
Write-Host "OK_PY_COMPILE: $py"

python $py --root $Root --topn-list $TopNList --hold-days-list $HoldDaysList --cost-bps $CostBps

Write-Host ""
Write-Host "=== V18.6B-R1 TECHNICAL TIMING DIAGNOSTIC DONE ==="
