$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_4B_factor_outcome_summary_promotion_rules.py"
$Integrated = Join-Path $Root "scripts\v18\run_v18_4A_R1_daily_integrated_wrapper.ps1"
$OpsDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$IntegratedLog = Join-Path $OpsDir ("V18_4B_upstream_integrated_" + $Stamp + ".log")

Write-Host ""
Write-Host "=== V18.4B FACTOR OUTCOME SUMMARY AND PROMOTION RULES START ==="
Write-Host ("ROOT: " + $Root)
Write-Host ("PYTHON: " + $Python)
Write-Host ("SCRIPT: " + $Script)
Write-Host ""

if (-not (Test-Path $Python)) {
    throw "Python not found: $Python"
}

if (-not (Test-Path $Script)) {
    throw "V18.4B script not found: $Script"
}

if (Test-Path $Integrated) {
    Write-Host "STEP 1: run upstream V18.4A-R1 integrated wrapper quietly"
    $OutText = & powershell -NoProfile -ExecutionPolicy Bypass -File $Integrated 2>&1
    $OutText | Set-Content -LiteralPath $IntegratedLog -Encoding UTF8
    if ($LASTEXITCODE -ne 0) {
        throw "Upstream integrated wrapper failed. Log: $IntegratedLog"
    }
} else {
    Write-Host "STEP 1: upstream integrated wrapper not found; use existing tracker state"
}

Write-Host "STEP 2: evaluate factor outcomes and promotion rules"
& $Python $Script

if ($LASTEXITCODE -ne 0) {
    throw "V18.4B evaluator failed"
}

Write-Host ""
Write-Host "UPSTREAM_INTEGRATED_LOG: $IntegratedLog"
Write-Host "=== V18.4B FACTOR OUTCOME SUMMARY AND PROMOTION RULES DONE ==="