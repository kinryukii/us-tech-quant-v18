param(
    [switch]$UseYFinanceForRollingScan,
    [switch]$FullDaily,
    [switch]$ReadCenterRefreshOnly,
    [switch]$ValidateOnly,
    [switch]$RunForwardTracker,
    [switch]$RunManualFeedback,
    [switch]$ForceSameDayPromotion,
    [switch]$DisableSameDayPromotionGuard,
    [int]$MaxRuntimeSeconds = 300,
    [int]$SoftStopSeconds = 270,
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16F CURRENT DAILY WITH ROLLING UNIVERSE SCAN START ==="
Write-Host "MODE: CURRENT_DAILY_INTEGRATION_WITH_ROLLING_SCAN"
Write-Host "USE_YFINANCE_FOR_ROLLING_SCAN: $UseYFinanceForRollingScan"
Write-Host "RUN_FORWARD_TRACKER: $RunForwardTracker"
Write-Host "RUN_MANUAL_FEEDBACK: $RunManualFeedback"
Write-Host "SAME_DAY_PROMOTION_GUARD: $((-not $DisableSameDayPromotionGuard).ToString().ToUpper())"
Write-Host "FORCE_SAME_DAY_PROMOTION: $($ForceSameDayPromotion.IsPresent.ToString().ToUpper())"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16F_current_daily_with_rolling_universe_scan.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16F Python script: $Script"
}

$Args16F = @("--root", $Root, "--max-runtime-seconds", "$MaxRuntimeSeconds", "--soft-stop-seconds", "$SoftStopSeconds")
if ($UseYFinanceForRollingScan) { $Args16F += "--use-yfinance-for-rolling-scan" }
if ($RunForwardTracker) { $Args16F += "--run-forward-tracker" }
if ($RunManualFeedback) { $Args16F += "--run-manual-feedback" }
if ($ForceSameDayPromotion) { $Args16F += "--force-same-day-promotion" }
if ($DisableSameDayPromotionGuard) { $Args16F += "--disable-same-day-promotion-guard" }
if ($FullDaily) { $Args16F += "--full-daily" }
if ($ReadCenterRefreshOnly) { $Args16F += "--read-center-refresh-only" }
if ($ValidateOnly) { $Args16F += "--validate-only" }

& $Python $Script @Args16F
exit $LASTEXITCODE
