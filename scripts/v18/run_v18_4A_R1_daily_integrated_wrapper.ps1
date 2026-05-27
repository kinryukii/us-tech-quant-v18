$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$OutDir = Join-Path $Root "outputs\v18\daily_integrated"
New-Item -ItemType Directory -Force -Path $OpsDir, $OutDir | Out-Null
$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$TrackerRun = Join-Path $Root "scripts\v18\run_v18_4A_factor_forward_outcome_tracker.ps1"
$TrackerRead = Join-Path $Root "outputs\v18\forward_outcome\V18_4A_READ_FIRST.txt"
$TrackerSummary = Join-Path $Root "outputs\v18\forward_outcome\V18_CURRENT_FORWARD_OUTCOME_SUMMARY.md"
$CockpitCurrent = Join-Path $Root "outputs\v18\cockpit\V18_CURRENT_DAILY_COCKPIT.md"
$Log = Join-Path $OpsDir ("V18_4A_R1_daily_integrated_" + $Stamp + ".log")

function GetText([string]$Path) {
    if (-not (Test-Path $Path)) { return "" }
    return Get-Content -LiteralPath $Path -Raw -Encoding UTF8
}

function GetKey([string]$Text, [string]$Key, [string]$Default = "UNKNOWN") {
    if (-not $Text) { return $Default }
    $pattern = "(?m)^\s*" + [regex]::Escape($Key) + "\s*:\s*(.+?)\s*$"
    $m = [regex]::Match($Text, $pattern)
    if ($m.Success) { return $m.Groups[1].Value.Trim() }
    return $Default
}

Write-Host ""
Write-Host "=== V18.4A-R1 DAILY INTEGRATED WRAPPER START ==="
Write-Host ("ROOT: " + $Root)
Write-Host ("TRACKER_RUN: " + $TrackerRun)

if (-not (Test-Path $TrackerRun)) {
    throw ("Missing tracker runner: " + $TrackerRun)
}

Write-Host "STEP 1: run V18.4A tracker quietly"
$OutText = & powershell -NoProfile -ExecutionPolicy Bypass -File $TrackerRun 2>&1
$OutText | Set-Content -LiteralPath $Log -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
    throw ("V18.4A tracker failed. Log: " + $Log)
}

$TrackerText = GetText $TrackerRead
$CockpitText = GetText $CockpitCurrent
$AllText = $CockpitText + "`n" + $TrackerText

$Status = GetKey $TrackerText "V18_4A_STATUS"
$CockpitStatus = GetKey $CockpitText "V18_3E_R2_STATUS" (GetKey $CockpitText "V18_3E_R1_STATUS")
$FinalAction = GetKey $AllText "FINAL_ACTION"
$TodaySafe = GetKey $AllText "TODAY_SAFE"
$BuyPermission = GetKey $AllText "BUY_PERMISSION"
$ActionableBuyCount = GetKey $AllText "ACTIONABLE_BUY_COUNT_TODAY"
$WorthReviewCount = GetKey $AllText "WORTH_REVIEW_BUT_LOCKED_COUNT"
$SelectedFactor = GetKey $AllText "SELECTED_FACTOR"
$Top10 = GetKey $TrackerText "TOP10_NAMES"
$OfficialReview = GetKey $TrackerText "OFFICIAL_REVIEW_NAMES"
$PackOverlap = GetKey $TrackerText "FACTOR_PACK_OVERLAP_NAMES"
$C3Overlap = GetKey $TrackerText "V18_3C_OVERLAP_NAMES"
$SnapshotDate = GetKey $TrackerText "CURRENT_SNAPSHOT_PRICE_DATES"
$SnapshotCount = GetKey $TrackerText "CURRENT_SNAPSHOT_COUNT"
$TrackerRows = GetKey $TrackerText "TRACKER_TOTAL_ROWS"
$PriceMissing = GetKey $TrackerText "PRICE_MISSING_COUNT"
$Done1 = GetKey $TrackerText "COMPLETED_1OBS_COUNT"
$Done3 = GetKey $TrackerText "COMPLETED_3OBS_COUNT"
$Done5 = GetKey $TrackerText "COMPLETED_5OBS_COUNT"
$Done10 = GetKey $TrackerText "COMPLETED_10OBS_COUNT"
$Done20 = GetKey $TrackerText "COMPLETED_20OBS_COUNT"
$DecisionImpact = GetKey $AllText "OFFICIAL_DECISION_IMPACT" "NONE"
$PromotionAction = GetKey $AllText "PROMOTION_ACTION" "NONE"

$IntegratedStatus = "OK_DAILY_INTEGRATED_READY"
if ($Status -ne "OK_FORWARD_TRACKER_UPDATED" -or $FinalAction -eq "UNKNOWN") {
    $IntegratedStatus = "WARN_DAILY_INTEGRATED_READY_WITH_PARSE_GAPS"
}

$ReadFirst = Join-Path $OutDir "V18_4A_R1_READ_FIRST.txt"
$CurrentTxt = Join-Path $OutDir "V18_4A_R1_CURRENT_DAILY_INTEGRATED.txt"
$CurrentMd = Join-Path $OutDir "V18_4A_R1_CURRENT_DAILY_INTEGRATED.md"
$GlobalMd = Join-Path $OutDir "V18_CURRENT_DAILY_INTEGRATED.md"

$Summary = @(
    "=== V18.4A-R1 DAILY INTEGRATED ===",
    "",
    ("V18_4A_R1_STATUS: " + $IntegratedStatus),
    ("RUN_TIME: " + $RunTime),
    "",
    "=== OFFICIAL DECISION ===",
    ("FINAL_ACTION: " + $FinalAction),
    ("TODAY_SAFE: " + $TodaySafe),
    ("BUY_PERMISSION: " + $BuyPermission),
    ("ACTIONABLE_BUY_COUNT_TODAY: " + $ActionableBuyCount),
    ("WORTH_REVIEW_BUT_LOCKED_COUNT: " + $WorthReviewCount),
    "",
    "=== SHADOW / FACTOR PACK ===",
    ("SELECTED_FACTOR: " + $SelectedFactor),
    ("FACTOR_TOP10_NAMES: " + $Top10),
    ("OFFICIAL_REVIEW_NAMES: " + $OfficialReview),
    ("FACTOR_PACK_OVERLAP_NAMES: " + $PackOverlap),
    ("V18_3C_OVERLAP_NAMES: " + $C3Overlap),
    "",
    "=== FORWARD OUTCOME TRACKER ===",
    ("V18_4A_STATUS: " + $Status),
    ("CURRENT_SNAPSHOT_PRICE_DATES: " + $SnapshotDate),
    ("CURRENT_SNAPSHOT_COUNT: " + $SnapshotCount),
    ("TRACKER_TOTAL_ROWS: " + $TrackerRows),
    ("PRICE_MISSING_COUNT: " + $PriceMissing),
    ("COMPLETED_1OBS_COUNT: " + $Done1),
    ("COMPLETED_3OBS_COUNT: " + $Done3),
    ("COMPLETED_5OBS_COUNT: " + $Done5),
    ("COMPLETED_10OBS_COUNT: " + $Done10),
    ("COMPLETED_20OBS_COUNT: " + $Done20),
    "",
    "=== SAFETY ===",
    ("OFFICIAL_DECISION_IMPACT: " + $DecisionImpact),
    ("PROMOTION_ACTION: " + $PromotionAction),
    "",
    "=== FILES ===",
    ("TRACKER_READ_FIRST: " + $TrackerRead),
    ("TRACKER_SUMMARY: " + $TrackerSummary),
    ("COCKPIT_CURRENT: " + $CockpitCurrent),
    ("RUN_LOG: " + $Log),
    ("READ_FIRST: " + $ReadFirst),
    ("GLOBAL_CURRENT_MD: " + $GlobalMd)
)

$Summary | Set-Content -LiteralPath $ReadFirst -Encoding UTF8
$Summary | Set-Content -LiteralPath $CurrentTxt -Encoding UTF8
$Summary | Set-Content -LiteralPath $CurrentMd -Encoding UTF8
$Summary | Set-Content -LiteralPath $GlobalMd -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4A-R1 READ FIRST ==="
Get-Content -LiteralPath $ReadFirst -Encoding UTF8
Write-Host ""
Write-Host "=== V18.4A-R1 DAILY INTEGRATED WRAPPER DONE ==="
