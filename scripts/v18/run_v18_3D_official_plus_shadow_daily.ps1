param([switch]$SkipOfficial)
$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$OfficialScript = "$Root\scripts\run_v17_8D_raw105_current_only_daily.ps1"
$ShadowQuiet = "$Root\scripts\v18\run_v18_3C_R1_factor_shadow_daily_quiet.ps1"
$ShadowNormal = "$Root\scripts\v18\run_v18_3C_factor_shadow_daily_wrapper.ps1"
$OutDir = "$Root\outputs\v18\daily"
$OpsDir = "$Root\outputs\v18\ops"
$ReadFirst = "$OutDir\V18_3D_READ_FIRST.txt"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OfficialLog = "$OpsDir\V18_3D_official_v17_8D_$Stamp.log"
$ShadowLog = "$OpsDir\V18_3D_shadow_v18_$Stamp.log"
New-Item -ItemType Directory -Force $OutDir | Out-Null
New-Item -ItemType Directory -Force $OpsDir | Out-Null

function Read-LineMatch {
    param([string]$Path, [string]$Pattern)
    if (!(Test-Path $Path)) { return @() }
    return @(Get-Content $Path | Where-Object { $_ -match $Pattern })
}

function Get-ShadowSummary {
    $CompareCsv = "$Root\outputs\v18\factor_shadow\V18_3B_R2_SHADOW_OFFICIAL_COMPARE_CURRENT.csv"
    $ShadowCsv = "$Root\outputs\v18\factor_shadow\V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv"
    $Result = [ordered]@{
        selected_factors = "UNKNOWN"
        shadow_name_count = 0
        top1 = "UNKNOWN"
        overlap_count = 0
        overlap_names = "NONE"
        shadow_top30_only_count = 0
        official_not_shadow_top30_count = 0
    }
    if (Test-Path $ShadowCsv) {
        $Shadow = @(Import-Csv $ShadowCsv)
        $Result.shadow_name_count = $Shadow.Count
        if ($Shadow.Count -gt 0) {
            $Top = $Shadow | Sort-Object {[int]$_.shadow_rank} | Select-Object -First 1
            $Result.top1 = $Top.ticker
            $Result.selected_factors = $Top.shadow_factor_ids
        }
    }
    if (Test-Path $CompareCsv) {
        $Cmp = @(Import-Csv $CompareCsv)
        $Overlap = @($Cmp | Where-Object {$_.compare_bucket -eq "SHADOW_TOP30_AND_OFFICIAL_REVIEW"})
        $TopOnly = @($Cmp | Where-Object {$_.compare_bucket -eq "SHADOW_TOP30_ONLY"})
        $OffNotTop = @($Cmp | Where-Object {$_.compare_bucket -eq "OFFICIAL_REVIEW_NOT_SHADOW_TOP30"})
        $Result.overlap_count = $Overlap.Count
        $Result.overlap_names = if ($Overlap.Count -gt 0) { ($Overlap.ticker -join ",") } else { "NONE" }
        $Result.shadow_top30_only_count = $TopOnly.Count
        $Result.official_not_shadow_top30_count = $OffNotTop.Count
    }
    return [pscustomobject]$Result
}

Write-Host ""
Write-Host "=== V18.3D OFFICIAL PLUS SHADOW DAILY START ==="
Write-Host ""

if (-not $SkipOfficial) {
    if (!(Test-Path $OfficialScript)) { throw "MISSING_OFFICIAL_SCRIPT: $OfficialScript" }
    Write-Host "STEP 1: RUN V17.8D OFFICIAL DAILY"
    Write-Host "OFFICIAL_LOG: $OfficialLog"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $OfficialScript *> $OfficialLog
    if ($LASTEXITCODE -ne 0) { throw "V17_8D_OFFICIAL_DAILY_FAILED_SEE_LOG: $OfficialLog" }
} else {
    Write-Host "STEP 1: SKIP V17.8D OFFICIAL DAILY"
}

Write-Host ""
Write-Host "STEP 2: RUN V18 SHADOW DAILY"
Write-Host "SHADOW_LOG: $ShadowLog"

if (Test-Path $ShadowQuiet) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ShadowQuiet -Force *> $ShadowLog
    if ($LASTEXITCODE -ne 0) { throw "V18_3C_R1_SHADOW_FAILED_SEE_LOG: $ShadowLog" }
} elseif (Test-Path $ShadowNormal) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $ShadowNormal *> $ShadowLog
    if ($LASTEXITCODE -ne 0) { throw "V18_3C_SHADOW_FAILED_SEE_LOG: $ShadowLog" }
} else {
    throw "MISSING_SHADOW_WRAPPER: $ShadowQuiet OR $ShadowNormal"
}

$V17Read = "$Root\outputs\v17\raw105_decision\V17_8D_READ_FIRST.txt"
$V17PanelTxt = "$Root\outputs\v17\raw105_decision\V17_8D_CURRENT_RAW105_DECISION_PANEL.txt"
$V17PanelMd = "$Root\outputs\v17\raw105_decision\V17_8D_CURRENT_RAW105_DECISION_PANEL.md"
$V18Read = if (Test-Path "$Root\outputs\v18\factor_shadow\V18_3C_R1_READ_FIRST.txt") { "$Root\outputs\v18\factor_shadow\V18_3C_R1_READ_FIRST.txt" } else { "$Root\outputs\v18\factor_shadow\V18_3C_READ_FIRST.txt" }
$V18Compare = "$Root\outputs\v18\factor_shadow\V18_3B_R2_READ_FIRST.txt"
$Tracker = "$Root\state\v18\factor_shadow_outcome_tracker.csv"
$S = Get-ShadowSummary

$OfficialLines = Read-LineMatch -Path $V17Read -Pattern "FINAL_ACTION|TODAY_SAFE|OFFICIAL_ACTION|BUDGET_ACTION|BUY_PERMISSION|ACTIONABLE_BUY_COUNT|WORTH_REVIEW"

$Lines = @(
    "=== V18.3D OFFICIAL PLUS SHADOW DAILY READ FIRST ===",
    "",
    "STATUS:",
    "V18_3D_STATUS: OK_OFFICIAL_PLUS_SHADOW_DAILY_READY",
    "",
    "OFFICIAL_DAILY:",
    "V17_8D_RUN_STATUS: OK_OR_SKIPPED_BY_USER_FLAG",
    "",
    "SHADOW_DAILY:",
    "V18_SHADOW_STATUS: OK",
    "SHADOW_OFFICIAL_DECISION_IMPACT: NONE",
    "SHADOW_PROMOTION_ACTION: NONE",
    "",
    "OFFICIAL_KEY_LINES:",
    ($OfficialLines -join "`n"),
    "",
    "SHADOW_SUMMARY:",
    "SELECTED_FACTORS: $($S.selected_factors)",
    "SHADOW_NAME_COUNT: $($S.shadow_name_count)",
    "TOP1: $($S.top1)",
    "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: $($S.overlap_count)",
    "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: $($S.overlap_names)",
    "SHADOW_TOP30_ONLY_COUNT: $($S.shadow_top30_only_count)",
    "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: $($S.official_not_shadow_top30_count)",
    "",
    "READ_FILES:",
    $V17Read,
    $V17PanelTxt,
    $V17PanelMd,
    $V18Read,
    $V18Compare,
    $Tracker,
    "",
    "LOGS:",
    $OfficialLog,
    $ShadowLog,
    "",
    "NEXT_DAILY_COMMAND:",
    "powershell -NoProfile -ExecutionPolicy Bypass -File ""D:\us-tech-quant\scripts\v18\run_v18_3D_official_plus_shadow_daily.ps1""",
    "",
    "IMPORTANT:",
    "V17.8D remains the official BUY / NO_BUY decision. V18 shadow output is observation only."
)
Set-Content -Path $ReadFirst -Value $Lines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.3D OFFICIAL PLUS SHADOW DAILY READY ==="
Write-Host "V18_3D_STATUS: OK_OFFICIAL_PLUS_SHADOW_DAILY_READY"
Write-Host "V17_8D_OFFICIAL_STATUS: OK_OR_SKIPPED_BY_USER_FLAG"
Write-Host "V18_SHADOW_STATUS: OK"
Write-Host "SHADOW_OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "SHADOW_PROMOTION_ACTION: NONE"
Write-Host "SELECTED_FACTORS: $($S.selected_factors)"
Write-Host "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: $($S.overlap_names)"
Write-Host ""
Write-Host "READ_FIRST:"
Write-Host $ReadFirst
Write-Host ""
Write-Host "OFFICIAL_READ:"
Write-Host $V17Read
Write-Host ""
Write-Host "SHADOW_READ:"
Write-Host $V18Read
Write-Host ""
Write-Host "LOGS:"
Write-Host $OfficialLog
Write-Host $ShadowLog
Write-Host ""
Write-Host "=== DONE ==="
