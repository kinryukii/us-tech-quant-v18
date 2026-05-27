$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

$OutDir = Join-Path $Root "outputs\v17\raw105_decision"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$RunTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Upstream = Join-Path $Root "scripts\run_v17_8A_raw105_full_decision_daily.ps1"

$DecisionCsv = Join-Path $OutDir "v17_8A_raw105_full_decision_daily.csv"
$V8AReadFirst = Join-Path $OutDir "V17_8A_READ_FIRST.txt"

$PanelCsv = Join-Path $OutDir "v17_8B_raw105_decision_readable_panel.csv"
$WorthReviewCsv = Join-Path $OutDir "v17_8B_worth_review_but_locked.csv"
$ActionableCsv = Join-Path $OutDir "v17_8B_actionable_buy_candidates.csv"
$SummaryMd = Join-Path $OutDir "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL.md"
$SummaryTxt = Join-Path $OutDir "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL_$Stamp.txt"
$ReadFirst = Join-Path $OutDir "V17_8B_READ_FIRST.txt"

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

Write-Host ""
Write-Host "=== V17.8B RAW105 FULL DECISION READABLE PANEL START ==="

if (-not (Test-Path $Upstream)) {
    throw "Missing upstream V17.8A script: $Upstream"
}

Write-Host ""
Write-Host "=== RUN UPSTREAM V17.8A FROM SCRATCH ==="
powershell -NoProfile -ExecutionPolicy Bypass -File $Upstream
if ($LASTEXITCODE -ne 0) {
    throw "Upstream V17.8A failed with exit code $LASTEXITCODE"
}

if (-not (Test-Path $DecisionCsv)) {
    throw "Missing V17.8A decision CSV: $DecisionCsv"
}

$Rows = Import-Csv $DecisionCsv

if (-not $Rows -or $Rows.Count -eq 0) {
    throw "V17.8A decision CSV is empty: $DecisionCsv"
}

$V8AKv = Read-KeyValues $V8AReadFirst

$FinalAction = $V8AKv["FINAL_ACTION"]
$RawDecisionCount = $V8AKv["RAW_UNIVERSE_DECISION_COUNT"]
$MainComputeCount = $V8AKv["MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC"]
$SecondStageCount = $V8AKv["SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC"]
$RawPriceOkCount = $V8AKv["RAW105_PRICE_OK_COUNT"]
$RawPriceFailCount = $V8AKv["RAW105_PRICE_FAIL_COUNT"]
$ActionableBuyCountFromA = $V8AKv["ACTIONABLE_BUY_COUNT_TODAY"]
$WorthReviewCountFromA = $V8AKv["WORTH_REVIEW_BUT_LOCKED_COUNT"]
$TodaySafe = $V8AKv["TODAY_SAFE"]
$OfficialAction = $V8AKv["OFFICIAL_ACTION"]
$BudgetAction = $V8AKv["BUDGET_ACTION"]
$BuyPermission = $V8AKv["BUY_PERMISSION"]

$Actionable = @(
    $Rows |
        Where-Object { $_.full_buy_decision -eq "BUY_CANDIDATE_REQUIRES_MANUAL_CONFIRMATION" } |
        Sort-Object ticker
)

$WorthReview = @(
    $Rows |
        Where-Object { $_.full_buy_decision -eq "WORTH_REVIEW_BUT_NO_BUY_TODAY_EVENT_OR_BUDGET_LOCKED" } |
        Sort-Object ticker
)

$MainWatch = @(
    $Rows |
        Where-Object { $_.candidate_tier -eq "B_MAIN_COMPUTE_NOT_TOP10" } |
        Sort-Object ticker
)

$ClassifiedOnly = @(
    $Rows |
        Where-Object { $_.candidate_tier -eq "C_CLASSIFIED_NOT_MAIN_COMPUTE" } |
        Sort-Object ticker
)

$NoBuyNotMain = @(
    $Rows |
        Where-Object { $_.full_buy_decision -eq "NO_BUY_NOT_MAIN_COMPUTE" } |
        Sort-Object ticker
)

$PanelRows = New-Object System.Collections.Generic.List[object]

function Add-PanelRow {
    param(
        [object]$r,
        [string]$DisplayGroup
    )

    $script:PanelRows.Add([pscustomobject]@{
        display_group = $DisplayGroup
        ticker = $r.ticker
        candidate_tier = $r.candidate_tier
        full_buy_decision = $r.full_buy_decision
        latest_price_date = $r.raw105_latest_price_date
        latest_close = $r.raw105_latest_close
        latest_volume = $r.raw105_latest_volume
        semantic_layer = $r.semantic_layer
        is_current_main_compute = $r.is_current_main_compute
        is_current_second_stage = $r.is_current_second_stage
        decision_reason_cn = $r.decision_reason_cn
    })
}

foreach ($r in $Actionable) {
    Add-PanelRow -r $r -DisplayGroup "ACTIONABLE_BUY_CANDIDATE"
}
foreach ($r in $WorthReview) {
    Add-PanelRow -r $r -DisplayGroup "WORTH_REVIEW_BUT_LOCKED"
}
foreach ($r in $MainWatch) {
    Add-PanelRow -r $r -DisplayGroup "MAIN_COMPUTE_WATCH"
}
foreach ($r in $ClassifiedOnly) {
    Add-PanelRow -r $r -DisplayGroup "CLASSIFIED_ONLY_NOT_MAIN"
}

$PanelRows | Export-Csv -Path $PanelCsv -NoTypeInformation -Encoding UTF8
$WorthReview | Export-Csv -Path $WorthReviewCsv -NoTypeInformation -Encoding UTF8
$Actionable | Export-Csv -Path $ActionableCsv -NoTypeInformation -Encoding UTF8

$ActionableCount = $Actionable.Count
$WorthReviewCount = $WorthReview.Count
$MainWatchCount = $MainWatch.Count
$ClassifiedOnlyCount = $ClassifiedOnly.Count
$NoBuyNotMainCount = $NoBuyNotMain.Count

$PanelStatus = if (
    $RawDecisionCount -eq "105" -and
    $RawPriceOkCount -eq "105" -and
    $RawPriceFailCount -eq "0" -and
    $ActionableCount -eq 0 -and
    $WorthReviewCount -eq 10
) {
    "OK_RAW105_DECISION_READABLE_NO_BUY_10_LOCKED"
} elseif (
    $RawDecisionCount -eq "105" -and
    $RawPriceOkCount -eq "105" -and
    $RawPriceFailCount -eq "0"
) {
    "OK_RAW105_DECISION_READABLE_DYNAMIC"
} else {
    "WARN_CHECK_RAW105_DECISION_PANEL"
}

$ReadableConclusion = if ($ActionableCount -gt 0) {
    "今天存在可执行买入候选，但必须人工确认。"
} elseif ($WorthReviewCount -gt 0) {
    "今天没有可执行买入；有 $WorthReviewCount 个值得复核但被事件/预算门控锁住。"
} else {
    "今天没有可执行买入候选。"
}

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.8B RAW105 Full Decision Readable Panel")
$Md.Add("")
$Md.Add("Generated: $RunTime")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("RAW105_DECISION_PANEL_STATUS: $PanelStatus")
$Md.Add("")
$Md.Add("FINAL_ACTION: $FinalAction")
$Md.Add("")
$Md.Add("**$ReadableConclusion**")
$Md.Add("")
$Md.Add("## 2. Gate Status")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---|")
$Md.Add("| TODAY_SAFE | $TodaySafe |")
$Md.Add("| OFFICIAL_ACTION | $OfficialAction |")
$Md.Add("| BUDGET_ACTION | $BudgetAction |")
$Md.Add("| BUY_PERMISSION | $BuyPermission |")
$Md.Add("")
$Md.Add("## 3. Count Summary")
$Md.Add("")
$Md.Add("| item | count |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_UNIVERSE_DECISION_COUNT | $RawDecisionCount |")
$Md.Add("| MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC | $MainComputeCount |")
$Md.Add("| SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC | $SecondStageCount |")
$Md.Add("| RAW105_PRICE_OK_COUNT | $RawPriceOkCount |")
$Md.Add("| RAW105_PRICE_FAIL_COUNT | $RawPriceFailCount |")
$Md.Add("| ACTIONABLE_BUY_COUNT_TODAY | $ActionableCount |")
$Md.Add("| WORTH_REVIEW_BUT_LOCKED_COUNT | $WorthReviewCount |")
$Md.Add("| MAIN_COMPUTE_WATCH_COUNT | $MainWatchCount |")
$Md.Add("| CLASSIFIED_ONLY_NOT_MAIN_COUNT | $ClassifiedOnlyCount |")
$Md.Add("| NO_BUY_NOT_MAIN_COMPUTE_COUNT | $NoBuyNotMainCount |")
$Md.Add("")
$Md.Add("## 4. 今日可执行买入")
$Md.Add("")
if ($ActionableCount -eq 0) {
    $Md.Add("今日可执行买入数量为 0。")
} else {
    $Md.Add("| ticker | latest_price_date | latest_close | decision | reason |")
    $Md.Add("|---|---:|---:|---|---|")
    foreach ($r in $Actionable) {
        $Md.Add("| $($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close) | $($r.full_buy_decision) | $($r.decision_reason_cn) |")
    }
}
$Md.Add("")
$Md.Add("## 5. 今日值得复核但被锁住")
$Md.Add("")
$Md.Add("| ticker | latest_price_date | latest_close | decision | reason |")
$Md.Add("|---|---:|---:|---|---|")
foreach ($r in $WorthReview) {
    $Md.Add("| $($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close) | $($r.full_buy_decision) | $($r.decision_reason_cn) |")
}
$Md.Add("")
$Md.Add("## 6. Main Compute Watch")
$Md.Add("")
$Md.Add("这些进入主计算层但没有进入 second stage，不是今日优先买入候选。")
$Md.Add("")
$Md.Add("| ticker | latest_price_date | latest_close | decision |")
$Md.Add("|---|---:|---:|---|")
foreach ($r in ($MainWatch | Select-Object -First 30)) {
    $Md.Add("| $($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close) | $($r.full_buy_decision) |")
}
$Md.Add("")
$Md.Add("## 7. Output Files")
$Md.Add("")
$Md.Add("- Full readable panel CSV: $PanelCsv")
$Md.Add("- Worth-review locked CSV: $WorthReviewCsv")
$Md.Add("- Actionable buy CSV: $ActionableCsv")
$Md.Add("- Summary MD: $SummaryMd")
$Md.Add("- Summary TXT: $SummaryTxt")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("- Upstream V17.8A CSV: $DecisionCsv")
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Txt = New-Object System.Collections.Generic.List[string]
$Txt.Add("V17.8B RAW105 FULL DECISION READABLE PANEL")
$Txt.Add("Generated: $RunTime")
$Txt.Add("")
$Txt.Add("1. STATUS")
$Txt.Add("RAW105_DECISION_PANEL_STATUS: $PanelStatus")
$Txt.Add("FINAL_ACTION: $FinalAction")
$Txt.Add("READABLE_CONCLUSION: $ReadableConclusion")
$Txt.Add("")
$Txt.Add("2. COUNTS")
$Txt.Add("RAW_UNIVERSE_DECISION_COUNT: $RawDecisionCount")
$Txt.Add("MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount")
$Txt.Add("SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount")
$Txt.Add("RAW105_PRICE_OK_COUNT: $RawPriceOkCount")
$Txt.Add("RAW105_PRICE_FAIL_COUNT: $RawPriceFailCount")
$Txt.Add("ACTIONABLE_BUY_COUNT_TODAY: $ActionableCount")
$Txt.Add("WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount")
$Txt.Add("MAIN_COMPUTE_WATCH_COUNT: $MainWatchCount")
$Txt.Add("")
$Txt.Add("3. GATES")
$Txt.Add("TODAY_SAFE: $TodaySafe")
$Txt.Add("OFFICIAL_ACTION: $OfficialAction")
$Txt.Add("BUDGET_ACTION: $BudgetAction")
$Txt.Add("BUY_PERMISSION: $BuyPermission")
$Txt.Add("")
$Txt.Add("4. ACTIONABLE BUY CANDIDATES")
if ($ActionableCount -eq 0) {
    $Txt.Add("NONE")
} else {
    foreach ($r in $Actionable) {
        $Txt.Add("$($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close) | $($r.full_buy_decision)")
    }
}
$Txt.Add("")
$Txt.Add("5. WORTH REVIEW BUT LOCKED")
foreach ($r in $WorthReview) {
    $Txt.Add("$($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close) | $($r.full_buy_decision)")
}
$Txt.Add("")
$Txt.Add("6. FILES")
$Txt.Add("SUMMARY_MD: $SummaryMd")
$Txt.Add("PANEL_CSV: $PanelCsv")
$Txt.Add("WORTH_REVIEW_CSV: $WorthReviewCsv")
$Txt.Add("ACTIONABLE_CSV: $ActionableCsv")
$Txt.Add("READ_FIRST: $ReadFirst")
$Txt.Add("")
$Txt.Add("7. NEXT NORMAL COMMAND")
$Txt.Add('Set-Location "D:\us-tech-quant"')
$Txt.Add('powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_8B_raw105_full_decision_readable_panel.ps1"')

$Txt | Set-Content -Path $SummaryTxt -Encoding UTF8

$Rf = @()
$Rf += "=== V17.8B RAW105 FULL DECISION READABLE PANEL READY ==="
$Rf += "RAW105_DECISION_PANEL_STATUS: $PanelStatus"
$Rf += "FINAL_ACTION: $FinalAction"
$Rf += "RAW_UNIVERSE_DECISION_COUNT: $RawDecisionCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount"
$Rf += "RAW105_PRICE_OK_COUNT: $RawPriceOkCount"
$Rf += "RAW105_PRICE_FAIL_COUNT: $RawPriceFailCount"
$Rf += "ACTIONABLE_BUY_COUNT_TODAY: $ActionableCount"
$Rf += "WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount"
$Rf += "TODAY_SAFE: $TodaySafe"
$Rf += "OFFICIAL_ACTION: $OfficialAction"
$Rf += "BUDGET_ACTION: $BudgetAction"
$Rf += "BUY_PERMISSION: $BuyPermission"
$Rf += ""
$Rf += "ACTIONABLE BUY CANDIDATES:"
if ($ActionableCount -eq 0) {
    $Rf += "NONE"
} else {
    foreach ($r in $Actionable) {
        $Rf += "$($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close)"
    }
}
$Rf += ""
$Rf += "WORTH REVIEW BUT LOCKED:"
foreach ($r in $WorthReview) {
    $Rf += "$($r.ticker) | $($r.raw105_latest_price_date) | $($r.raw105_latest_close)"
}
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryTxt
$Rf += ""
$Rf += "MD REPORT:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "FULL PANEL CSV:"
$Rf += $PanelCsv
$Rf += ""
$Rf += "NEXT NORMAL COMMAND:"
$Rf += 'Set-Location "D:\us-tech-quant"'
$Rf += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\run_v17_8B_raw105_full_decision_readable_panel.ps1"'

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.8B RAW105 FULL DECISION READABLE PANEL READY ==="
Write-Host "RAW105_DECISION_PANEL_STATUS: $PanelStatus"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "RAW_UNIVERSE_DECISION_COUNT: $RawDecisionCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT_DYNAMIC: $MainComputeCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT_DYNAMIC: $SecondStageCount"
Write-Host "RAW105_PRICE_OK_COUNT: $RawPriceOkCount"
Write-Host "RAW105_PRICE_FAIL_COUNT: $RawPriceFailCount"
Write-Host "ACTIONABLE_BUY_COUNT_TODAY: $ActionableCount"
Write-Host "WORTH_REVIEW_BUT_LOCKED_COUNT: $WorthReviewCount"
Write-Host "TODAY_SAFE: $TodaySafe"
Write-Host "OFFICIAL_ACTION: $OfficialAction"
Write-Host "BUDGET_ACTION: $BudgetAction"
Write-Host "BUY_PERMISSION: $BuyPermission"

Write-Host ""
Write-Host "=== ACTIONABLE BUY CANDIDATES ==="
if ($ActionableCount -eq 0) {
    Write-Host "NONE"
} else {
    $Actionable |
        Select-Object ticker,raw105_latest_price_date,raw105_latest_close,full_buy_decision |
        Format-Table -AutoSize
}

Write-Host ""
Write-Host "=== WORTH REVIEW BUT LOCKED ==="
$WorthReview |
    Select-Object ticker,raw105_latest_price_date,raw105_latest_close,full_buy_decision |
    Format-Table -AutoSize

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
Write-Host "=== V17.8B RAW105 FULL DECISION READABLE PANEL DONE ==="
