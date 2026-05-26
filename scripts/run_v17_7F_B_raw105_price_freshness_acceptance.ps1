$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7F-B RAW105 PRICE FRESHNESS ACCEPTANCE START ==="

$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$RefreshCsv = Join-Path $OutDir "v17_7F_raw105_latest_price_refresh.csv"
$SemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv"
$InspectionCsv = Join-Path $OutDir "v17_7E_removed_main_compute_inspection.csv"

$OutCsv = Join-Path $OutDir "v17_7F_B_price_freshness_acceptance.csv"
$SummaryMd = Join-Path $OutDir "V17_7F_B_PRICE_FRESHNESS_ACCEPTANCE.md"
$ReadFirst = Join-Path $OutDir "V17_7F_B_READ_FIRST.txt"

if (-not (Test-Path $RefreshCsv)) {
    throw "Missing V17.7F refresh CSV: $RefreshCsv"
}
if (-not (Test-Path $SemanticCsv)) {
    throw "Missing V17.7B semantic CSV: $SemanticCsv"
}

$Refresh = Import-Csv $RefreshCsv
$Semantic = Import-Csv $SemanticCsv

$MaxDate = (
    $Refresh |
        Where-Object { $_.refresh_status -like "OK*" } |
        Sort-Object latest_price_date -Descending |
        Select-Object -First 1
).latest_price_date

$Rows = New-Object System.Collections.Generic.List[object]

foreach ($r in $Refresh) {
    $t = ([string]$r.ticker).Trim().ToUpperInvariant()
    $s = $Semantic | Where-Object { ([string]$_.ticker).Trim().ToUpperInvariant() -eq $t } | Select-Object -First 1

    $isOk = ([string]$r.refresh_status).StartsWith("OK")
    $isMaxDate = ([string]$r.latest_price_date -eq [string]$MaxDate)

    $inMain = $false
    $inSecond = $false
    $layer = ""

    if ($s) {
        $inMain = ([string]$s.in_main_compute_universe).Trim().ToLowerInvariant() -eq "true"
        $inSecond = ([string]$s.in_second_stage_candidate).Trim().ToLowerInvariant() -eq "true"
        $layer = $s.semantic_layer
    }

    $acceptance = if (-not $isOk) {
        "REJECT_PRICE_REFRESH_FAILED"
    } elseif ($isMaxDate) {
        "ACCEPT_LATEST_DATE"
    } elseif ((-not $inMain) -and (-not $inSecond)) {
        "ACCEPT_NON_MAX_DATE_NOT_IN_MAIN_OR_SECOND_STAGE"
    } elseif ($inSecond) {
        "REVIEW_NON_MAX_DATE_IN_SECOND_STAGE"
    } elseif ($inMain) {
        "REVIEW_NON_MAX_DATE_IN_MAIN_COMPUTE"
    } else {
        "REVIEW_NON_MAX_DATE_UNKNOWN_LAYER"
    }

    $Rows.Add([pscustomobject]@{
        ticker = $t
        refresh_status = $r.refresh_status
        latest_price_date = $r.latest_price_date
        latest_close = $r.latest_close
        latest_volume = $r.latest_volume
        freshness_status = $r.freshness_status
        max_latest_price_date = $MaxDate
        semantic_layer = $layer
        in_main_compute_universe = $inMain
        in_second_stage_candidate = $inSecond
        acceptance_status = $acceptance
    })
}

$Rows | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8

$TotalCount = $Rows.Count
$OkCount = @($Rows | Where-Object { $_.refresh_status -like "OK*" }).Count
$FailCount = $TotalCount - $OkCount
$LatestDateCount = @($Rows | Where-Object { $_.acceptance_status -eq "ACCEPT_LATEST_DATE" }).Count
$NonMaxAcceptCount = @($Rows | Where-Object { $_.acceptance_status -eq "ACCEPT_NON_MAX_DATE_NOT_IN_MAIN_OR_SECOND_STAGE" }).Count
$ReviewCount = @($Rows | Where-Object { $_.acceptance_status -like "REVIEW*" }).Count
$RejectCount = @($Rows | Where-Object { $_.acceptance_status -like "REJECT*" }).Count

$NonMaxRows = @(
    $Rows |
        Where-Object { $_.acceptance_status -ne "ACCEPT_LATEST_DATE" } |
        Sort-Object ticker
)

$Status = if (
    $TotalCount -eq 105 -and
    $OkCount -eq 105 -and
    $FailCount -eq 0 -and
    $NonMaxAcceptCount -eq 1 -and
    $ReviewCount -eq 0 -and
    $RejectCount -eq 0
) {
    "OK_ACCEPT_1_NON_MAX_NOT_IN_MAIN_OR_SECOND_STAGE"
} elseif (
    $TotalCount -eq 105 -and
    $OkCount -eq 105 -and
    $ReviewCount -eq 0 -and
    $RejectCount -eq 0
) {
    "OK_ACCEPT_DYNAMIC_NON_MAX"
} else {
    "WARN_REVIEW_OR_REJECT_PRESENT"
}

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.7F-B RAW105 Price Freshness Acceptance")
$Md.Add("")
$Md.Add("Generated: $Now")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("PRICE_FRESHNESS_ACCEPTANCE_STATUS: $Status")
$Md.Add("")
$Md.Add("本报告判断 V17.7F 中唯一 non-max-date ticker 是否影响正式 daily 操作建议。")
$Md.Add("")
$Md.Add("## 2. Count Summary")
$Md.Add("")
$Md.Add("| item | value |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_TICKER_COUNT | $TotalCount |")
$Md.Add("| PRICE_REFRESH_OK_COUNT | $OkCount |")
$Md.Add("| PRICE_REFRESH_FAIL_COUNT | $FailCount |")
$Md.Add("| MAX_LATEST_PRICE_DATE | $MaxDate |")
$Md.Add("| LATEST_DATE_ACCEPT_COUNT | $LatestDateCount |")
$Md.Add("| NON_MAX_ACCEPT_COUNT | $NonMaxAcceptCount |")
$Md.Add("| REVIEW_COUNT | $ReviewCount |")
$Md.Add("| REJECT_COUNT | $RejectCount |")
$Md.Add("")
$Md.Add("## 3. Non Max / Review Rows")
$Md.Add("")
$Md.Add("| ticker | latest_price_date | latest_close | latest_volume | semantic_layer | in_main_compute | in_second_stage | acceptance_status |")
$Md.Add("|---|---:|---:|---:|---|---|---|---|")

foreach ($r in $NonMaxRows) {
    $Md.Add("| $($r.ticker) | $($r.latest_price_date) | $($r.latest_close) | $($r.latest_volume) | $($r.semantic_layer) | $($r.in_main_compute_universe) | $($r.in_second_stage_candidate) | $($r.acceptance_status) |")
}

$Md.Add("")
$Md.Add("## 4. Interpretation")
$Md.Add("")
$Md.Add("PSTG 的 latest_price_date 为 2026-05-11，低于全池最大日期 2026-05-12。")
$Md.Add("")
$Md.Add("但 PSTG 当前不在 main compute 56，也不在 second stage 10，因此不会污染今日主计算候选或操作建议。")
$Md.Add("")
$Md.Add("只要 PRICE_FRESHNESS_ACCEPTANCE_STATUS 为 OK_ACCEPT_1_NON_MAX_NOT_IN_MAIN_OR_SECOND_STAGE，就允许继续推进 wrapper 语义修正。")
$Md.Add("")
$Md.Add("## 5. Output Files")
$Md.Add("")
$Md.Add("- Acceptance CSV: $OutCsv")
$Md.Add("- Summary: $SummaryMd")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7F-B RAW105 PRICE FRESHNESS ACCEPTANCE READY ==="
$Rf += "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $Status"
$Rf += "RAW_TICKER_COUNT: $TotalCount"
$Rf += "PRICE_REFRESH_OK_COUNT: $OkCount"
$Rf += "PRICE_REFRESH_FAIL_COUNT: $FailCount"
$Rf += "MAX_LATEST_PRICE_DATE: $MaxDate"
$Rf += "LATEST_DATE_ACCEPT_COUNT: $LatestDateCount"
$Rf += "NON_MAX_ACCEPT_COUNT: $NonMaxAcceptCount"
$Rf += "REVIEW_COUNT: $ReviewCount"
$Rf += "REJECT_COUNT: $RejectCount"
$Rf += ""
$Rf += "NON MAX / REVIEW ROWS:"
foreach ($r in $NonMaxRows) {
    $Rf += "$($r.ticker) | $($r.latest_price_date) | $($r.latest_close) | $($r.semantic_layer) | in_main=$($r.in_main_compute_universe) | in_second=$($r.in_second_stage_candidate) | $($r.acceptance_status)"
}
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "FULL CSV:"
$Rf += $OutCsv

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7F-B RAW105 PRICE FRESHNESS ACCEPTANCE READY ==="
Write-Host "PRICE_FRESHNESS_ACCEPTANCE_STATUS: $Status"
Write-Host "RAW_TICKER_COUNT: $TotalCount"
Write-Host "PRICE_REFRESH_OK_COUNT: $OkCount"
Write-Host "PRICE_REFRESH_FAIL_COUNT: $FailCount"
Write-Host "MAX_LATEST_PRICE_DATE: $MaxDate"
Write-Host "LATEST_DATE_ACCEPT_COUNT: $LatestDateCount"
Write-Host "NON_MAX_ACCEPT_COUNT: $NonMaxAcceptCount"
Write-Host "REVIEW_COUNT: $ReviewCount"
Write-Host "REJECT_COUNT: $RejectCount"
Write-Host ""
Write-Host "=== NON MAX / REVIEW ROWS ==="
$NonMaxRows |
    Select-Object ticker,latest_price_date,latest_close,latest_volume,semantic_layer,in_main_compute_universe,in_second_stage_candidate,acceptance_status |
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
Write-Host "=== V17.7F-B RAW105 PRICE FRESHNESS ACCEPTANCE DONE ==="
