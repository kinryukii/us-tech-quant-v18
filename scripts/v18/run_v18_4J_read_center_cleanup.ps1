param(
    [switch]$RunDaily
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"

$FinalDailyWrapper = Join-Path $Root "scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"

$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"
New-Item -ItemType Directory -Force -Path $ReadCenterDir | Out-Null

$ReadCenter = Join-Path $ReadCenterDir "V18_4J_CURRENT_READ_CENTER.md"
$CurrentReadFirst = Join-Path $ReadCenterDir "V18_CURRENT_READ_FIRST.md"
$ReadFirstTxt = Join-Path $ReadCenterDir "V18_4J_READ_FIRST.txt"

$DailyReadFirst = Join-Path $Root "outputs\v18\daily_integrated\V18_4I_R1_READ_FIRST.txt"
$FinalDailyPromotion = Join-Path $Root "outputs\v18\daily_integrated\V18_CURRENT_FINAL_DAILY_PROMOTION_MERGE.md"
$OfficialDaily = Join-Path $Root "outputs\v18\daily_integrated\V18_4B_R1_READ_FIRST.txt"
$FactorAuditReadFirst = Join-Path $Root "outputs\v18\daily_integrated\V18_4G_R1_READ_FIRST.txt"

$PromotionReadFirst = Join-Path $Root "outputs\v18\promotion_merge\V18_4I_READ_FIRST.txt"
$PromotionCurrent = Join-Path $Root "outputs\v18\promotion_merge\V18_CURRENT_BACKTEST_FORWARD_PROMOTION.md"

$RobustnessCurrent = Join-Path $Root "outputs\v18\factor_backtest\V18_CURRENT_FACTOR_ROBUSTNESS_INTERPRETATION.md"
$ForwardSummary = Join-Path $Root "outputs\v18\forward_outcome\V18_CURRENT_FORWARD_OUTCOME_SUMMARY.md"
$PromotionRules = Join-Path $Root "outputs\v18\outcome_summary\V18_CURRENT_FACTOR_OUTCOME_PROMOTION.md"

Write-Host ""
Write-Host "=== V18.4J READ CENTER CLEANUP START ==="

if ($RunDaily) {
    if (!(Test-Path $FinalDailyWrapper)) {
        throw "Missing final daily wrapper: $FinalDailyWrapper"
    }

    Write-Host ""
    Write-Host "STEP 1: run V18.4I-R1 final daily wrapper"

    powershell -NoProfile -ExecutionPolicy Bypass -File $FinalDailyWrapper

    if ($LASTEXITCODE -ne 0) {
        throw "V18.4I-R1 final daily wrapper failed with exit code $LASTEXITCODE"
    }
}
else {
    Write-Host ""
    Write-Host "STEP 1: skip daily run. Use -RunDaily if you want refresh first."
}

function Get-TextOrEmpty {
    param([string]$Path)

    if (Test-Path $Path) {
        return Get-Content $Path -Raw -Encoding UTF8
    }

    return ""
}

function Get-KV {
    param(
        [string]$Text,
        [string]$Key
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return "UNKNOWN"
    }

    $Pattern = "(?m)^\s*-?\s*" + [regex]::Escape($Key) + "\s*:\s*`?([^`r`n]+)`?\s*$"
    $Match = [regex]::Match($Text, $Pattern)

    if ($Match.Success) {
        return $Match.Groups[1].Value.Trim()
    }

    return "UNKNOWN"
}

$DailyText = Get-TextOrEmpty $DailyReadFirst
$OfficialText = Get-TextOrEmpty $OfficialDaily
$PromotionText = Get-TextOrEmpty $PromotionReadFirst
$FactorAuditText = Get-TextOrEmpty $FactorAuditReadFirst

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$FinalAction = Get-KV $OfficialText "FINAL_ACTION"
$TodaySafe = Get-KV $OfficialText "TODAY_SAFE"
$BuyPermission = Get-KV $OfficialText "BUY_PERMISSION"
$ActionableBuyCount = Get-KV $OfficialText "ACTIONABLE_BUY_COUNT_TODAY"
$WorthReviewCount = Get-KV $OfficialText "WORTH_REVIEW_BUT_LOCKED_COUNT"

$SelectedFactor = Get-KV $OfficialText "SELECTED_FACTOR"
$FactorTop10 = Get-KV $OfficialText "FACTOR_TOP10_NAMES"
$OfficialReview = Get-KV $OfficialText "OFFICIAL_REVIEW_NAMES"
$FactorOverlap = Get-KV $OfficialText "FACTOR_PACK_OVERLAP_NAMES"

$TrackerRows = Get-KV $OfficialText "TRACKER_TOTAL_ROWS"
$SnapshotDateCount = Get-KV $OfficialText "SNAPSHOT_DATE_COUNT"
$LatestSnapshotPriceDate = Get-KV $OfficialText "LATEST_SNAPSHOT_PRICE_DATE"
$Completed1 = Get-KV $OfficialText "COMPLETED_1OBS_COUNT"
$Completed3 = Get-KV $OfficialText "COMPLETED_3OBS_COUNT"
$Completed5 = Get-KV $OfficialText "COMPLETED_5OBS_COUNT"
$Completed10 = Get-KV $OfficialText "COMPLETED_10OBS_COUNT"
$Completed20 = Get-KV $OfficialText "COMPLETED_20OBS_COUNT"

$PromotionRecommendation = Get-KV $OfficialText "PROMOTION_RECOMMENDATION"
$PromotionCandidateCount = Get-KV $OfficialText "PROMOTION_CANDIDATE_COUNT"
$RejectCandidateCount = Get-KV $OfficialText "REJECT_CANDIDATE_COUNT"
$OfficialDecisionImpact = Get-KV $OfficialText "OFFICIAL_DECISION_IMPACT"
$PromotionAction = Get-KV $OfficialText "PROMOTION_ACTION"

$DirectPromotion = Get-KV $PromotionText "DIRECT_PROMOTION"
$GlobalForwardGate = Get-KV $PromotionText "GLOBAL_FORWARD_GATE"
$CoreAlphaWatch = Get-KV $PromotionText "CORE_ALPHA_WATCH"
$PrimaryConfirmationWatch = Get-KV $PromotionText "PRIMARY_CONFIRMATION_WATCH"

$RuntimeCodeCount = Get-KV $FactorAuditText "RUNTIME_CODE_COUNT"
$MissingReferenceCount = Get-KV $FactorAuditText "MISSING_REFERENCE_COUNT"
$WorldquantFound = Get-KV $FactorAuditText "WORLDQUANT_STYLE_FACTOR_FOUND_COUNT"
$OutputColumnFound = Get-KV $FactorAuditText "OUTPUT_COLUMN_FOUND_COUNT"
$ForwardCovered = Get-KV $FactorAuditText "FORWARD_COVERED_COUNT"
$ForwardMissing = Get-KV $FactorAuditText "FORWARD_MISSING_COUNT"

$Lines = @()

$Lines += "# V18.4J Current Read Center"
$Lines += ""
$Lines += "Generated at: $Now"
$Lines += ""
$Lines += "## 1. Today Action"
$Lines += ""
$Lines += "- FINAL_ACTION: $FinalAction"
$Lines += "- TODAY_SAFE: $TodaySafe"
$Lines += "- BUY_PERMISSION: $BuyPermission"
$Lines += "- ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount"
$Lines += "- WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount"
$Lines += ""
$Lines += "Interpretation:"
$Lines += ""
$Lines += "Today remains no new buy unless the official daily decision changes."
$Lines += ""
$Lines += "## 2. Factor Pack"
$Lines += ""
$Lines += "- SELECTED_FACTOR: $SelectedFactor"
$Lines += "- FACTOR_TOP10_NAMES: $FactorTop10"
$Lines += "- OFFICIAL_REVIEW_NAMES: $OfficialReview"
$Lines += "- FACTOR_PACK_OVERLAP_NAMES: $FactorOverlap"
$Lines += ""
$Lines += "## 3. Forward Tracker"
$Lines += ""
$Lines += "- TRACKER_TOTAL_ROWS: $TrackerRows"
$Lines += "- SNAPSHOT_DATE_COUNT: $SnapshotDateCount"
$Lines += "- LATEST_SNAPSHOT_PRICE_DATE: $LatestSnapshotPriceDate"
$Lines += "- COMPLETED_1OBS_COUNT: $Completed1"
$Lines += "- COMPLETED_3OBS_COUNT: $Completed3"
$Lines += "- COMPLETED_5OBS_COUNT: $Completed5"
$Lines += "- COMPLETED_10OBS_COUNT: $Completed10"
$Lines += "- COMPLETED_20OBS_COUNT: $Completed20"
$Lines += ""
$Lines += "## 4. Promotion Status"
$Lines += ""
$Lines += "- PROMOTION_RECOMMENDATION: $PromotionRecommendation"
$Lines += "- PROMOTION_CANDIDATE_COUNT: $PromotionCandidateCount"
$Lines += "- REJECT_CANDIDATE_COUNT: $RejectCandidateCount"
$Lines += "- GLOBAL_FORWARD_GATE: $GlobalForwardGate"
$Lines += "- DIRECT_PROMOTION: $DirectPromotion"
$Lines += "- OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact"
$Lines += "- PROMOTION_ACTION: $PromotionAction"
$Lines += ""
$Lines += "## 5. Backtest Forward Promotion Cluster"
$Lines += ""
$Lines += "- CORE_ALPHA_WATCH: $CoreAlphaWatch"
$Lines += "- PRIMARY_CONFIRMATION_WATCH: $PrimaryConfirmationWatch"
$Lines += ""
$Lines += "Current interpretation:"
$Lines += ""
$Lines += "- F007 is core alpha watch, but not promoted."
$Lines += "- F009 is primary confirmation watch, but not promoted."
$Lines += "- F010, F011, F008 and F006 remain auxiliary evidence only."
$Lines += "- Official decision impact remains NONE."
$Lines += ""
$Lines += "## 6. Factor Audit Health"
$Lines += ""
$Lines += "- RUNTIME_CODE_COUNT: $RuntimeCodeCount"
$Lines += "- MISSING_REFERENCE_COUNT: $MissingReferenceCount"
$Lines += "- WORLDQUANT_STYLE_FACTOR_FOUND_COUNT: $WorldquantFound"
$Lines += "- OUTPUT_COLUMN_FOUND_COUNT: $OutputColumnFound"
$Lines += "- FORWARD_COVERED_COUNT: $ForwardCovered"
$Lines += "- FORWARD_MISSING_COUNT: $ForwardMissing"
$Lines += ""
$Lines += "## 7. Final Daily Command"
$Lines += ""
$Lines += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'
$Lines += ""
$Lines += "## 8. Read Files"
$Lines += ""
$Lines += "- V18.4I-R1 read first: $DailyReadFirst"
$Lines += "- Final daily promotion merge: $FinalDailyPromotion"
$Lines += "- Official daily read first: $OfficialDaily"
$Lines += "- Factor audit read first: $FactorAuditReadFirst"
$Lines += "- Promotion merge read first: $PromotionReadFirst"
$Lines += "- Promotion current: $PromotionCurrent"
$Lines += "- Factor robustness interpretation: $RobustnessCurrent"
$Lines += "- Forward summary: $ForwardSummary"
$Lines += "- Promotion rules: $PromotionRules"
$Lines += ""
$Lines += "## 9. Safety Guard"
$Lines += ""
$Lines += "No factor research layer can bypass:"
$Lines += ""
$Lines += "- event gate"
$Lines += "- budget lock"
$Lines += "- behavior guard"
$Lines += "- official daily decision"
$Lines += "- position cap"
$Lines += ""
$Lines += "Therefore the current factor research layer remains evidence-only."

Set-Content -Path $ReadCenter -Value $Lines -Encoding UTF8
Set-Content -Path $CurrentReadFirst -Value $Lines -Encoding UTF8

$TxtLines = @()
$TxtLines += "V18_4J_STATUS: OK_READ_CENTER_READY"
$TxtLines += "GENERATED_AT: $Now"
$TxtLines += "CURRENT_READ_FIRST: $CurrentReadFirst"
$TxtLines += "READ_CENTER: $ReadCenter"
$TxtLines += "FINAL_ACTION: $FinalAction"
$TxtLines += "BUY_PERMISSION: $BuyPermission"
$TxtLines += "DIRECT_PROMOTION: $DirectPromotion"
$TxtLines += "OFFICIAL_DECISION_IMPACT: $OfficialDecisionImpact"
$TxtLines += "PROMOTION_ACTION: $PromotionAction"
$TxtLines += 'FINAL_DAILY_COMMAND: powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'

Set-Content -Path $ReadFirstTxt -Value $TxtLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4J READ CENTER CLEANUP READY ==="
Write-Host "V18_4J_STATUS: OK_READ_CENTER_READY"
Write-Host "FINAL_ACTION:" $FinalAction
Write-Host "BUY_PERMISSION:" $BuyPermission
Write-Host "DIRECT_PROMOTION:" $DirectPromotion
Write-Host "OFFICIAL_DECISION_IMPACT:" $OfficialDecisionImpact
Write-Host "PROMOTION_ACTION:" $PromotionAction
Write-Host "CURRENT_READ_FIRST:" $CurrentReadFirst
Write-Host "READ_CENTER:" $ReadCenter
Write-Host "READ_FIRST_TXT:" $ReadFirstTxt

Write-Host ""
Write-Host "=== V18.4J READ CENTER CLEANUP DONE ==="