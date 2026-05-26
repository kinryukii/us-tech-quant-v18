param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ForceSameDayPromotion,
    [switch]$DisableSameDayPromotionGuard
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.16E PROMOTION / DEMOTION ENGINE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: PROMOTION_DEMOTION_ONLY"
Write-Host "PRICE_UPDATE_EXECUTED: FALSE"
Write-Host "EVENT_UPDATE_EXECUTED: FALSE"
Write-Host "FULL_UNIVERSE_UPDATE_EXECUTED: FALSE"
Write-Host "SAME_DAY_PROMOTION_GUARD: $((-not $DisableSameDayPromotionGuard).ToString().ToUpper())"
Write-Host "FORCE_SAME_DAY_PROMOTION: $($ForceSameDayPromotion.IsPresent.ToString().ToUpper())"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_16E_promotion_demotion_engine.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.16E Python script: $Script"
}

$Args16E = @("--root", $Root)
if ($ForceSameDayPromotion) { $Args16E += "--force-same-day-promotion" }
if ($DisableSameDayPromotionGuard) { $Args16E += "--disable-same-day-promotion-guard" }

& $Python $Script @Args16E
exit $LASTEXITCODE
