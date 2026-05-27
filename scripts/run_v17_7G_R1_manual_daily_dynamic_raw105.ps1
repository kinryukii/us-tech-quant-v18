$ErrorActionPreference = "Continue"

$Root = "D:\us-tech-quant"
Set-Location $Root

$OutDir = Join-Path $Root "outputs\v17\manual_daily"
$AuditDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
New-Item -ItemType Directory -Force -Path $AuditDir | Out-Null

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$Upstream = Join-Path $Root "scripts\run_v17_7C_R1_manual_daily_with_raw105_audit.ps1"

$SummaryTxt = Join-Path $OutDir "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_$Stamp.txt"
$SummaryMd = Join-Path $OutDir "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_$Stamp.md"
$ReadFirst = Join-Path $OutDir "V17_7G_R1_READ_FIRST.txt"
$StepCsv = Join-Path $OutDir "v17_7G_R1_steps_$Stamp.csv"

$C_R1_ReadFirst = Join-Path $AuditDir "V17_7C_R1_READ_FIRST.txt"
$C_R1_Summary = Join-Path $AuditDir "V17_7C_R1_MANUAL_DAILY_WITH_RAW105_AUDIT_SUMMARY.md"
$F_Refresh = Join-Path $AuditDir "V17_7F_RAW105_LATEST_PRICE_REFRESH.md"
$F_B_Accept = Join-Path $AuditDir "V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md"
$Semantic = Join-Path $AuditDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md"
$Delta = Join-Path $AuditDir "V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md"
$Removed = Join-Path $AuditDir "V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md"

$Steps = New-Object System.Collections.Generic.List[object]

function Add-Step {
    param(
        [string]$Name,
        [string]$Status,
        [int]$ExitCode,
        [string]$Note
    )

    $script:Steps.Add([pscustomobject]@{
        run_time = $RunTime
        step_name = $Name
        status = $Status
        exit_code = $ExitCode
        note = $Note
    })
}

function Read-KeyValues {
    param([string]$Path)

    $map = @{}

    if (-not (Test-Path $Path)) {
        return $map
    }

    $lines = Get-Content $Path
    foreach ($line in $lines) {
        if ($line -match "^([^:]+):\s*(.*)$") {
            $key = $Matches[1].Trim()
            $val = $Matches[2].Trim()
            if ($key.Length -gt 0) {
                $map[$key] = $val
            }
        }
    }

    return $map
}

function Find-LatestManualDailyReport {
    $dir = Join-Path $Root "outputs\v17\manual_daily"
    if (-not (Test-Path $dir)) {
        return $null
    }

    $file = Get-ChildItem -Path $dir -Filter "V17_6F_E_MANUAL_DAILY_STABLE_*.txt" -File |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    return $file
}

Write-Host ""
Write-Host "=== V17.7G-R1 DYNAMIC RAW105 MANUAL DAILY START ==="

if (-not (Test-Path $Upstream)) {
    Add-Step -Name "V17_7C_R1_UPSTREAM" -Status "MISSING" -ExitCode 9004 -Note "missing upstream script"
    Write-Host "MISSING UPSTREAM SCRIPT:"
    Write-Host $Upstream
} else {
    Write-Host ""
    Write-Host "=== RUN UPSTREAM V17.7C-R1 ==="
    powershell -NoProfile -ExecutionPolicy Bypass -File $Upstream
    $code = $LASTEXITCODE

    if ($null -eq $code) {
        $code = 0
    }

    if ($code -eq 0) {
        Add-Step -Name "V17_7C_R1_UPSTREAM" -Status "OK" -ExitCode 0 -Note "upstream completed"
    } else {
        Add-Step -Name "V17_7C_R1_UPSTREAM" -Status "FAIL" -ExitCode $code -Note "upstream nonzero exit"
    }
}

$Steps | Export-Csv -Path $StepCsv -NoTypeInformation -Encoding UTF8

$AuditKv = Read-KeyValues $C_R1_ReadFirst

$LatestManual = Find-LatestManualDailyReport
$DailyKv = @{}
$LatestManualPath = ""

if ($LatestManual) {
    $LatestManualPath = $LatestManual.FullName
    $DailyKv = Read-KeyValues $LatestManual.FullName
}

$V17_7C_R1_Status = $AuditKv["V17_7C_R1_STATUS"]
$BaseDailyStatus = $AuditKv["BASE_DAILY_STATUS"]

$RawUniverseCount = $AuditKv["RAW_UNIVERSE_COUNT"]
$ClassifiedUniverseCount = $AuditKv["CLASSIFIED_UNIVERSE_COUNT"]
$MainComputeUniverseCount = $AuditKv["MAIN_COMPUTE_UNIVERSE_COUNT"]
$SecondStageCandidateCount = $AuditKv["SECOND_STAGE_CANDIDATE_COUNT"]

$Raw105PriceRefreshStatus = $AuditKv["RAW105_PRICE_REFRESH_STATUS"]
$PriceRefreshOkCount = $AuditKv["PRICE_REFRESH_OK_COUNT"]
$PriceRefreshFailCount = $AuditKv["PRICE_REFRESH_FAIL_COUNT"]
$MaxLatestPriceDate = $AuditKv["MAX_LATEST_PRICE_DATE"]
$LatestDateCount = $AuditKv["LATEST_DATE_COUNT"]
$OkButNotMaxDateCount = $AuditKv["OK_BUT_NOT_MAX_DATE_COUNT"]

$FreshnessAcceptanceStatus = $AuditKv["PRICE_FRESHNESS_ACCEPTANCE_STATUS"]
$DeltaAuditStatus = $AuditKv["DELTA_AUDIT_STATUS"]
$RemovedInspectionStatus = $AuditKv["REMOVED_INSPECTION_STATUS"]

$ManualDailyStatus = $DailyKv["MANUAL_DAILY_STATUS"]
$TodaySafe = $DailyKv["TODAY_SAFE"]
$OfficialAction = $DailyKv["OFFICIAL_ACTION"]
$BudgetAction = $DailyKv["BUDGET_ACTION"]
$BuyPermission = $DailyKv["BUY_PERMISSION"]
$GlobalMode = $DailyKv["GLOBAL_MODE"]
$CriticalUnknownCount = $DailyKv["CRITICAL_UNKNOWN_COUNT"]
$PriceAuditStatus = $DailyKv["PRICE_AUDIT_STATUS"]
$PriceRowCount = $DailyKv["PRICE_ROW_COUNT"]
$MainPriceOkCount = $DailyKv["PRICE_OK_COUNT"]
$MainPriceFailCount = $DailyKv["PRICE_FAIL_COUNT"]
$MainPriceStaleCount = $DailyKv["PRICE_STALE_COUNT"]
$MainMinLatestPriceDate = $DailyKv["MIN_LATEST_PRICE_DATE"]
$MainMaxLatestPriceDate = $DailyKv["MAX_LATEST_PRICE_DATE"]
$V16HealthStatus = $DailyKv["V16_HEALTH_STATUS"]
$HealthCompatStatus = $DailyKv["HEALTH_COMPAT_STATUS"]

$HardFailSteps = @($Steps | Where-Object { $_.status -ne "OK" })

$Status = if (
    $HardFailSteps.Count -eq 0 -and
    $V17_7C_R1_Status -like "OK*" -and
    $BaseDailyStatus -in @("OK", "SOFT_OK_OUTPUTS_VALID") -and
    $RawUniverseCount -eq "105" -and
    $ClassifiedUniverseCount -eq "105" -and
    [int]$MainComputeUniverseCount -gt 0 -and
    [int]$SecondStageCandidateCount -gt 0 -and
    $Raw105PriceRefreshStatus -eq "OK" -and
    $PriceRefreshOkCount -eq "105" -and
    $PriceRefreshFailCount -eq "0" -and
    $FreshnessAcceptanceStatus -like "OK*" -and
    $ManualDailyStatus -eq "OK" -and
    $PriceAuditStatus -eq "OK"
) {
    "OK_DYNAMIC_RAW105_MANUAL_DAILY"
} elseif (
    $HardFailSteps.Count -eq 0 -and
    $RawUniverseCount -eq "105" -and
    $Raw105PriceRefreshStatus -eq "OK" -and
    $FreshnessAcceptanceStatus -like "OK*"
) {
    "OK_RAW105_AUDIT_ONLY_CHECK_DAILY_FIELDS"
} else {
    "FAIL_OR_REVIEW_REQUIRED"
}

$OfficialReadable = if ($TodaySafe -eq "NO_TRADE_NO_NEW_BUYS") {
    "今天不交易 / 不开新仓。"
} else {
    "今日操作需要人工复核。"
}

$Txt = New-Object System.Collections.Generic.List[string]
$Txt.Add("V17.7G-R1 DYNAMIC RAW105 MANUAL DAILY")
$Txt.Add("Generated: $RunTime")
$Txt.Add("")
$Txt.Add("1. STATUS")
$Txt.Add("V17_7G_R1_STATUS: $Status")
$Txt.Add("UPSTREAM_V17_7C_R1_STATUS: $V17_7C_R1_Status")
$Txt.Add("BASE_DAILY_STATUS: $BaseDailyStatus")
$Txt.Add("MANUAL_DAILY_STATUS: $ManualDailyStatus")
$Txt.Add("")
$Txt.Add("2. TODAY OPERATION ADVICE")
$Txt.Add("TODAY_SAFE: $TodaySafe")
$Txt.Add("OFFICIAL_ACTION: $OfficialAction")
$Txt.Add("BUDGET_ACTION: $BudgetAction")
$Txt.Add("BUY_PERMISSION: $BuyPermission")
$Txt.Add("GLOBAL_MODE: $GlobalMode")
$Txt.Add("CRITICAL_UNKNOWN_COUNT: $CriticalUnknownCount")
$Txt.Add("READABLE_CONCLUSION: $OfficialReadable")
$Txt.Add("")
$Txt.Add("3. CORRECT UNIVERSE HIERARCHY")
$Txt.Add("RAW_UNIVERSE_COUNT: $RawUniverseCount")
$Txt.Add("CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount")
$Txt.Add("MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeUniverseCount")
$Txt.Add("SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCandidateCount")
$Txt.Add("")
$Txt.Add("4. RAW105 PRICE REFRESH")
$Txt.Add("RAW105_PRICE_REFRESH_STATUS: $Raw105PriceRefreshStatus")
$Txt.Add("PRICE_REFRESH_OK_COUNT: $PriceRefreshOkCount")
$Txt.Add("PRICE_REFRESH_FAIL_COUNT: $PriceRefreshFailCount")
$Txt.Add("MAX_LATEST_PRICE_DATE: $MaxLatestPriceDate")
$Txt.Add("LATEST_DATE_COUNT: $LatestDateCount")
$Txt.Add("OK_BUT_NOT_MAX_DATE_COUNT: $OkButNotMaxDateCount")
$Txt.Add("PRICE_FRESHNESS_ACCEPTANCE_STATUS: $FreshnessAcceptanceStatus")
$Txt.Add("")
$Txt.Add("5. MAIN COMPUTE PRICE AUDIT")
$Txt.Add("PRICE_AUDIT_STATUS: $PriceAuditStatus")
$Txt.Add("PRICE_ROW_COUNT: $PriceRowCount")
$Txt.Add("PRICE_OK_COUNT: $MainPriceOkCount")
$Txt.Add("PRICE_FAIL_COUNT: $MainPriceFailCount")
$Txt.Add("PRICE_STALE_COUNT: $MainPriceStaleCount")
$Txt.Add("MIN_LATEST_PRICE_DATE: $MainMinLatestPriceDate")
$Txt.Add("MAX_LATEST_PRICE_DATE: $MainMaxLatestPriceDate")
$Txt.Add("")
$Txt.Add("6. DELTA / REMOVED INSPECTION")
$Txt.Add("DELTA_AUDIT_STATUS: $DeltaAuditStatus")
$Txt.Add("REMOVED_INSPECTION_STATUS: $RemovedInspectionStatus")
$Txt.Add("")
$Txt.Add("7. HEALTH")
$Txt.Add("V16_HEALTH_STATUS: $V16HealthStatus")
$Txt.Add("HEALTH_COMPAT_STATUS: $HealthCompatStatus")
$Txt.Add("")
$Txt.Add("8. READ FILES")
$Txt.Add("THIS_REPORT_TXT: $SummaryTxt")
$Txt.Add("THIS_REPORT_MD: $SummaryMd")
$Txt.Add("READ_FIRST: $ReadFirst")
$Txt.Add("LATEST_BASE_MANUAL_DAILY: $LatestManualPath")
$Txt.Add("UPSTREAM_SUMMARY: $C_R1_Summary")
$Txt.Add("RAW105_REFRESH: $F_Refresh")
$Txt.Add("FRESHNESS_ACCEPTANCE: $F_B_Accept")
$Txt.Add("UNIVERSE_SEMANTIC: $Semantic")
$Txt.Add("DELTA_AUDIT: $Delta")
$Txt.Add("REMOVED_INSPECTION: $Removed")
$Txt.Add("")
$Txt.Add("9. NEXT NORMAL COMMAND")
$Txt.Add('Set-Location "D:\us-tech-quant"')
$Txt.Add('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1"')

$Txt | Set-Content -Path $SummaryTxt -Encoding UTF8

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.7G-R1 Dynamic RAW105 Manual Daily")
$Md.Add("")
$Md.Add("Generated: $RunTime")
$Md.Add("")
$Md.Add("## 1. Status")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---|")
$Md.Add("| V17_7G_R1_STATUS | $Status |")
$Md.Add("| UPSTREAM_V17_7C_R1_STATUS | $V17_7C_R1_Status |")
$Md.Add("| BASE_DAILY_STATUS | $BaseDailyStatus |")
$Md.Add("| MANUAL_DAILY_STATUS | $ManualDailyStatus |")
$Md.Add("")
$Md.Add("## 2. Today Operation Advice")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---|")
$Md.Add("| TODAY_SAFE | $TodaySafe |")
$Md.Add("| OFFICIAL_ACTION | $OfficialAction |")
$Md.Add("| BUDGET_ACTION | $BudgetAction |")
$Md.Add("| BUY_PERMISSION | $BuyPermission |")
$Md.Add("| GLOBAL_MODE | $GlobalMode |")
$Md.Add("| CRITICAL_UNKNOWN_COUNT | $CriticalUnknownCount |")
$Md.Add("")
$Md.Add("Conclusion: $OfficialReadable")
$Md.Add("")
$Md.Add("## 3. Correct Universe Hierarchy")
$Md.Add("")
$Md.Add("| layer | count |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_UNIVERSE_COUNT | $RawUniverseCount |")
$Md.Add("| CLASSIFIED_UNIVERSE_COUNT | $ClassifiedUniverseCount |")
$Md.Add("| MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC | $MainComputeUniverseCount |")
$Md.Add("| SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC | $SecondStageCandidateCount |")
$Md.Add("")
$Md.Add("MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC is not hardcoded. It can change day by day.")
$Md.Add("")
$Md.Add("## 4. RAW105 Price Refresh")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| RAW105_PRICE_REFRESH_STATUS | $Raw105PriceRefreshStatus |")
$Md.Add("| PRICE_REFRESH_OK_COUNT | $PriceRefreshOkCount |")
$Md.Add("| PRICE_REFRESH_FAIL_COUNT | $PriceRefreshFailCount |")
$Md.Add("| MAX_LATEST_PRICE_DATE | $MaxLatestPriceDate |")
$Md.Add("| LATEST_DATE_COUNT | $LatestDateCount |")
$Md.Add("| OK_BUT_NOT_MAX_DATE_COUNT | $OkButNotMaxDateCount |")
$Md.Add("| PRICE_FRESHNESS_ACCEPTANCE_STATUS | $FreshnessAcceptanceStatus |")
$Md.Add("")
$Md.Add("## 5. Main Compute Price Audit")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| PRICE_AUDIT_STATUS | $PriceAuditStatus |")
$Md.Add("| PRICE_ROW_COUNT | $PriceRowCount |")
$Md.Add("| PRICE_OK_COUNT | $MainPriceOkCount |")
$Md.Add("| PRICE_FAIL_COUNT | $MainPriceFailCount |")
$Md.Add("| PRICE_STALE_COUNT | $MainPriceStaleCount |")
$Md.Add("| MIN_LATEST_PRICE_DATE | $MainMinLatestPriceDate |")
$Md.Add("| MAX_LATEST_PRICE_DATE | $MainMaxLatestPriceDate |")
$Md.Add("")
$Md.Add("## 6. Read Files")
$Md.Add("")
$Md.Add("- TXT report: $SummaryTxt")
$Md.Add("- MD report: $SummaryMd")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("- Latest base manual daily: $LatestManualPath")
$Md.Add("- Upstream summary: $C_R1_Summary")
$Md.Add("- RAW105 refresh: $F_Refresh")
$Md.Add("- Freshness acceptance: $F_B_Accept")
$Md.Add("- Universe semantic audit: $Semantic")
$Md.Add("- Delta audit: $Delta")
$Md.Add("- Removed inspection: $Removed")
$Md.Add("")
$Md.Add("## 7. Next Normal Command")
$Md.Add("")
$Md.Add('Set-Location "D:\us-tech-quant"')
$Md.Add("")
$Md.Add('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1"')
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7G-R1 DYNAMIC RAW105 MANUAL DAILY READY ==="
$Rf += "V17_7G_R1_STATUS: $Status"
$Rf += "TODAY_SAFE: $TodaySafe"
$Rf += "OFFICIAL_ACTION: $OfficialAction"
$Rf += "BUDGET_ACTION: $BudgetAction"
$Rf += "BUY_PERMISSION: $BuyPermission"
$Rf += "GLOBAL_MODE: $GlobalMode"
$Rf += "RAW_UNIVERSE_COUNT: $RawUniverseCount"
$Rf += "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeUniverseCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCandidateCount"
$Rf += "RAW105_PRICE_REFRESH_STATUS: $Raw105PriceRefreshStatus"
$Rf += "PRICE_REFRESH_OK_COUNT: $PriceRefreshOkCount"
$Rf += "PRICE_REFRESH_FAIL_COUNT: $PriceRefreshFailCount"
$Rf += "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $FreshnessAcceptanceStatus"
$Rf += "PRICE_AUDIT_STATUS: $PriceAuditStatus"
$Rf += "PRICE_ROW_COUNT: $PriceRowCount"
$Rf += "PRICE_OK_COUNT: $MainPriceOkCount"
$Rf += "PRICE_FAIL_COUNT: $MainPriceFailCount"
$Rf += "PRICE_STALE_COUNT: $MainPriceStaleCount"
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryTxt
$Rf += ""
$Rf += "MD REPORT:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "LATEST BASE MANUAL DAILY:"
$Rf += $LatestManualPath
$Rf += ""
$Rf += "NEXT NORMAL COMMAND:"
$Rf += 'Set-Location "D:\us-tech-quant"'
$Rf += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_7G_R1_manual_daily_dynamic_raw105.ps1"'

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7G-R1 DYNAMIC RAW105 MANUAL DAILY READY ==="
Write-Host "V17_7G_R1_STATUS: $Status"
Write-Host "TODAY_SAFE: $TodaySafe"
Write-Host "OFFICIAL_ACTION: $OfficialAction"
Write-Host "BUDGET_ACTION: $BudgetAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host "GLOBAL_MODE: $GlobalMode"
Write-Host "RAW_UNIVERSE_COUNT: $RawUniverseCount"
Write-Host "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeUniverseCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCandidateCount"
Write-Host "RAW105_PRICE_REFRESH_STATUS: $Raw105PriceRefreshStatus"
Write-Host "PRICE_REFRESH_OK_COUNT: $PriceRefreshOkCount"
Write-Host "PRICE_REFRESH_FAIL_COUNT: $PriceRefreshFailCount"
Write-Host "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $FreshnessAcceptanceStatus"
Write-Host "PRICE_AUDIT_STATUS: $PriceAuditStatus"
Write-Host "PRICE_ROW_COUNT: $PriceRowCount"
Write-Host "PRICE_OK_COUNT: $MainPriceOkCount"
Write-Host "PRICE_FAIL_COUNT: $MainPriceFailCount"
Write-Host "PRICE_STALE_COUNT: $MainPriceStaleCount"
Write-Host ""
Write-Host "START HERE:"
Write-Host $SummaryTxt
Write-Host ""
Write-Host "MD REPORT:"
Write-Host $SummaryMd
Write-Host ""
Write-Host "READ FIRST:"
Write-Host $ReadFirst

Write-Host ""
Write-Host "=== V17.7G-R1 DYNAMIC RAW105 MANUAL DAILY DONE ==="

if ($Status -like "FAIL*") {
    exit 1
}

exit 0
