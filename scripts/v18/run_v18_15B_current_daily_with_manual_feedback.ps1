param(
    [switch]$UseYFinance,
    [switch]$FullDaily,
    [switch]$ReadCenterRefreshOnly,
    [switch]$ValidateOnly,
    [switch]$RunForwardTracker,
    [switch]$RunManualFeedback,
    [switch]$AllowEmptyManualFiles
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Run14E = Join-Path $Root "scripts\v18\run_v18_14E_current_daily_with_forward_tracker.ps1"
$Run15A = Join-Path $Root "scripts\v18\run_v18_15A_manual_position_trade_feedback.ps1"
$Script15B = Join-Path $Root "scripts\v18\v18_15B_current_daily_with_manual_feedback.py"

foreach ($Required in @($Python, $Run14E, $Run15A, $Script15B)) {
    if (-not (Test-Path $Required)) {
        throw "Missing required file: $Required"
    }
}

$Mode = "READ_CENTER_REFRESH_ONLY"
if ($ValidateOnly) {
    $Mode = "VALIDATE_ONLY"
}
elseif ($FullDaily) {
    $Mode = "FULL_DAILY"
}
elseif ($ReadCenterRefreshOnly) {
    $Mode = "READ_CENTER_REFRESH_ONLY"
}

Write-Host "=== V18.15B CURRENT DAILY WITH MANUAL FEEDBACK START ==="
Write-Host "MODE: $Mode"
Write-Host "RUN_FORWARD_TRACKER: $RunForwardTracker"
Write-Host "RUN_MANUAL_FEEDBACK: $RunManualFeedback"
Write-Host "ALLOW_EMPTY_MANUAL_FILES: $AllowEmptyManualFiles"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "MANUAL_FEEDBACK_INTEGRATED: TRUE"

$Args14E = @()
if ($FullDaily) { $Args14E += "-FullDaily" }
if ($ReadCenterRefreshOnly) { $Args14E += "-ReadCenterRefreshOnly" }
if ($ValidateOnly) { $Args14E += "-ValidateOnly" }
if ($RunForwardTracker) { $Args14E += "-RunForwardTracker" }
if ($UseYFinance -and $FullDaily) { $Args14E += "-UseYFinance" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $Run14E @Args14E
if ($LASTEXITCODE -ne 0) {
    throw "V18_14E_CURRENT_DAILY_WITH_FORWARD_TRACKER_FAILED"
}

$ManualRun = "SKIPPED"
if ($RunManualFeedback) {
    $ManualRun = "RAN"
    $Args15A = @("-AllowEmptyManualFiles")
    if ($AllowEmptyManualFiles) {
        $Args15A = @("-AllowEmptyManualFiles")
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run15A @Args15A
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_15A_MANUAL_FEEDBACK_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }
}

& $Python $Script15B --root $Root --mode $Mode --forward-tracker-run $(if ($RunForwardTracker) { "RAN" } else { "SKIPPED" }) --manual-feedback-run $ManualRun
exit $LASTEXITCODE
