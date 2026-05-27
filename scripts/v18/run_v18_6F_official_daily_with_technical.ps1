param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$SkipMainDaily,
    [switch]$SkipTechnicalRefresh
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6F OFFICIAL DAILY WITH TECHNICAL START ==="
Write-Host "ROOT: $Root"
Write-Host "SKIP_MAIN_DAILY: $SkipMainDaily"
Write-Host "SKIP_TECHNICAL_REFRESH: $SkipTechnicalRefresh"

Set-Location $Root

$mainDaily = Join-Path $Root "scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"
$techReadCenter = Join-Path $Root "scripts\v18\run_v18_6D_technical_timing_read_center.ps1"
$finalMerge = Join-Path $Root "scripts\v18\run_v18_6E_final_read_center_with_technical.ps1"

if (!(Test-Path $mainDaily)) {
    throw "Missing main daily wrapper: $mainDaily"
}

if (!(Test-Path $techReadCenter)) {
    throw "Missing technical timing read center wrapper: $techReadCenter"
}

if (!(Test-Path $finalMerge)) {
    throw "Missing final read center merge wrapper: $finalMerge"
}

if (!$SkipMainDaily) {
    Write-Host ""
    Write-Host "STEP 1: run V18.4J main final daily read center"
    powershell -NoProfile -ExecutionPolicy Bypass -File $mainDaily
}
else {
    Write-Host ""
    Write-Host "STEP 1: skipped main daily refresh"
}

if (!$SkipTechnicalRefresh) {
    Write-Host ""
    Write-Host "STEP 2: run V18.6D technical timing read center with fresh technical"
    powershell -NoProfile -ExecutionPolicy Bypass -File $techReadCenter -RunFreshTechnical
}
else {
    Write-Host ""
    Write-Host "STEP 2: skipped technical refresh"
}

Write-Host ""
Write-Host "STEP 3: build V18.6E final read center with technical"
powershell -NoProfile -ExecutionPolicy Bypass -File $finalMerge

Write-Host ""
Write-Host "=== V18.6F OFFICIAL DAILY WITH TECHNICAL READY ==="
Write-Host "FINAL_READ_CENTER:"
Write-Host (Join-Path $Root "outputs\v18\read_center\V18_6E_CURRENT_FINAL_READ_CENTER_WITH_TECHNICAL.md")
Write-Host "READ_FIRST:"
Write-Host (Join-Path $Root "outputs\v18\read_center\V18_6E_READ_FIRST.txt")
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

Write-Host ""
Write-Host "=== V18.6F OFFICIAL DAILY WITH TECHNICAL DONE ==="
