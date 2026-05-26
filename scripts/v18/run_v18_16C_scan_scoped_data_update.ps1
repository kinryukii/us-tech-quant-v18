param(
    [switch]$UseYFinance,
    [switch]$LocalCacheBootstrap,
    [int]$MaxRuntimeSeconds = 300,
    [int]$SoftStopSeconds = 270,
    [int]$MaxTickerUpdates = 0,
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16C SCAN-SCOPED DATA UPDATE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SCAN_SCOPED_DATA_UPDATE_ONLY"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "LOCAL_CACHE_BOOTSTRAP: $LocalCacheBootstrap"
Write-Host "MAX_RUNTIME_SECONDS: $MaxRuntimeSeconds"
Write-Host "SOFT_STOP_SECONDS: $SoftStopSeconds"
Write-Host "PRICE_UPDATE_EXECUTED: SCAN_SCOPE_ONLY"
Write-Host "EVENT_UPDATE_EXECUTED: SCAN_SCOPE_ONLY"
Write-Host "FULL_UNIVERSE_UPDATE_EXECUTED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16C_scan_scoped_data_update.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16C Python script: $Script"
}

$Args16C = @("--root", $Root, "--max-runtime-seconds", "$MaxRuntimeSeconds", "--soft-stop-seconds", "$SoftStopSeconds")
if ($UseYFinance) {
    $Args16C += "--use-yfinance"
}
if ($LocalCacheBootstrap) {
    $Args16C += "--local-cache-bootstrap"
}
if ($MaxTickerUpdates -gt 0) {
    $Args16C += @("--max-ticker-updates", "$MaxTickerUpdates")
}

& $Python $Script @Args16C
exit $LASTEXITCODE
