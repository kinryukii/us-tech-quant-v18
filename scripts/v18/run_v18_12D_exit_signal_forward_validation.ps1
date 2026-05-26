param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.12D EXIT SIGNAL FORWARD VALIDATION START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

Set-Location $Root

$PyScript = Join-Path $Root "scripts\v18\v18_12D_exit_signal_forward_validation.py"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ReadFirst = Join-Path $Root "outputs\v18\sell_timing\V18_12D_READ_FIRST.txt"

if (-not (Test-Path $PyScript)) {
    throw "Missing Python script: $PyScript"
}

if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
else {
    $Python = "python"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $PyScript"

& $Python $PyScript --root $Root
if ($LASTEXITCODE -ne 0) {
    Write-Host "V18.12D PYTHON FAILED: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== V18.12D EXIT SIGNAL FORWARD VALIDATION DONE ==="

if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.12D READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
