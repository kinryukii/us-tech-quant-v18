# V17.8D RAW105 CURRENT-ONLY DAILY
# Purpose:
# - Run V17.8C clean overwrite daily from scratch
# - Capture all upstream timestamp-heavy output into a fixed log
# - Print only stable current files to terminal
# - Avoid clickable deleted timestamp files in VS Code

$ErrorActionPreference = "Stop"

try {
    [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
} catch {}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir

Set-Location $Root

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$UpstreamScript = Join-Path $Root "scripts\run_v17_8C_raw105_clean_overwrite_daily.ps1"

$Raw105DecisionDir = Join-Path $Root "outputs\v17\raw105_decision"
$OpsDir = Join-Path $Root "outputs\v17\ops"

New-Item -ItemType Directory -Force -Path $Raw105DecisionDir | Out-Null
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$UpstreamLog = Join-Path $OpsDir "V17_8D_upstream_8C_run.log"
$ThisRunSummary = Join-Path $OpsDir "V17_8D_current_only_daily_summary.txt"

$V17CReadFirst = Join-Path $Raw105DecisionDir "V17_8C_READ_FIRST.txt"
$V17CTxt = Join-Path $Raw105DecisionDir "V17_8C_CURRENT_RAW105_DECISION_PANEL.txt"
$V17CMd = Join-Path $Raw105DecisionDir "V17_8C_CURRENT_RAW105_DECISION_PANEL.md"
$V17CCleanupReport = Join-Path $OpsDir "V17_8C_cleanup_overwrite_report.csv"

$V17DReadFirst = Join-Path $Raw105DecisionDir "V17_8D_READ_FIRST.txt"
$V17DTxt = Join-Path $Raw105DecisionDir "V17_8D_CURRENT_RAW105_DECISION_PANEL.txt"
$V17DMd = Join-Path $Raw105DecisionDir "V17_8D_CURRENT_RAW105_DECISION_PANEL.md"

function Get-LastKeyValue {
    param(
        [string[]]$Lines,
        [string]$Key
    )

    $pattern = "^\s*" + [regex]::Escape($Key) + "\s*:\s*(.+?)\s*$"
    $matches = @($Lines | Where-Object { $_ -match $pattern })

    if ($matches.Count -eq 0) {
        return "UNKNOWN"
    }

    $last = $matches[-1]
    if ($last -match $pattern) {
        return $Matches[1].Trim()
    }

    return "UNKNOWN"
}

Write-Host ""
Write-Host "=== V17.8D RAW105 CURRENT-ONLY DAILY START ==="
Write-Host "Generated: $Now"
Write-Host ""
Write-Host "RUNNING UPSTREAM:"
Write-Host $UpstreamScript
Write-Host ""
Write-Host "UPSTREAM OUTPUT WILL BE SAVED TO:"
Write-Host $UpstreamLog
Write-Host ""

if (-not (Test-Path $UpstreamScript)) {
    Write-Host "UPSTREAM_STATUS: FAIL_SCRIPT_NOT_FOUND"
    Write-Host "MISSING_SCRIPT: $UpstreamScript"
    exit 1
}

# Run V17.8C but do not show its timestamp-heavy output in terminal.
# All output goes into a fixed log file.
& powershell -NoProfile -ExecutionPolicy Bypass -File $UpstreamScript *> $UpstreamLog
$UpstreamExitCode = $LASTEXITCODE

if ($null -eq $UpstreamExitCode) {
    $UpstreamExitCode = 0
}

$LogLines = @()
if (Test-Path $UpstreamLog) {
    $LogLines = Get-Content $UpstreamLog -Encoding UTF8
}

$PanelStatus = Get-LastKeyValue -Lines $LogLines -Key "RAW105_DECISION_PANEL_STATUS"
$FinalAction = Get-LastKeyValue -Lines $LogLines -Key "FINAL_ACTION"
$RawUniverseDecisionCount = Get-LastKeyValue -Lines $LogLines -Key "RAW_UNIVERSE_DECISION_COUNT"
$MainComputeCount = Get-LastKeyValue -Lines $LogLines -Key "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC"
$SecondStageCount = Get-LastKeyValue -Lines $LogLines -Key "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC"
$Raw105PriceOk = Get-LastKeyValue -Lines $LogLines -Key "RAW105_PRICE_OK_COUNT"
$Raw105PriceFail = Get-LastKeyValue -Lines $LogLines -Key "RAW105_PRICE_FAIL_COUNT"
$ActionableBuyCount = Get-LastKeyValue -Lines $LogLines -Key "ACTIONABLE_BUY_COUNT_TODAY"
$WorthReviewLockedCount = Get-LastKeyValue -Lines $LogLines -Key "WORTH_REVIEW_BUT_LOCKED_COUNT"
$TodaySafe = Get-LastKeyValue -Lines $LogLines -Key "TODAY_SAFE"
$OfficialAction = Get-LastKeyValue -Lines $LogLines -Key "OFFICIAL_ACTION"
$BudgetAction = Get-LastKeyValue -Lines $LogLines -Key "BUDGET_ACTION"
$BuyPermission = Get-LastKeyValue -Lines $LogLines -Key "BUY_PERMISSION"
$TimestampDeleted = Get-LastKeyValue -Lines $LogLines -Key "TIMESTAMP_FILES_DELETED"
$TimestampDeleteFailed = Get-LastKeyValue -Lines $LogLines -Key "TIMESTAMP_DELETE_FAILED"

$RequiredFiles = @($V17CReadFirst, $V17CTxt, $V17CMd)
$MissingFiles = @($RequiredFiles | Where-Object { -not (Test-Path $_) })

if ($MissingFiles.Count -gt 0) {
    Write-Host ""
    Write-Host "=== V17.8D RAW105 CURRENT-ONLY DAILY FAILED ==="
    Write-Host "UPSTREAM_EXIT_CODE: $UpstreamExitCode"
    Write-Host "REASON: REQUIRED_CURRENT_FILES_MISSING"
    Write-Host ""
    Write-Host "MISSING FILES:"
    foreach ($f in $MissingFiles) {
        Write-Host $f
    }
    Write-Host ""
    Write-Host "DIAGNOSTIC LOG:"
    Write-Host $UpstreamLog
    exit 2
}

# Create V17.8D current aliases so the daily read files are version-clean.
Copy-Item -Force $V17CReadFirst $V17DReadFirst
Copy-Item -Force $V17CTxt $V17DTxt
Copy-Item -Force $V17CMd $V17DMd

$SummaryText = @"
V17.8D RAW105 CURRENT-ONLY DAILY SUMMARY
Generated: $Now

UPSTREAM_EXIT_CODE: $UpstreamExitCode

RAW105_DECISION_PANEL_STATUS: $PanelStatus
FINAL_ACTION: $FinalAction
RAW_UNIVERSE_DECISION_COUNT: $RawUniverseDecisionCount
MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount
SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount
RAW105_PRICE_OK_COUNT: $Raw105PriceOk
RAW105_PRICE_FAIL_COUNT: $Raw105PriceFail
ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount
WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewLockedCount
TODAY_SAFE: $TodaySafe
OFFICIAL_ACTION: $OfficialAction
BUDGET_ACTION: $BudgetAction
BUY_PERMISSION: $BuyPermission

CURRENT READ FIRST:
$V17DReadFirst

CURRENT TXT:
$V17DTxt

CURRENT MD:
$V17DMd

UPSTREAM LOG:
$UpstreamLog

CLEANUP REPORT:
$V17CCleanupReport

TIMESTAMP_FILES_DELETED: $TimestampDeleted
TIMESTAMP_DELETE_FAILED: $TimestampDeleteFailed

NOTE:
Terminal intentionally hides upstream timestamp report paths.
Read only the CURRENT files above for daily use.
"@

$SummaryText | Set-Content -Path $ThisRunSummary -Encoding UTF8

Write-Host ""
Write-Host "=== V17.8D RAW105 CURRENT-ONLY DAILY READY ==="
Write-Host "UPSTREAM_EXIT_CODE: $UpstreamExitCode"
Write-Host ""
Write-Host "RAW105_DECISION_PANEL_STATUS: $PanelStatus"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "RAW_UNIVERSE_DECISION_COUNT: $RawUniverseDecisionCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount"
Write-Host "RAW105_PRICE_OK_COUNT: $Raw105PriceOk"
Write-Host "RAW105_PRICE_FAIL_COUNT: $Raw105PriceFail"
Write-Host "ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount"
Write-Host "WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewLockedCount"
Write-Host "TODAY_SAFE: $TodaySafe"
Write-Host "OFFICIAL_ACTION: $OfficialAction"
Write-Host "BUDGET_ACTION: $BudgetAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host ""
Write-Host "READ THESE CURRENT FILES ONLY:"
Write-Host ""
Write-Host "CURRENT READ FIRST:"
Write-Host $V17DReadFirst
Write-Host ""
Write-Host "CURRENT TXT:"
Write-Host $V17DTxt
Write-Host ""
Write-Host "CURRENT MD:"
Write-Host $V17DMd
Write-Host ""
Write-Host "RUN SUMMARY:"
Write-Host $ThisRunSummary
Write-Host ""
Write-Host "UPSTREAM LOG:"
Write-Host $UpstreamLog
Write-Host ""
Write-Host "CLEANUP REPORT:"
Write-Host $V17CCleanupReport
Write-Host ""
Write-Host "TIMESTAMP_FILES_DELETED: $TimestampDeleted"
Write-Host "TIMESTAMP_DELETE_FAILED: $TimestampDeleteFailed"
Write-Host ""
Write-Host "=== V17.8D RAW105 CURRENT-ONLY DAILY DONE ==="

if ($UpstreamExitCode -ne 0) {
    exit $UpstreamExitCode
}

exit 0
