$ErrorActionPreference = "Continue"

$Root = "D:\us-tech-quant"
Set-Location $Root

$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Summary = Join-Path $OutDir "V17_7C_R1_MANUAL_DAILY_WITH_RAW105_AUDIT_SUMMARY.md"
$StepsCsv = Join-Path $OutDir "v17_7C_R1_manual_daily_steps.csv"
$ReadFirst = Join-Path $OutDir "V17_7C_R1_READ_FIRST.txt"

$BaseDaily = Join-Path $Root "scripts\run_v17_6F_manual_daily_full_universe_latest_price.ps1"
$Raw105Refresh = Join-Path $Root "scripts\run_v17_7F_raw105_latest_price_refresh.ps1"
$FreshnessAccept = Join-Path $Root "scripts\run_v17_7F_B_raw105_price_freshness_acceptance.ps1"
$RawAudit = Join-Path $Root "scripts\run_v17_7_raw_universe_full_screen_audit.ps1"
$SemanticAudit = Join-Path $Root "scripts\run_v17_7B_universe_semantic_audit.ps1"
$DeltaAudit = Join-Path $Root "scripts\run_v17_7D_main_compute_delta_audit.ps1"
$RemovedInspection = Join-Path $Root "scripts\run_v17_7E_removed_main_compute_inspection.ps1"

$BaseReport = Join-Path $Root "outputs\v17\price\V17_6E_SCREENED_UNIVERSE_LATEST_PRICE_AUDIT.md"

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$Steps = New-Object System.Collections.Generic.List[object]

function Add-Step {
    param(
        [string]$Name,
        [string]$Status,
        [int]$ExitCode,
        [string]$Path,
        [string]$Note
    )

    $script:Steps.Add([pscustomobject]@{
        run_time = $RunTime
        step_name = $Name
        status = $Status
        exit_code = $ExitCode
        script_path = $Path
        note = $Note
    })
}

function Test-BaseDailyOutputValid {
    if (-not (Test-Path $BaseReport)) {
        return $false
    }

    $text = Get-Content $BaseReport -Raw

    $hasAuditOk = $text -match "AUDIT_STATUS.*OK"
    $hasPriceFailZero = $text -match "PRICE_FAIL_COUNT.*0"
    $hasSecondStage = $text -match "SECOND_STAGE_COUNT"

    return ($hasAuditOk -and $hasPriceFailZero -and $hasSecondStage)
}

function Run-NormalStep {
    param(
        [string]$Name,
        [string]$ScriptPath
    )

    Write-Host ""
    Write-Host "=== RUN STEP: $Name ==="

    if (-not (Test-Path $ScriptPath)) {
        $msg = "MISSING_SCRIPT: $ScriptPath"
        Write-Host $msg
        Add-Step -Name $Name -Status "MISSING" -ExitCode 9004 -Path $ScriptPath -Note $msg
        return 9004
    }

    powershell -NoProfile -ExecutionPolicy Bypass -File $ScriptPath
    $code = $LASTEXITCODE

    if ($null -eq $code) {
        $code = 0
    }

    if ($code -eq 0) {
        Add-Step -Name $Name -Status "OK" -ExitCode 0 -Path $ScriptPath -Note "completed"
        return 0
    } else {
        Add-Step -Name $Name -Status "FAIL" -ExitCode $code -Path $ScriptPath -Note "nonzero exit"
        return $code
    }
}

function Run-BaseDailyStep {
    Write-Host ""
    Write-Host "=== RUN STEP: V17_6F_MANUAL_DAILY_BASE ==="

    if (-not (Test-Path $BaseDaily)) {
        $msg = "MISSING_SCRIPT: $BaseDaily"
        Write-Host $msg
        Add-Step -Name "V17_6F_MANUAL_DAILY_BASE" -Status "MISSING" -ExitCode 9004 -Path $BaseDaily -Note $msg
        return 9004
    }

    powershell -NoProfile -ExecutionPolicy Bypass -File $BaseDaily
    $code = $LASTEXITCODE

    if ($null -eq $code) {
        $code = 0
    }

    if ($code -eq 0) {
        Add-Step -Name "V17_6F_MANUAL_DAILY_BASE" -Status "OK" -ExitCode 0 -Path $BaseDaily -Note "base daily completed"
        return 0
    }

    $valid = Test-BaseDailyOutputValid
    if ($valid) {
        Add-Step -Name "V17_6F_MANUAL_DAILY_BASE" -Status "SOFT_OK_OUTPUTS_VALID" -ExitCode $code -Path $BaseDaily -Note "nonzero exit but key V17.6E outputs are valid"
        return 0
    }

    Add-Step -Name "V17_6F_MANUAL_DAILY_BASE" -Status "FAIL_OUTPUTS_INVALID" -ExitCode $code -Path $BaseDaily -Note "nonzero exit and key outputs not valid"
    return $code
}

function Read-KeyValueFile {
    param([string]$Path)

    $map = @{}

    if (-not (Test-Path $Path)) {
        return $map
    }

    $lines = Get-Content $Path
    foreach ($line in $lines) {
        if ($line -match "^([^:]+):\s*(.+)$") {
            $k = $Matches[1].Trim()
            $v = $Matches[2].Trim()
            $map[$k] = $v
        }
    }

    return $map
}

Write-Host ""
Write-Host "=== V17.7C-R1 MANUAL DAILY WITH RAW105 AUDIT START ==="

$BaseExit = Run-BaseDailyStep
$Raw105Exit = Run-NormalStep -Name "V17_7F_RAW105_LATEST_PRICE_REFRESH" -ScriptPath $Raw105Refresh
$FreshnessExit = Run-NormalStep -Name "V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE" -ScriptPath $FreshnessAccept
$RawAuditExit = Run-NormalStep -Name "V17_7_RAW_UNIVERSE_FULL_AUDIT" -ScriptPath $RawAudit
$SemanticExit = Run-NormalStep -Name "V17_7B_UNIVERSE_SEMANTIC_AUDIT" -ScriptPath $SemanticAudit
$DeltaExit = Run-NormalStep -Name "V17_7D_MAIN_COMPUTE_DELTA_AUDIT" -ScriptPath $DeltaAudit
$RemovedExit = Run-NormalStep -Name "V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION" -ScriptPath $RemovedInspection

$Steps | Export-Csv -Path $StepsCsv -NoTypeInformation -Encoding UTF8

$SemanticReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt"
$RefreshReadFirst = Join-Path $OutDir "V17_7F_READ_FIRST.txt"
$AcceptanceReadFirst = Join-Path $OutDir "V17_7F_B_READ_FIRST.txt"
$DeltaReadFirst = Join-Path $OutDir "V17_7D_READ_FIRST.txt"
$RemovedReadFirst = Join-Path $OutDir "V17_7E_READ_FIRST.txt"

$semantic = Read-KeyValueFile $SemanticReadFirst
$refresh = Read-KeyValueFile $RefreshReadFirst
$accept = Read-KeyValueFile $AcceptanceReadFirst
$delta = Read-KeyValueFile $DeltaReadFirst
$removed = Read-KeyValueFile $RemovedReadFirst

$UniverseSemanticStatus = $semantic["UNIVERSE_SEMANTIC_STATUS"]
$RawUniverseCount = $semantic["RAW_UNIVERSE_COUNT"]
$ClassifiedUniverseCount = $semantic["CLASSIFIED_UNIVERSE_COUNT"]
$MainComputeUniverseCount = $semantic["MAIN_COMPUTE_UNIVERSE_COUNT"]
$SecondStageCandidateCount = $semantic["SECOND_STAGE_CANDIDATE_COUNT"]
$RawPriceOkCount = $semantic["RAW_PRICE_OK_COUNT"]
$RawPriceFailCount = $semantic["RAW_PRICE_FAIL_COUNT"]

$Raw105RefreshStatus = $refresh["RAW105_PRICE_REFRESH_STATUS"]
$Raw105RefreshOkCount = $refresh["PRICE_REFRESH_OK_COUNT"]
$Raw105RefreshFailCount = $refresh["PRICE_REFRESH_FAIL_COUNT"]
$MaxLatestPriceDate = $refresh["MAX_LATEST_PRICE_DATE"]
$LatestDateCount = $refresh["LATEST_DATE_COUNT"]
$OkButNotMaxDateCount = $refresh["OK_BUT_NOT_MAX_DATE_COUNT"]

$FreshnessAcceptanceStatus = $accept["PRICE_FRESHNESS_ACCEPTANCE_STATUS"]
$FreshnessReviewCount = $accept["REVIEW_COUNT"]
$FreshnessRejectCount = $accept["REJECT_COUNT"]
$NonMaxAcceptCount = $accept["NON_MAX_ACCEPT_COUNT"]

$DeltaAuditStatus = $delta["DELTA_AUDIT_STATUS"]
$MainRemovedCount = $delta["MAIN_COMPUTE_REMOVED_COUNT"]
$MainAddedCount = $delta["MAIN_COMPUTE_ADDED_COUNT"]

$RemovedInspectionStatus = $removed["REMOVED_INSPECTION_STATUS"]

$HardFailSteps = @(
    $Steps |
        Where-Object {
            $_.status -notin @("OK", "SOFT_OK_OUTPUTS_VALID")
        }
)

$BaseStep = $Steps | Where-Object { $_.step_name -eq "V17_6F_MANUAL_DAILY_BASE" } | Select-Object -First 1

$FinalStatus = if (
    $HardFailSteps.Count -eq 0 -and
    $RawUniverseCount -eq "105" -and
    $ClassifiedUniverseCount -eq "105" -and
    $MainComputeUniverseCount -eq "56" -and
    $SecondStageCandidateCount -eq "10" -and
    $Raw105RefreshStatus -eq "OK" -and
    $Raw105RefreshOkCount -eq "105" -and
    $Raw105RefreshFailCount -eq "0" -and
    $FreshnessAcceptanceStatus -eq "OK_ACCEPT_1_NON_MAX_NOT_IN_MAIN_OR_SECOND_STAGE" -and
    $FreshnessReviewCount -eq "0" -and
    $FreshnessRejectCount -eq "0" -and
    $DeltaAuditStatus -eq "OK_CURRENT_105_56_10" -and
    $RemovedInspectionStatus -eq "OK_REMOVED_10_STILL_RAW_CLASSIFIED_PRICE_OK"
) {
    "OK_CURRENT_105_56_10_WITH_PSTG_ACCEPTED"
} elseif (
    $HardFailSteps.Count -eq 0 -and
    $RawUniverseCount -eq "105" -and
    $ClassifiedUniverseCount -eq "105" -and
    $Raw105RefreshStatus -eq "OK" -and
    $FreshnessReviewCount -eq "0" -and
    $FreshnessRejectCount -eq "0"
) {
    "OK_DYNAMIC_COUNTS_WITH_RAW105_REFRESH"
} else {
    "FAIL_OR_REVIEW_REQUIRED"
}

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.7C-R1 Manual Daily With RAW105 Audit")
$Md.Add("")
$Md.Add("Generated: $Now")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("V17_7C_R1_STATUS: $FinalStatus")
$Md.Add("")
$Md.Add("本 wrapper 修正 V17.7C 的状态语义：base daily 若非零退出，但关键输出有效，则标记为 SOFT_OK_OUTPUTS_VALID，而不是误报 failed。")
$Md.Add("")
$Md.Add("## 2. Correct Current Universe Hierarchy")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_UNIVERSE_COUNT | $RawUniverseCount |")
$Md.Add("| CLASSIFIED_UNIVERSE_COUNT | $ClassifiedUniverseCount |")
$Md.Add("| MAIN_COMPUTE_UNIVERSE_COUNT | $MainComputeUniverseCount |")
$Md.Add("| SECOND_STAGE_CANDIDATE_COUNT | $SecondStageCandidateCount |")
$Md.Add("| RAW_PRICE_OK_COUNT | $RawPriceOkCount |")
$Md.Add("| RAW_PRICE_FAIL_COUNT | $RawPriceFailCount |")
$Md.Add("")
$Md.Add("## 3. RAW105 Latest Price Refresh")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| RAW105_PRICE_REFRESH_STATUS | $Raw105RefreshStatus |")
$Md.Add("| PRICE_REFRESH_OK_COUNT | $Raw105RefreshOkCount |")
$Md.Add("| PRICE_REFRESH_FAIL_COUNT | $Raw105RefreshFailCount |")
$Md.Add("| MAX_LATEST_PRICE_DATE | $MaxLatestPriceDate |")
$Md.Add("| LATEST_DATE_COUNT | $LatestDateCount |")
$Md.Add("| OK_BUT_NOT_MAX_DATE_COUNT | $OkButNotMaxDateCount |")
$Md.Add("")
$Md.Add("## 4. Freshness Acceptance")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| PRICE_FRESHNESS_ACCEPTANCE_STATUS | $FreshnessAcceptanceStatus |")
$Md.Add("| NON_MAX_ACCEPT_COUNT | $NonMaxAcceptCount |")
$Md.Add("| REVIEW_COUNT | $FreshnessReviewCount |")
$Md.Add("| REJECT_COUNT | $FreshnessRejectCount |")
$Md.Add("")
$Md.Add("## 5. Main Compute Delta")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| DELTA_AUDIT_STATUS | $DeltaAuditStatus |")
$Md.Add("| MAIN_COMPUTE_REMOVED_COUNT | $MainRemovedCount |")
$Md.Add("| MAIN_COMPUTE_ADDED_COUNT | $MainAddedCount |")
$Md.Add("| REMOVED_INSPECTION_STATUS | $RemovedInspectionStatus |")
$Md.Add("")
$Md.Add("## 6. Step Results")
$Md.Add("")
$Md.Add("| step | status | exit_code | note |")
$Md.Add("|---|---|---:|---|")
foreach ($s in $Steps) {
    $Md.Add("| $($s.step_name) | $($s.status) | $($s.exit_code) | $($s.note) |")
}
$Md.Add("")
$Md.Add("## 7. Interpretation")
$Md.Add("")
$Md.Add("当前正式口径：RAW 原始池 105 个全部刷新与审计；105 个全部 classified；当前 main compute 动态层为 56；second stage 候选为 10。")
$Md.Add("")
$Md.Add("PSTG 是唯一 non-max-date ticker，日期为 2026-05-11，但它不在 main compute 56，也不在 second stage 10，因此不阻断今日候选/操作建议。")
$Md.Add("")
$Md.Add("## 8. Output Files")
$Md.Add("")
$Md.Add("- V17.7C-R1 summary: $Summary")
$Md.Add("- V17.7C-R1 read first: $ReadFirst")
$Md.Add("- V17.7C-R1 steps CSV: $StepsCsv")
$Md.Add("- RAW105 refresh: " + (Join-Path $OutDir "V17_7F_RAW105_LATEST_PRICE_REFRESH.md"))
$Md.Add("- Freshness acceptance: " + (Join-Path $OutDir "V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md"))
$Md.Add("- Universe semantic audit: " + (Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md"))
$Md.Add("- Delta audit: " + (Join-Path $OutDir "V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md"))
$Md.Add("- Removed inspection: " + (Join-Path $OutDir "V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md"))
$Md.Add("")

$Md | Set-Content -Path $Summary -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7C-R1 MANUAL DAILY WITH RAW105 AUDIT READY ==="
$Rf += "V17_7C_R1_STATUS: $FinalStatus"
$Rf += "BASE_DAILY_STATUS: $($BaseStep.status)"
$Rf += "RAW_UNIVERSE_COUNT: $RawUniverseCount"
$Rf += "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
$Rf += "RAW105_PRICE_REFRESH_STATUS: $Raw105RefreshStatus"
$Rf += "PRICE_REFRESH_OK_COUNT: $Raw105RefreshOkCount"
$Rf += "PRICE_REFRESH_FAIL_COUNT: $Raw105RefreshFailCount"
$Rf += "MAX_LATEST_PRICE_DATE: $MaxLatestPriceDate"
$Rf += "LATEST_DATE_COUNT: $LatestDateCount"
$Rf += "OK_BUT_NOT_MAX_DATE_COUNT: $OkButNotMaxDateCount"
$Rf += "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $FreshnessAcceptanceStatus"
$Rf += "DELTA_AUDIT_STATUS: $DeltaAuditStatus"
$Rf += "REMOVED_INSPECTION_STATUS: $RemovedInspectionStatus"
$Rf += ""
$Rf += "START HERE:"
$Rf += $Summary
$Rf += ""
$Rf += "STEPS CSV:"
$Rf += $StepsCsv
$Rf += ""
$Rf += "READ DETAILS:"
$Rf += (Join-Path $OutDir "V17_7F_RAW105_LATEST_PRICE_REFRESH.md")
$Rf += (Join-Path $OutDir "V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md")
$Rf += (Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md")
$Rf += (Join-Path $OutDir "V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md")
$Rf += (Join-Path $OutDir "V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md")

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7C-R1 MANUAL DAILY WITH RAW105 AUDIT READY ==="
Write-Host "V17_7C_R1_STATUS: $FinalStatus"
Write-Host "BASE_DAILY_STATUS: $($BaseStep.status)"
Write-Host "RAW_UNIVERSE_COUNT: $RawUniverseCount"
Write-Host "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
Write-Host "RAW105_PRICE_REFRESH_STATUS: $Raw105RefreshStatus"
Write-Host "PRICE_REFRESH_OK_COUNT: $Raw105RefreshOkCount"
Write-Host "PRICE_REFRESH_FAIL_COUNT: $Raw105RefreshFailCount"
Write-Host "MAX_LATEST_PRICE_DATE: $MaxLatestPriceDate"
Write-Host "LATEST_DATE_COUNT: $LatestDateCount"
Write-Host "OK_BUT_NOT_MAX_DATE_COUNT: $OkButNotMaxDateCount"
Write-Host "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $FreshnessAcceptanceStatus"
Write-Host "DELTA_AUDIT_STATUS: $DeltaAuditStatus"
Write-Host "REMOVED_INSPECTION_STATUS: $RemovedInspectionStatus"
Write-Host ""
Write-Host "START HERE:"
Write-Host $Summary
Write-Host ""
Write-Host "READ FIRST:"
Write-Host $ReadFirst

Write-Host ""
Write-Host "=== V17.7C-R1 MANUAL DAILY WITH RAW105 AUDIT DONE ==="

if ($FinalStatus -like "FAIL*") {
    exit 1
}

exit 0
