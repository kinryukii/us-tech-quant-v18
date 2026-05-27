param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

# V18.12A wrapper purpose:
# Run the sell timing shadow engine and print its READ_FIRST summary. The
# wrapper does not call official daily scripts and does not place sell/trade
# orders. It keeps all safety guardrails visible in the console banner.
Write-Host ""
Write-Host "=== V18.12A SELL TIMING SHADOW ENGINE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "AUTO_TRADE: DISABLED"

Set-Location $Root

$PyScript = Join-Path $Root "scripts\v18\v18_12A_sell_timing_shadow_engine.py"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$ReadFirst = Join-Path $Root "outputs\v18\sell_timing\V18_12A_READ_FIRST.txt"

if (-not (Test-Path $PyScript)) {
    throw "Missing Python script: $PyScript"
}

# Prefer the repo venv for stable V18 execution, with a plain python fallback
# for environments where the venv has not been created.
if (Test-Path $VenvPython) {
    $Python = $VenvPython
}
else {
    $Python = "python"
}

Write-Host "PYTHON: $Python"

# The Python engine performs read-only input discovery and writes only the
# V18.12A shadow output files under outputs\v18\sell_timing.
& $Python $PyScript --root $Root
if ($LASTEXITCODE -ne 0) {
    Write-Host "V18.12A PYTHON FAILED: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "=== V18.12A SELL TIMING SHADOW ENGINE DONE ==="

# Print the regenerated current READ_FIRST so operators can confirm the
# no-position behavior, output paths, and disabled auto-sell/auto-trade state.
if (Test-Path $ReadFirst) {
    Write-Host ""
    Write-Host "=== V18.12A READ FIRST ==="
    Get-Content -Path $ReadFirst -Encoding UTF8
}
