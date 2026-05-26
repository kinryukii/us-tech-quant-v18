$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$OpsDir = Join-Path $Root "outputs\v18\ops"
$OutDir = Join-Path $Root "outputs\v18\daily_integrated"
New-Item -ItemType Directory -Force -Path $OpsDir, $OutDir | Out-Null
$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$EvaluatorRun = Join-Path $Root "scripts\v18\run_v18_4B_factor_outcome_summary_promotion_rules.ps1"
$IntegratedRead = Join-Path $Root "outputs\v18\daily_integrated\V18_4A_R1_READ_FIRST.txt"
$PromotionRead = Join-Path $Root "outputs\v18\outcome_summary\V18_4B_READ_FIRST.txt"
$PromotionRules = Join-Path $Root "outputs\v18\outcome_summary\V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md"
$PromotionSummaryCsv = Join-Path $Root "outputs\v18\outcome_summary\V18_4B_CURRENT_FACTOR_OUTCOME_SUMMARY.csv"
$ForwardSummary = Join-Path $Root "outputs\v18\forward_outcome\V18_CURRENT_FORWARD_OUTCOME_SUMMARY.md"
$Log = Join-Path $OpsDir ("V18_4B_R1_final_daily_" + $Stamp + ".log")

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
Write-Host "=== V18.4B-R1 FINAL DAILY WRAPPER START ==="
Write-Host ("ROOT: " + $Root)
Write-Host ("EVALUATOR_RUN: " + $EvaluatorRun)

if (-not (Test-Path $EvaluatorRun)) {
    throw ("Missing V18.4B evaluator runner: " + $EvaluatorRun)
}

Write-Host "STEP 1: run V18.4B evaluator quietly"
$OutText = & powershell -NoProfile -ExecutionPolicy Bypass -File $EvaluatorRun 2>&1
$OutText | Set-Content -LiteralPath $Log -Encoding UTF8
if ($LASTEXITCODE -ne 0) {
    throw ("V18.4B evaluator failed. Log: " + $Log)
}

$IntegratedText = GetText $IntegratedRead
$PromotionText = GetText $PromotionRead
$AllText = $IntegratedText + "`n" + $PromotionText

$V18_4A_R1_Status = GetKey $IntegratedText "V18_4A_R1_STATUS"
$V18_4A_Status = GetKey $IntegratedText "V18_4A_STATUS"
$V18_4B_Status = GetKey $PromotionText "V18_4B_STATUS"

$FinalAction = GetKey $AllText "FINAL_ACTION"
$TodaySafe = GetKey $AllText "TODAY_SAFE"
$BuyPermission = GetKey $AllText "BUY_PERMISSION"
$ActionableBuyCount = GetKey $AllText "ACTIONABLE_BUY_COUNT_TODAY"
$WorthReviewCount = GetKey $AllText "WORTH_REVIEW_BUT_LOCKED_COUNT"

$SelectedFactor = GetKey $AllText "SELECTED_FACTOR"
$FactorTop10 = GetKey $AllText "FACTOR_TOP10_NAMES"
$OfficialReview = GetKey $AllText "OFFICIAL_REVIEW_NAMES"
$FactorPackOverlap = GetKey $AllText "FACTOR_PACK_OVERLAP_NAMES"
$V18_3C_Overlap = GetKey $AllText "V18_3C_OVERLAP_NAMES"

$TrackerRows = GetKey $AllText "TRACKER_TOTAL_ROWS"
$SnapshotDateCount = GetKey $PromotionText "SNAPSHOT_DATE_COUNT"
$LatestSnapshotDate = GetKey $PromotionText "LATEST_SNAPSHOT_PRICE_DATE"
$Done1 = GetKey $AllText "COMPLETED_1OBS_COUNT"
$Done3 = GetKey $AllText "COMPLETED_3OBS_COUNT"
$Done5 = GetKey $AllText "COMPLETED_5OBS_COUNT"
$Done10 = GetKey $AllText "COMPLETED_10OBS_COUNT"
$Done20 = GetKey $AllText "COMPLETED_20OBS_COUNT"

$PromotionRecommendation = GetKey $PromotionText "PROMOTION_RECOMMENDATION"
$PromotionCandidateCount = GetKey $PromotionText "PROMOTION_CANDIDATE_COUNT"
$RejectCandidateCount = GetKey $PromotionText "REJECT_CANDIDATE_COUNT"
$DecisionImpact = GetKey $AllText "OFFICIAL_DECISION_IMPACT" "NONE"
$PromotionAction = GetKey $AllText "PROMOTION_ACTION" "NONE"

$FinalStatus = "OK_FINAL_DAILY_READY"
if (($V18_4B_Status -eq "UNKNOWN") -or ($FinalAction -eq "UNKNOWN") -or ($PromotionRecommendation -eq "UNKNOWN")) {
    $FinalStatus = "WARN_FINAL_DAILY_READY_WITH_PARSE_GAPS"
}

$ReadFirst = Join-Path $OutDir "V18_4B_R1_READ_FIRST.txt"
$CurrentTxt = Join-Path $OutDir "V18_4B_R1_CURRENT_FINAL_DAILY.txt"
$CurrentMd = Join-Path $OutDir "V18_4B_R1_CURRENT_FINAL_DAILY.md"
$GlobalMd = Join-Path $OutDir "V18_CURRENT_FINAL_DAILY.md"

$Summary = @(
    "=== V18.4B-R1 FINAL DAILY ===",
    "",
    ("V18_4B_R1_STATUS: " + $FinalStatus),
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
    ("FACTOR_TOP10_NAMES: " + $FactorTop10),
    ("OFFICIAL_REVIEW_NAMES: " + $OfficialReview),
    ("FACTOR_PACK_OVERLAP_NAMES: " + $FactorPackOverlap),
    ("V18_3C_OVERLAP_NAMES: " + $V18_3C_Overlap),
    "",
    "=== FORWARD OUTCOME TRACKER ===",
    ("V18_4A_R1_STATUS: " + $V18_4A_R1_Status),
    ("V18_4A_STATUS: " + $V18_4A_Status),
    ("TRACKER_TOTAL_ROWS: " + $TrackerRows),
    ("SNAPSHOT_DATE_COUNT: " + $SnapshotDateCount),
    ("LATEST_SNAPSHOT_PRICE_DATE: " + $LatestSnapshotDate),
    ("COMPLETED_1OBS_COUNT: " + $Done1),
    ("COMPLETED_3OBS_COUNT: " + $Done3),
    ("COMPLETED_5OBS_COUNT: " + $Done5),
    ("COMPLETED_10OBS_COUNT: " + $Done10),
    ("COMPLETED_20OBS_COUNT: " + $Done20),
    "",
    "=== PROMOTION RULES ===",
    ("V18_4B_STATUS: " + $V18_4B_Status),
    ("PROMOTION_RECOMMENDATION: " + $PromotionRecommendation),
    ("PROMOTION_CANDIDATE_COUNT: " + $PromotionCandidateCount),
    ("REJECT_CANDIDATE_COUNT: " + $RejectCandidateCount),
    "",
    "=== SAFETY ===",
    ("OFFICIAL_DECISION_IMPACT: " + $DecisionImpact),
    ("PROMOTION_ACTION: " + $PromotionAction),
    "",
    "=== FILES ===",
    ("INTEGRATED_READ_FIRST: " + $IntegratedRead),
    ("PROMOTION_READ_FIRST: " + $PromotionRead),
    ("FORWARD_SUMMARY: " + $ForwardSummary),
    ("PROMOTION_RULES: " + $PromotionRules),
    ("PROMOTION_SUMMARY_CSV: " + $PromotionSummaryCsv),
    ("RUN_LOG: " + $Log),
    ("READ_FIRST: " + $ReadFirst),
    ("GLOBAL_CURRENT_MD: " + $GlobalMd),
    "",
    "=== DAILY COMMAND ===",
    'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1"'
    "",
    "NOTE: V18.4B-R1 is evaluation-only. It does not change official BUY/NO_BUY decisions."
)

$Summary | Set-Content -LiteralPath $ReadFirst -Encoding UTF8
$Summary | Set-Content -LiteralPath $CurrentTxt -Encoding UTF8
$Summary | Set-Content -LiteralPath $CurrentMd -Encoding UTF8
$Summary | Set-Content -LiteralPath $GlobalMd -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4B-R1 READ FIRST ==="
Get-Content -LiteralPath $ReadFirst -Encoding UTF8
Write-Host ""
Write-Host "=== V18.4B-R1 FINAL DAILY WRAPPER DONE ==="
