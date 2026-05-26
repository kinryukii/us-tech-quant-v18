param(
    [double]$InitialCashUSD = 2000.0,
    [int]$MaxNewPositions = 3,
    [int]$MaxReportRows = 40,
    [switch]$SkipOfficialDaily,
    [switch]$UseYFinance,
    [switch]$AllowLocalApprox,
    [switch]$OverwriteForward
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Target = Join-Path $Root "scripts\v18\run_v18_9C_official_daily_with_sim_validation.ps1"

if (-not (Test-Path $Target)) {
    throw "MISSING_CURRENT_TARGET: $Target"
}

Write-Host ""
Write-Host "=== V18 CURRENT OFFICIAL DAILY ENTRY ==="
Write-Host "TARGET: $Target"
Write-Host "INITIAL_CASH_USD: $InitialCashUSD"
Write-Host "MAX_NEW_POSITIONS: $MaxNewPositions"
Write-Host "MAX_REPORT_ROWS: $MaxReportRows"
Write-Host "SKIP_OFFICIAL_DAILY: $SkipOfficialDaily"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "ALLOW_LOCAL_APPROX: $AllowLocalApprox"
Write-Host "OVERWRITE_FORWARD: $OverwriteForward"
Write-Host ""

$argsList = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $Target,
    "-InitialCashUSD", $InitialCashUSD,
    "-MaxNewPositions", $MaxNewPositions,
    "-MaxReportRows", $MaxReportRows
)

if ($SkipOfficialDaily) {
    $argsList += "-SkipOfficialDaily"
}

if ($UseYFinance) {
    $argsList += "-UseYFinance"
}

if ($AllowLocalApprox) {
    $argsList += "-AllowLocalApprox"
}

if ($OverwriteForward) {
    $argsList += "-OverwriteForward"
}

& powershell @argsList

if ($LASTEXITCODE -ne 0) {
    throw "FAIL: V18 current official daily entry"
}

Write-Host ""
Write-Host "=== V18 CURRENT OFFICIAL DAILY ENTRY DONE ==="
