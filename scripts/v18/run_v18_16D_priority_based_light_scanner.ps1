param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16D PRIORITY-BASED LIGHT SCANNER START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: PRIORITY_BASED_LIGHT_SCAN_ONLY"
Write-Host "PRICE_UPDATE_EXECUTED: FALSE"
Write-Host "EVENT_UPDATE_EXECUTED: FALSE"
Write-Host "FULL_UNIVERSE_UPDATE_EXECUTED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16D_priority_based_light_scanner.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16D Python script: $Script"
}

& $Python $Script --root $Root
exit $LASTEXITCODE
