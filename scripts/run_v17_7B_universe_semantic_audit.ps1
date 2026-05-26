$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7B-R1 UNIVERSE SEMANTIC AUDIT START ==="

$InCsv = Join-Path $Root "outputs\v17\raw_universe_audit\v17_7_raw_universe_full_screen_audit.csv"
$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
$OutCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv"
$SummaryMd = Join-Path $OutDir "V17_7B_UNIVERSE_SEMANTIC_AUDIT.md"
$ReadFirst = Join-Path $OutDir "V17_7B_READ_FIRST.txt"

if (-not (Test-Path $InCsv)) {
    throw "Missing V17.7 raw audit CSV: $InCsv"
}

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Rows = Import-Csv $InCsv

if (-not $Rows -or $Rows.Count -eq 0) {
    throw "V17.7 raw audit CSV is empty: $InCsv"
}

function To-Bool($v) {
    $s = [string]$v
    return ($s.Trim().ToLowerInvariant() -in @("true", "1", "yes", "y"))
}

$SemanticRows = foreach ($r in $Rows) {
    $inRaw = To-Bool $r.in_raw_universe
    $inClassified = To-Bool $r.in_screened_universe
    $inMainCompute = To-Bool $r.in_selected_for_execution
    $inSecond = To-Bool $r.in_second_stage
    $priceOk = ([string]$r.price_status).StartsWith("OK")

    $Layer = if ($inSecond) {
        "SECOND_STAGE_CANDIDATE"
    } elseif ($inMainCompute) {
        "MAIN_COMPUTE_UNIVERSE"
    } elseif ($inClassified) {
        "CLASSIFIED_ONLY_NOT_MAIN_COMPUTE"
    } else {
        "RAW_ONLY_NOT_CLASSIFIED"
    }

    $TradeMeaning = if ($inSecond) {
        "重点候选池；仍需事件风险、预算、人工复核和触发价确认"
    } elseif ($inMainCompute) {
        "进入主计算/执行前置层；但未进入重点候选池"
    } elseif ($inClassified) {
        "已被系统分类和价格审计；未进入主计算层"
    } else {
        "仅存在于原始池；未进入分类层"
    }

    [pscustomobject]@{
        ticker = $r.ticker
        semantic_layer = $Layer
        trade_meaning_cn = $TradeMeaning
        in_raw_universe = $inRaw
        in_classified_universe = $inClassified
        in_main_compute_universe = $inMainCompute
        in_second_stage_candidate = $inSecond
        raw_price_ok = $priceOk
        price_status = $r.price_status
        latest_price_date = $r.latest_price_date
        latest_close = $r.latest_close
        manual_review_decision = $r.manual_review_decision
        previous_full_pipeline_status = $r.full_pipeline_status
        special_tag = $r.special_tag
        inferred_exclusion_reason = $r.inferred_exclusion_reason
    }
}

$RawUniverseCount = ($SemanticRows | Where-Object { $_.in_raw_universe }).Count
$ClassifiedUniverseCount = ($SemanticRows | Where-Object { $_.in_classified_universe }).Count
$MainComputeUniverseCount = ($SemanticRows | Where-Object { $_.in_main_compute_universe }).Count
$SecondStageCandidateCount = ($SemanticRows | Where-Object { $_.in_second_stage_candidate }).Count
$RawPriceOkCount = ($SemanticRows | Where-Object { $_.raw_price_ok }).Count
$RawPriceFailCount = $RawUniverseCount - $RawPriceOkCount

$ClassifiedOnlyCount = ($SemanticRows | Where-Object { $_.semantic_layer -eq "CLASSIFIED_ONLY_NOT_MAIN_COMPUTE" }).Count
$MainComputeOnlyCount = ($SemanticRows | Where-Object { $_.semantic_layer -eq "MAIN_COMPUTE_UNIVERSE" }).Count
$SecondStageOnlyCount = ($SemanticRows | Where-Object { $_.semantic_layer -eq "SECOND_STAGE_CANDIDATE" }).Count
$RawOnlyCount = ($SemanticRows | Where-Object { $_.semantic_layer -eq "RAW_ONLY_NOT_CLASSIFIED" }).Count

$Status = if (
    $RawUniverseCount -eq 105 -and
    $ClassifiedUniverseCount -eq 105 -and
    $MainComputeUniverseCount -eq 66 -and
    $SecondStageCandidateCount -eq 10 -and
    $RawPriceOkCount -eq 105 -and
    $RawPriceFailCount -eq 0
) {
    "OK_EXPECTED_105_66_10"
} elseif (
    $RawUniverseCount -gt 0 -and
    $RawPriceFailCount -eq 0 -and
    $MainComputeUniverseCount -gt 0 -and
    $SecondStageCandidateCount -gt 0
) {
    "OK_DYNAMIC_COUNTS"
} else {
    "WARN_CHECK_COUNTS"
}

$SemanticRows |
    Sort-Object semantic_layer, ticker |
    Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8

$LayerCounts = $SemanticRows |
    Group-Object semantic_layer |
    Sort-Object Name |
    ForEach-Object {
        [pscustomobject]@{
            semantic_layer = $_.Name
            count = $_.Count
        }
    }

$NowText = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Md = New-Object System.Collections.Generic.List[string]

$Md.Add("# V17.7B-R1 Universe Semantic Audit")
$Md.Add("")
$Md.Add("Generated: $NowText")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("UNIVERSE_SEMANTIC_STATUS: $Status")
$Md.Add("")
$Md.Add("本层不改变交易策略，只修正 universe 数量口径，防止把 66 误读成原始池数量。")
$Md.Add("")
$Md.Add("当前正确口径：")
$Md.Add("")
$Md.Add("RAW_UNIVERSE_COUNT: $RawUniverseCount")
$Md.Add("CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount")
$Md.Add("MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount")
$Md.Add("SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount")
$Md.Add("RAW_PRICE_OK_COUNT: $RawPriceOkCount")
$Md.Add("RAW_PRICE_FAIL_COUNT: $RawPriceFailCount")
$Md.Add("")
$Md.Add("## 2. Count Summary")
$Md.Add("")
$Md.Add("| item | count | meaning |")
$Md.Add("|---|---:|---|")
$Md.Add("| RAW_UNIVERSE_COUNT | $RawUniverseCount | 原始股票池总数 |")
$Md.Add("| CLASSIFIED_UNIVERSE_COUNT | $ClassifiedUniverseCount | 已进入分类/审计文件的数量 |")
$Md.Add("| MAIN_COMPUTE_UNIVERSE_COUNT | $MainComputeUniverseCount | 进入主计算/执行前置层的数量；这就是之前看到的 66 |")
$Md.Add("| SECOND_STAGE_CANDIDATE_COUNT | $SecondStageCandidateCount | 重点候选池数量 |")
$Md.Add("| CLASSIFIED_ONLY_NOT_MAIN_COMPUTE_COUNT | $ClassifiedOnlyCount | 已分类但未进入主计算层 |")
$Md.Add("| MAIN_COMPUTE_NOT_SECOND_STAGE_COUNT | $MainComputeOnlyCount | 进入主计算但未进入 second stage |")
$Md.Add("| SECOND_STAGE_COUNT | $SecondStageOnlyCount | second stage 候选 |")
$Md.Add("| RAW_ONLY_NOT_CLASSIFIED_COUNT | $RawOnlyCount | 原始池中未分类数量 |")
$Md.Add("| RAW_PRICE_OK_COUNT | $RawPriceOkCount | 原始池中价格可用数量 |")
$Md.Add("| RAW_PRICE_FAIL_COUNT | $RawPriceFailCount | 原始池中价格失败数量 |")
$Md.Add("")
$Md.Add("## 3. Semantic Layer Counts")
$Md.Add("")
$Md.Add("| semantic_layer | count |")
$Md.Add("|---|---:|")

foreach ($x in $LayerCounts) {
    $Md.Add("| $($x.semantic_layer) | $($x.count) |")
}

$Md.Add("")
$Md.Add("## 4. Correct Interpretation")
$Md.Add("")
$Md.Add("以后不要说：只有 66 个股票参与系统。")
$Md.Add("")
$Md.Add("更准确的说法是：原始池 105 个全部参与价格审计和分类；其中 66 个进入主计算/执行前置层；10 个进入 second stage 重点候选层。")
$Md.Add("")
$Md.Add("## 5. Output Files")
$Md.Add("")
$Md.Add("- Semantic audit CSV: $OutCsv")
$Md.Add("- Summary: $SummaryMd")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7B-R1 UNIVERSE SEMANTIC AUDIT READY ==="
$Rf += "UNIVERSE_SEMANTIC_STATUS: $Status"
$Rf += "RAW_UNIVERSE_COUNT: $RawUniverseCount"
$Rf += "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
$Rf += "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
$Rf += "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
$Rf += "RAW_PRICE_OK_COUNT: $RawPriceOkCount"
$Rf += "RAW_PRICE_FAIL_COUNT: $RawPriceFailCount"
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "FULL CSV:"
$Rf += $OutCsv

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7B-R1 UNIVERSE SEMANTIC AUDIT READY ==="
Write-Host "UNIVERSE_SEMANTIC_STATUS: $Status"
Write-Host "RAW_UNIVERSE_COUNT: $RawUniverseCount"
Write-Host "CLASSIFIED_UNIVERSE_COUNT: $ClassifiedUniverseCount"
Write-Host "MAIN_COMPUTE_UNIVERSE_COUNT: $MainComputeUniverseCount"
Write-Host "SECOND_STAGE_CANDIDATE_COUNT: $SecondStageCandidateCount"
Write-Host "RAW_PRICE_OK_COUNT: $RawPriceOkCount"
Write-Host "RAW_PRICE_FAIL_COUNT: $RawPriceFailCount"
Write-Host ""
Write-Host "START HERE:"
Write-Host $SummaryMd
Write-Host ""
Write-Host "FULL CSV:"
Write-Host $OutCsv
Write-Host ""
Write-Host "READ FIRST:"
Write-Host $ReadFirst

Write-Host ""
Write-Host "=== V17.7B-R1 UNIVERSE SEMANTIC AUDIT DONE ==="
