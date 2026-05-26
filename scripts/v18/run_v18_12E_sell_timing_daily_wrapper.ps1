param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.12E SELL TIMING DAILY WRAPPER START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

Set-Location $Root

$Steps = @(
    "scripts\v18\run_v18_12A_sell_timing_shadow_engine.ps1",
    "scripts\v18\run_v18_12B_sell_timing_technical_label_integration.ps1",
    "scripts\v18\run_v18_12C_position_lifecycle_review.ps1",
    "scripts\v18\run_v18_12D_exit_signal_forward_validation.ps1"
)

foreach ($Step in $Steps) {
    $StepPath = Join-Path $Root $Step
    if (-not (Test-Path $StepPath)) {
        throw "Missing V18.12 sell timing step: $StepPath"
    }
    Write-Host ""
    Write-Host "RUN_STEP: $Step"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $StepPath -Root $Root
    if ($LASTEXITCODE -ne 0) {
        Write-Host "STEP_FAILED: $Step EXIT=$LASTEXITCODE"
        exit $LASTEXITCODE
    }
}

$PyScript = Join-Path $Root "scripts\v18\v18_12E_sell_timing_read_center.py"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ReadFirst = Join-Path $Root "outputs\v18\sell_timing\V18_12E_READ_FIRST.txt"

if (-not (Test-Path $PyScript)) {
    throw "Missing Python script: $PyScript"
}

if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
else {
    $Python = "python"
}

Write-Host ""
Write-Host "RUN_STEP: scripts\v18\v18_12E_sell_timing_read_center.py"
Write-Host "PYTHON: $Python"
& $Python $PyScript --root $Root
if ($LASTEXITCODE -ne 0) {
    Write-Host "V18.12E READ CENTER FAILED: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== V18.12E SELL TIMING DAILY WRAPPER DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.12E READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
