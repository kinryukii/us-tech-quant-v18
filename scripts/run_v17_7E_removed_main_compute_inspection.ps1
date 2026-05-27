$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7E REMOVED MAIN COMPUTE INSPECTION START ==="

$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$DeltaCsv = Join-Path $OutDir "v17_7D_main_compute_delta_audit.csv"
$SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv"

$OutCsv = Join-Path $OutDir "v17_7E_removed_main_compute_inspection.csv"
$SummaryMd = Join-Path $OutDir "V17_7E_REMOVED_MAIN_COMPUTE_INSPECTION.md"
$ReadFirst = Join-Path $OutDir "V17_7E_READ_FIRST.txt"

if (-not (Test-Path $DeltaCsv)) {
    throw "Missing V17.7D delta CSV: $DeltaCsv"
}

if (-not (Test-Path $SemanticCsv)) {
    throw "Missing V17.7B semantic CSV: $SemanticCsv"
}

$Delta = Import-Csv $DeltaCsv
$Semantic = Import-Csv $SemanticCsv

$Removed = @(
    $Delta |
        Where-Object {
            $_.comparison_layer -eq "MAIN_COMPUTE" -and
            $_.delta_status -eq "REMOVED_FROM_MAIN_COMPUTE"
        } |
        Sort-Object ticker
)

$Added = @(
    $Delta |
        Where-Object {
            $_.comparison_layer -eq "MAIN_COMPUTE" -and
            $_.delta_status -eq "ADDED_TO_MAIN_COMPUTE"
        } |
        Sort-Object ticker
)

$Rows = New-Object System.Collections.Generic.List[object]

foreach ($r in $Removed) {
    $t = ([string]$r.ticker).Trim().ToUpperInvariant()
    $s = $Semantic | Where-Object { ([string]$_.ticker).Trim().ToUpperInvariant() -eq $t } | Select-Object -First 1

    $priceOk = ([string]$r.current_price_status).StartsWith("OK")

    $interpretation = if ($s -and $s.in_raw_universe -eq "True" -and $s.in_classified_universe -eq "True" -and $priceOk -and $s.in_main_compute_universe -eq "False") {
        "仍在 RAW 105 和 classified 105 中，价格 OK；只是当前未进入 main compute 56"
    } elseif ($priceOk) {
        "价格 OK，但当前层级需要人工复核"
    } else {
        "价格或分类状态异常，需要检查"
    }

    $Rows.Add([pscustomobject]@{
        ticker = $t
        delta_status = $r.delta_status
        current_semantic_layer = $r.current_semantic_layer
        in_raw_universe = if ($s) { $s.in_raw_universe } else { "" }
        in_classified_universe = if ($s) { $s.in_classified_universe } else { "" }
        in_main_compute_universe = if ($s) { $s.in_main_compute_universe } else { "" }
        in_second_stage_candidate = if ($s) { $s.in_second_stage_candidate } else { "" }
        current_price_status = $r.current_price_status
        current_latest_price_date = $r.current_latest_price_date
        current_latest_close = $r.current_latest_close
        current_manual_review_decision = $r.current_manual_review_decision
        current_special_tag = $r.current_special_tag
        current_inferred_exclusion_reason = $r.current_inferred_exclusion_reason
        interpretation_cn = $interpretation
    })
}

$Rows | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8

$RemovedCount = $Removed.Count
$AddedCount = $Added.Count
$RemovedPriceOkCount = @($Rows | Where-Object { ([string]$_.current_price_status).StartsWith("OK") }).Count
$RemovedStillRawCount = @($Rows | Where-Object { $_.in_raw_universe -eq "True" }).Count
$RemovedStillClassifiedCount = @($Rows | Where-Object { $_.in_classified_universe -eq "True" }).Count
$RemovedStillSecondStageCount = @($Rows | Where-Object { $_.in_second_stage_candidate -eq "True" }).Count

$Status = if (
    $RemovedCount -eq 10 -and
    $AddedCount -eq 0 -and
    $RemovedPriceOkCount -eq 10 -and
    $RemovedStillRawCount -eq 10 -and
    $RemovedStillClassifiedCount -eq 10
) {
    "OK_REMOVED_10_STILL_RAW_CLASSIFIED_PRICE_OK"
} elseif (
    $RemovedCount -gt 0 -and
    $RemovedPriceOkCount -eq $RemovedCount
) {
    "OK_REMOVED_DYNAMIC_PRICE_OK"
} else {
    "WARN_CHECK_REMOVED_NAMES"
}

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.7E Removed Main Compute Inspection")
$Md.Add("")
$Md.Add("Generated: $Now")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("REMOVED_INSPECTION_STATUS: $Status")
$Md.Add("")
$Md.Add("本报告检查从旧 stable 主计算层 66 中被移出、当前不在 main compute 56 里的标的。")
$Md.Add("")
$Md.Add("## 2. Count Summary")
$Md.Add("")
$Md.Add("| item | count |")
$Md.Add("|---|---:|")
$Md.Add("| MAIN_COMPUTE_REMOVED_COUNT | $RemovedCount |")
$Md.Add("| MAIN_COMPUTE_ADDED_COUNT | $AddedCount |")
$Md.Add("| REMOVED_PRICE_OK_COUNT | $RemovedPriceOkCount |")
$Md.Add("| REMOVED_STILL_RAW_COUNT | $RemovedStillRawCount |")
$Md.Add("| REMOVED_STILL_CLASSIFIED_COUNT | $RemovedStillClassifiedCount |")
$Md.Add("| REMOVED_STILL_SECOND_STAGE_COUNT | $RemovedStillSecondStageCount |")
$Md.Add("")
$Md.Add("## 3. Removed Tickers")
$Md.Add("")
$Md.Add("| ticker | current_semantic_layer | price_status | latest_price_date | latest_close | interpretation |")
$Md.Add("|---|---|---|---:|---:|---|")

foreach ($r in $Rows) {
    $Md.Add("| $($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close) | $($r.interpretation_cn) |")
}

$Md.Add("")
$Md.Add("## 4. Interpretation")
$Md.Add("")
$Md.Add("如果 REMOVED_PRICE_OK_COUNT 等于 MAIN_COMPUTE_REMOVED_COUNT，说明这 10 个不是因为价格失败被移出。")
$Md.Add("")
$Md.Add("如果 REMOVED_STILL_RAW_COUNT 和 REMOVED_STILL_CLASSIFIED_COUNT 都等于 10，说明它们仍在 105 原始池和 105 分类池中，只是没有进入当前 main compute 56。")
$Md.Add("")
$Md.Add("## 5. Output Files")
$Md.Add("")
$Md.Add("- Inspection CSV: $OutCsv")
$Md.Add("- Summary: $SummaryMd")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7E REMOVED MAIN COMPUTE INSPECTION READY ==="
$Rf += "REMOVED_INSPECTION_STATUS: $Status"
$Rf += "MAIN_COMPUTE_REMOVED_COUNT: $RemovedCount"
$Rf += "MAIN_COMPUTE_ADDED_COUNT: $AddedCount"
$Rf += "REMOVED_PRICE_OK_COUNT: $RemovedPriceOkCount"
$Rf += "REMOVED_STILL_RAW_COUNT: $RemovedStillRawCount"
$Rf += "REMOVED_STILL_CLASSIFIED_COUNT: $RemovedStillClassifiedCount"
$Rf += "REMOVED_STILL_SECOND_STAGE_COUNT: $RemovedStillSecondStageCount"
$Rf += ""
$Rf += "REMOVED TICKERS:"
foreach ($r in $Rows) {
    $Rf += "$($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close)"
}
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "FULL CSV:"
$Rf += $OutCsv

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7E REMOVED MAIN COMPUTE INSPECTION READY ==="
Write-Host "REMOVED_INSPECTION_STATUS: $Status"
Write-Host "MAIN_COMPUTE_REMOVED_COUNT: $RemovedCount"
Write-Host "MAIN_COMPUTE_ADDED_COUNT: $AddedCount"
Write-Host "REMOVED_PRICE_OK_COUNT: $RemovedPriceOkCount"
Write-Host "REMOVED_STILL_RAW_COUNT: $RemovedStillRawCount"
Write-Host "REMOVED_STILL_CLASSIFIED_COUNT: $RemovedStillClassifiedCount"
Write-Host "REMOVED_STILL_SECOND_STAGE_COUNT: $RemovedStillSecondStageCount"
Write-Host ""
Write-Host "=== REMOVED TICKERS ==="
$Rows |
    Select-Object ticker,current_semantic_layer,current_price_status,current_latest_price_date,current_latest_close |
    Format-Table -AutoSize

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
Write-Host "=== V17.7E REMOVED MAIN COMPUTE INSPECTION DONE ==="
