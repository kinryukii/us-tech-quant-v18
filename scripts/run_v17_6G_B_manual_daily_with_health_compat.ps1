$ErrorActionPreference = "Continue"

$Root = "D:\us-tech-quant"
Set-Location $Root

$CompatScript = Join-Path $Root "scripts\run_v17_6G_B_legacy_health_compat_preflight.ps1"
$ManualDailyScript = Join-Path $Root "scripts\run_v17_6F_manual_daily_full_universe_latest_price.ps1"

Write-Host ""
Write-Host "=== V17.6G-B MANUAL DAILY WITH HEALTH COMPAT START ==="

Write-Host ""
Write-Host "=== STEP 0: LEGACY HEALTH COMPAT PREFLIGHT ==="
powershell -NoProfile -ExecutionPolicy Bypass -File $CompatScript

Write-Host ""
Write-Host "=== STEP 1: RUN V17.6F-E MANUAL DAILY ==="
powershell -NoProfile -ExecutionPolicy Bypass -File $ManualDailyScript
$DailyExit = $LASTEXITCODE

Write-Host ""
Write-Host "=== STEP 2: POST-RUN HEALTH / SOFT EXIT CHECK ==="

$HealthMd = Join-Path $Root "outputs\v16\health\V16_HEALTH_CHECK.md"
$HealthJson = Join-Path $Root "outputs\v16\health\V16_HEALTH_CHECK.json"
$V17Summary = Join-Path $Root "outputs\v17\factor_effectiveness\V17_2D_OFFICIAL_DAILY_INTEGRATION_SUMMARY.md"

Write-Host ""
Write-Host "HEALTH_MD:"
Write-Host $HealthMd

if (Test-Path $HealthMd) {
    Select-String -Path $HealthMd -Pattern "总体状态|MISSING|UNKNOWN|FAIL|OK" | Select-Object -First 40 | Format-Table LineNumber,Line -AutoSize
} else {
    Write-Host "MISSING HEALTH MD"
}

Write-Host ""
Write-Host "HEALTH_JSON:"
Write-Host $HealthJson

if (Test-Path $HealthJson) {
    Select-String -Path $HealthJson -Pattern '"status"|"missing_dirs"|"missing_files"|"missing_core"|"event_confirmation_workflow_status"' | Format-Table LineNumber,Line -AutoSize
} else {
    Write-Host "MISSING HEALTH JSON"
}

Write-Host ""
Write-Host "V17_2D SUMMARY:"
Write-Host $V17Summary

if (Test-Path $V17Summary) {
    Select-String -Path $V17Summary -Pattern "BASE_OFFICIAL_DAILY|BASE_EXIT_CODE|FINAL_STATUS" | Format-Table LineNumber,Line -AutoSize
} else {
    Write-Host "MISSING V17 SUMMARY"
}

Write-Host ""
Write-Host "=== V17.6G-B DONE ==="
Write-Host "DAILY_EXIT_CODE: $DailyExit"
exit $DailyExit
