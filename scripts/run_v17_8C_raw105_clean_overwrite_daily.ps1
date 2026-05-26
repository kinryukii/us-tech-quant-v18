$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

$DecisionDir = Join-Path $Root "outputs\v17\raw105_decision"
$ManualDir = Join-Path $Root "outputs\v17\manual_daily"
$OpsDir = Join-Path $Root "outputs\v17\ops"

New-Item -ItemType Directory -Force -Path $DecisionDir | Out-Null
New-Item -ItemType Directory -Force -Path $ManualDir | Out-Null
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$Upstream = Join-Path $Root "scripts\run_v17_8B_raw105_full_decision_readable_panel.ps1"

$CurrentTxt = Join-Path $DecisionDir "V17_8C_CURRENT_RAW105_DECISION_PANEL.txt"
$CurrentMd = Join-Path $DecisionDir "V17_8C_CURRENT_RAW105_DECISION_PANEL.md"
$CurrentReadFirst = Join-Path $DecisionDir "V17_8C_READ_FIRST.txt"

$CurrentFullCsv = Join-Path $DecisionDir "v17_8C_current_raw105_full_decision.csv"
$CurrentWorthReviewCsv = Join-Path $DecisionDir "v17_8C_current_worth_review_but_locked.csv"
$CurrentActionableCsv = Join-Path $DecisionDir "v17_8C_current_actionable_buy_candidates.csv"

$CleanupReport = Join-Path $OpsDir "V17_8C_cleanup_overwrite_report.csv"

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

function Copy-IfExists {
    param(
        [string]$Source,
        [string]$Dest
    )

    if (Test-Path $Source) {
        Copy-Item -Path $Source -Destination $Dest -Force
        return $true
    }

    return $false
}

function Remove-GeneratedFiles {
    param(
        [array]$Targets
    )

    $rows = New-Object System.Collections.Generic.List[object]

    foreach ($t in $Targets) {
        $dir = $t.Dir
        $pattern = $t.Pattern

        if (-not (Test-Path $dir)) {
            continue
        }

        $files = Get-ChildItem -Path $dir -Filter $pattern -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending

        foreach ($f in $files) {
            $status = "PENDING"
            try {
                Remove-Item -Path $f.FullName -Force
                $status = "DELETED"
            } catch {
                $status = "DELETE_FAILED"
            }

            $rows.Add([pscustomobject]@{
                pattern = $pattern
                status = $status
                last_write_time = $f.LastWriteTime
                length = $f.Length
                full_name = $f.FullName
            })
        }
    }

    return $rows
}

Write-Host ""
Write-Host "=== V17.8C RAW105 CLEAN OVERWRITE DAILY START ==="

if (-not (Test-Path $Upstream)) {
    throw "Missing upstream V17.8B script: $Upstream"
}

Write-Host ""
Write-Host "=== RUN UPSTREAM V17.8B FROM SCRATCH ==="
powershell -NoProfile -ExecutionPolicy Bypass -File $Upstream

if ($LASTEXITCODE -ne 0) {
    throw "Upstream V17.8B failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "=== COPY LATEST OUTPUTS TO FIXED CURRENT FILES ==="

$LatestPanelTxt = Get-ChildItem -Path $DecisionDir -Filter "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL_*.txt" -File |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $LatestPanelTxt) {
    throw "Latest V17.8B panel txt not found."
}

$V8BMd = Join-Path $DecisionDir "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL.md"
$V8BReadFirst = Join-Path $DecisionDir "V17_8B_READ_FIRST.txt"

$V8AFullCsv = Join-Path $DecisionDir "v17_8A_raw105_full_decision_daily.csv"
$V8BWorthCsv = Join-Path $DecisionDir "v17_8B_worth_review_but_locked.csv"
$V8BActionableCsv = Join-Path $DecisionDir "v17_8B_actionable_buy_candidates.csv"

Copy-Item -Path $LatestPanelTxt.FullName -Destination $CurrentTxt -Force

if (-not (Copy-IfExists -Source $V8BMd -Dest $CurrentMd)) {
    throw "Missing V17.8B md report: $V8BMd"
}

Copy-IfExists -Source $V8AFullCsv -Dest $CurrentFullCsv | Out-Null
Copy-IfExists -Source $V8BWorthCsv -Dest $CurrentWorthReviewCsv | Out-Null
Copy-IfExists -Source $V8BActionableCsv -Dest $CurrentActionableCsv | Out-Null

$kv = Read-KeyValues $V8BReadFirst

$PanelStatus = $kv["RAW105_DECISION_PANEL_STATUS"]
$FinalAction = $kv["FINAL_ACTION"]
$RawDecisionCount = $kv["RAW_UNIVERSE_DECISION_COUNT"]
$MainComputeCount = $kv["MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC"]
$SecondStageCount = $kv["SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC"]
$RawPriceOkCount = $kv["RAW105_PRICE_OK_COUNT"]
$RawPriceFailCount = $kv["RAW105_PRICE_FAIL_COUNT"]
$ActionableBuyCount = $kv["ACTIONABLE_BUY_COUNT_TODAY"]
$WorthReviewCount = $kv["WORTH_REVIEW_BUT_LOCKED_COUNT"]
$TodaySafe = $kv["TODAY_SAFE"]
$OfficialAction = $kv["OFFICIAL_ACTION"]
$BudgetAction = $kv["BUDGET_ACTION"]
$BuyPermission = $kv["BUY_PERMISSION"]

$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Rf = @()
$Rf += "=== V17.8C CURRENT RAW105 CLEAN OVERWRITE DAILY ==="
$Rf += "Generated: $RunTime"
$Rf += ""
$Rf += "RAW105_DECISION_PANEL_STATUS: $PanelStatus"
$Rf += "FINAL_ACTION: $FinalAction"
$Rf += "RAW_UNIVERSE_DECISION_COUNT: $RawDecisionCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount"
$Rf += "RAW105_PRICE_OK_COUNT: $RawPriceOkCount"
$Rf += "RAW105_PRICE_FAIL_COUNT: $RawPriceFailCount"
$Rf += "ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount"
$Rf += "WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount"
$Rf += "TODAY_SAFE: $TodaySafe"
$Rf += "OFFICIAL_ACTION: $OfficialAction"
$Rf += "BUDGET_ACTION: $BudgetAction"
$Rf += "BUY_PERMISSION: $BuyPermission"
$Rf += ""
$Rf += "START HERE:"
$Rf += $CurrentTxt
$Rf += ""
$Rf += "MD REPORT:"
$Rf += $CurrentMd
$Rf += ""
$Rf += "FULL RAW105 DECISION CSV:"
$Rf += $CurrentFullCsv
$Rf += ""
$Rf += "WORTH REVIEW CSV:"
$Rf += $CurrentWorthReviewCsv
$Rf += ""
$Rf += "ACTIONABLE BUY CSV:"
$Rf += $CurrentActionableCsv
$Rf += ""
$Rf += "NEXT NORMAL COMMAND:"
$Rf += 'Set-Location "D:\us-tech-quant"'
$Rf += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_8C_raw105_clean_overwrite_daily.ps1"'

$Rf | Set-Content -Path $CurrentReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== CLEAN TIMESTAMP GENERATED FILES ==="

$Targets = @(
    @{
        Dir = $ManualDir
        Pattern = "V17_6F_E_MANUAL_DAILY_STABLE_*.txt"
    },
    @{
        Dir = $ManualDir
        Pattern = "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_*.txt"
    },
    @{
        Dir = $ManualDir
        Pattern = "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_*.md"
    },
    @{
        Dir = $ManualDir
        Pattern = "v17_6F_E_full_universe_chain_*.log"
    },
    @{
        Dir = $ManualDir
        Pattern = "v17_6F_E_price_audit_*.log"
    },
    @{
        Dir = $ManualDir
        Pattern = "v17_6F_E_official_daily_*.log"
    },
    @{
        Dir = $ManualDir
        Pattern = "v17_7G_R1_steps_*.csv"
    },
    @{
        Dir = $DecisionDir
        Pattern = "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL_*.txt"
    }
)

$CleanupRows = Remove-GeneratedFiles -Targets $Targets
$CleanupRows | Export-Csv -Path $CleanupReport -NoTypeInformation -Encoding UTF8

$DeletedCount = @($CleanupRows | Where-Object { $_.status -eq "DELETED" }).Count
$FailedCount = @($CleanupRows | Where-Object { $_.status -eq "DELETE_FAILED" }).Count

Write-Host ""
Write-Host "=== V17.8C RAW105 CLEAN OVERWRITE DAILY READY ==="
Write-Host "RAW105_DECISION_PANEL_STATUS: $PanelStatus"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "RAW_UNIVERSE_DECISION_COUNT: $RawDecisionCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount"
Write-Host "ACTIONABLE_BUY_COUNT_TODAY: $ActionableBuyCount"
Write-Host "WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount"
Write-Host "TODAY_SAFE: $TodaySafe"
Write-Host "OFFICIAL_ACTION: $OfficialAction"
Write-Host "BUDGET_ACTION: $BudgetAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host ""
Write-Host "CURRENT READ FIRST:"
Write-Host $CurrentReadFirst
Write-Host ""
Write-Host "CURRENT TXT:"
Write-Host $CurrentTxt
Write-Host ""
Write-Host "CURRENT MD:"
Write-Host $CurrentMd
Write-Host ""
Write-Host "CLEANUP_REPORT:"
Write-Host $CleanupReport
Write-Host ""
Write-Host "TIMESTAMP_FILES_DELETED: $DeletedCount"
Write-Host "TIMESTAMP_DELETE_FAILED: $FailedCount"
Write-Host ""
Write-Host "=== V17.8C RAW105 CLEAN OVERWRITE DAILY DONE ==="

if ($FailedCount -gt 0) {
    exit 1
}

exit 0
