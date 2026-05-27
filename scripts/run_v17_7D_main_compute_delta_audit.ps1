$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== V17.7D MAIN COMPUTE DELTA AUDIT START ==="

$OutDir = Join-Path $Root "outputs\v17\raw_universe_audit"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$CurrentSemanticCsv = Join-Path $OutDir "v17_7B_universe_semantic_audit.csv"
$CurrentSecondStageCsv = Join-Path $Root "outputs\v17\price\v17_6E_second_stage_tickers.csv"
$CurrentMainCsv = Join-Path $Root "outputs\v17\price\v17_6E_screened_universe_tickers.csv"

$StableRoot = Join-Path $Root "archive\stable\V17_6H_R2_stable_repair_health_compat_manual_daily_20260512_214624"
$StableSelectedCsv = Join-Path $StableRoot "outputs\v16\universe\V16_FULL_UNIVERSE_SELECTED_FOR_EXECUTION.csv"
$StableSecondStageCsv = Join-Path $StableRoot "outputs\v17\price\v17_6E_second_stage_tickers.csv"

$OutCsv = Join-Path $OutDir "v17_7D_main_compute_delta_audit.csv"
$SummaryMd = Join-Path $OutDir "V17_7D_MAIN_COMPUTE_DELTA_AUDIT.md"
$ReadFirst = Join-Path $OutDir "V17_7D_READ_FIRST.txt"

function Get-TickerColumn {
    param($Rows)

    if (-not $Rows -or $Rows.Count -eq 0) {
        return $null
    }

    $Props = $Rows[0].PSObject.Properties.Name

    foreach ($c in @("ticker", "Ticker", "symbol", "Symbol")) {
        if ($Props -contains $c) {
            return $c
        }
    }

    foreach ($p in $Props) {
        if ($p.ToLowerInvariant().Contains("ticker") -or $p.ToLowerInvariant().Contains("symbol")) {
            return $p
        }
    }

    return $Props[0]
}

function Read-TickerSet {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return [pscustomobject]@{
            path = $Path
            exists = $false
            tickers = @()
        }
    }

    $rows = Import-Csv $Path

    if (-not $rows -or $rows.Count -eq 0) {
        return [pscustomobject]@{
            path = $Path
            exists = $true
            tickers = @()
        }
    }

    $col = Get-TickerColumn $rows

    $tickers = @(
        $rows |
            ForEach-Object {
                ([string]$_.$col).Trim().ToUpperInvariant()
            } |
            Where-Object { $_ -and $_ -ne "NAN" } |
            Sort-Object -Unique
    )

    return [pscustomobject]@{
        path = $Path
        exists = $true
        tickers = $tickers
    }
}

if (-not (Test-Path $CurrentSemanticCsv)) {
    throw "Missing current semantic audit CSV. Run V17.7B first: $CurrentSemanticCsv"
}

$CurrentSemantic = Import-Csv $CurrentSemanticCsv

$CurrentMainFromSemantic = @(
    $CurrentSemantic |
        Where-Object { $_.in_main_compute_universe -eq "True" -or $_.in_main_compute_universe -eq "true" } |
        ForEach-Object { ([string]$_.ticker).Trim().ToUpperInvariant() } |
        Where-Object { $_ } |
        Sort-Object -Unique
)

$CurrentSecondFromSemantic = @(
    $CurrentSemantic |
        Where-Object { $_.in_second_stage_candidate -eq "True" -or $_.in_second_stage_candidate -eq "true" } |
        ForEach-Object { ([string]$_.ticker).Trim().ToUpperInvariant() } |
        Where-Object { $_ } |
        Sort-Object -Unique
)

$StableSelected = Read-TickerSet $StableSelectedCsv
$StableSecond = Read-TickerSet $StableSecondStageCsv
$CurrentMainFile = Read-TickerSet $CurrentMainCsv
$CurrentSecondFile = Read-TickerSet $CurrentSecondStageCsv

$OldMain = @($StableSelected.tickers)
$NewMain = @($CurrentMainFromSemantic)

$OldSecond = @($StableSecond.tickers)
$NewSecond = @($CurrentSecondFromSemantic)

$AllMainTickers = @($OldMain + $NewMain | Sort-Object -Unique)
$AllSecondTickers = @($OldSecond + $NewSecond | Sort-Object -Unique)

$Rows = New-Object System.Collections.Generic.List[object]

foreach ($t in $AllMainTickers) {
    $oldIn = $OldMain -contains $t
    $newIn = $NewMain -contains $t

    $delta = if ($oldIn -and $newIn) {
        "UNCHANGED_IN_MAIN_COMPUTE"
    } elseif ($oldIn -and -not $newIn) {
        "REMOVED_FROM_MAIN_COMPUTE"
    } elseif (-not $oldIn -and $newIn) {
        "ADDED_TO_MAIN_COMPUTE"
    } else {
        "UNKNOWN"
    }

    $semanticRow = $CurrentSemantic | Where-Object { ([string]$_.ticker).Trim().ToUpperInvariant() -eq $t } | Select-Object -First 1

    $Rows.Add([pscustomobject]@{
        ticker = $t
        comparison_layer = "MAIN_COMPUTE"
        old_in_stable = $oldIn
        current_in_latest = $newIn
        delta_status = $delta
        current_semantic_layer = if ($semanticRow) { $semanticRow.semantic_layer } else { "" }
        current_price_status = if ($semanticRow) { $semanticRow.price_status } else { "" }
        current_latest_price_date = if ($semanticRow) { $semanticRow.latest_price_date } else { "" }
        current_latest_close = if ($semanticRow) { $semanticRow.latest_close } else { "" }
        current_manual_review_decision = if ($semanticRow) { $semanticRow.manual_review_decision } else { "" }
        current_special_tag = if ($semanticRow) { $semanticRow.special_tag } else { "" }
        current_inferred_exclusion_reason = if ($semanticRow) { $semanticRow.inferred_exclusion_reason } else { "" }
    })
}

foreach ($t in $AllSecondTickers) {
    $oldIn = $OldSecond -contains $t
    $newIn = $NewSecond -contains $t

    $delta = if ($oldIn -and $newIn) {
        "UNCHANGED_IN_SECOND_STAGE"
    } elseif ($oldIn -and -not $newIn) {
        "REMOVED_FROM_SECOND_STAGE"
    } elseif (-not $oldIn -and $newIn) {
        "ADDED_TO_SECOND_STAGE"
    } else {
        "UNKNOWN"
    }

    $semanticRow = $CurrentSemantic | Where-Object { ([string]$_.ticker).Trim().ToUpperInvariant() -eq $t } | Select-Object -First 1

    $Rows.Add([pscustomobject]@{
        ticker = $t
        comparison_layer = "SECOND_STAGE"
        old_in_stable = $oldIn
        current_in_latest = $newIn
        delta_status = $delta
        current_semantic_layer = if ($semanticRow) { $semanticRow.semantic_layer } else { "" }
        current_price_status = if ($semanticRow) { $semanticRow.price_status } else { "" }
        current_latest_price_date = if ($semanticRow) { $semanticRow.latest_price_date } else { "" }
        current_latest_close = if ($semanticRow) { $semanticRow.latest_close } else { "" }
        current_manual_review_decision = if ($semanticRow) { $semanticRow.manual_review_decision } else { "" }
        current_special_tag = if ($semanticRow) { $semanticRow.special_tag } else { "" }
        current_inferred_exclusion_reason = if ($semanticRow) { $semanticRow.inferred_exclusion_reason } else { "" }
    })
}

$Rows | Export-Csv -Path $OutCsv -NoTypeInformation -Encoding UTF8

$OldMainCount = $OldMain.Count
$NewMainCount = $NewMain.Count
$MainRemoved = @($Rows | Where-Object { $_.comparison_layer -eq "MAIN_COMPUTE" -and $_.delta_status -eq "REMOVED_FROM_MAIN_COMPUTE" })
$MainAdded = @($Rows | Where-Object { $_.comparison_layer -eq "MAIN_COMPUTE" -and $_.delta_status -eq "ADDED_TO_MAIN_COMPUTE" })

$OldSecondCount = $OldSecond.Count
$NewSecondCount = $NewSecond.Count
$SecondRemoved = @($Rows | Where-Object { $_.comparison_layer -eq "SECOND_STAGE" -and $_.delta_status -eq "REMOVED_FROM_SECOND_STAGE" })
$SecondAdded = @($Rows | Where-Object { $_.comparison_layer -eq "SECOND_STAGE" -and $_.delta_status -eq "ADDED_TO_SECOND_STAGE" })

$RawCount = ($CurrentSemantic | Where-Object { $_.in_raw_universe -eq "True" -or $_.in_raw_universe -eq "true" }).Count
$ClassifiedCount = ($CurrentSemantic | Where-Object { $_.in_classified_universe -eq "True" -or $_.in_classified_universe -eq "true" }).Count
$PriceOkCount = ($CurrentSemantic | Where-Object { ([string]$_.price_status).StartsWith("OK") }).Count
$PriceFailCount = $RawCount - $PriceOkCount

$AuditStatus = if ($RawCount -eq 105 -and $ClassifiedCount -eq 105 -and $PriceOkCount -eq 105 -and $PriceFailCount -eq 0 -and $NewMainCount -eq 56 -and $NewSecondCount -eq 10) {
    "OK_CURRENT_105_56_10"
} elseif ($RawCount -eq 105 -and $ClassifiedCount -eq 105 -and $PriceFailCount -eq 0) {
    "OK_RAW_PRICE_WITH_DYNAMIC_MAIN_COUNT"
} else {
    "WARN_CHECK_UNIVERSE_DELTA"
}

$Now = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$Md = New-Object System.Collections.Generic.List[string]
$Md.Add("# V17.7D Main Compute Delta Audit")
$Md.Add("")
$Md.Add("Generated: $Now")
$Md.Add("")
$Md.Add("## 1. Main Conclusion")
$Md.Add("")
$Md.Add("DELTA_AUDIT_STATUS: $AuditStatus")
$Md.Add("")
$Md.Add("本报告比较 V17.6H-R2 稳定快照里的主计算层，与当前最新 V17.7B 语义审计里的主计算层。")
$Md.Add("")
$Md.Add("## 2. Count Summary")
$Md.Add("")
$Md.Add("| item | count |")
$Md.Add("|---|---:|")
$Md.Add("| RAW_UNIVERSE_COUNT_CURRENT | $RawCount |")
$Md.Add("| CLASSIFIED_UNIVERSE_COUNT_CURRENT | $ClassifiedCount |")
$Md.Add("| RAW_PRICE_OK_COUNT_CURRENT | $PriceOkCount |")
$Md.Add("| RAW_PRICE_FAIL_COUNT_CURRENT | $PriceFailCount |")
$Md.Add("| OLD_MAIN_COMPUTE_COUNT_STABLE | $OldMainCount |")
$Md.Add("| CURRENT_MAIN_COMPUTE_COUNT | $NewMainCount |")
$Md.Add("| MAIN_COMPUTE_REMOVED_COUNT | $($MainRemoved.Count) |")
$Md.Add("| MAIN_COMPUTE_ADDED_COUNT | $($MainAdded.Count) |")
$Md.Add("| OLD_SECOND_STAGE_COUNT_STABLE | $OldSecondCount |")
$Md.Add("| CURRENT_SECOND_STAGE_COUNT | $NewSecondCount |")
$Md.Add("| SECOND_STAGE_REMOVED_COUNT | $($SecondRemoved.Count) |")
$Md.Add("| SECOND_STAGE_ADDED_COUNT | $($SecondAdded.Count) |")
$Md.Add("")
$Md.Add("## 3. Removed From Main Compute")
$Md.Add("")
$Md.Add("| ticker | current_semantic_layer | price_status | latest_price_date | latest_close |")
$Md.Add("|---|---|---|---:|---:|")
foreach ($r in $MainRemoved) {
    $Md.Add("| $($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close) |")
}
$Md.Add("")
$Md.Add("## 4. Added To Main Compute")
$Md.Add("")
$Md.Add("| ticker | current_semantic_layer | price_status | latest_price_date | latest_close |")
$Md.Add("|---|---|---|---:|---:|")
foreach ($r in $MainAdded) {
    $Md.Add("| $($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close) |")
}
$Md.Add("")
$Md.Add("## 5. Second Stage Changes")
$Md.Add("")
$Md.Add("### Removed From Second Stage")
$Md.Add("")
$Md.Add("| ticker | current_semantic_layer | price_status | latest_price_date | latest_close |")
$Md.Add("|---|---|---|---:|---:|")
foreach ($r in $SecondRemoved) {
    $Md.Add("| $($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close) |")
}
$Md.Add("")
$Md.Add("### Added To Second Stage")
$Md.Add("")
$Md.Add("| ticker | current_semantic_layer | price_status | latest_price_date | latest_close |")
$Md.Add("|---|---|---|---:|---:|")
foreach ($r in $SecondAdded) {
    $Md.Add("| $($r.ticker) | $($r.current_semantic_layer) | $($r.current_price_status) | $($r.current_latest_price_date) | $($r.current_latest_close) |")
}
$Md.Add("")
$Md.Add("## 6. Output Files")
$Md.Add("")
$Md.Add("- Delta CSV: $OutCsv")
$Md.Add("- Summary: $SummaryMd")
$Md.Add("- Read first: $ReadFirst")
$Md.Add("")

$Md | Set-Content -Path $SummaryMd -Encoding UTF8

$Rf = @()
$Rf += "=== V17.7D MAIN COMPUTE DELTA AUDIT READY ==="
$Rf += "DELTA_AUDIT_STATUS: $AuditStatus"
$Rf += "RAW_UNIVERSE_COUNT_CURRENT: $RawCount"
$Rf += "CLASSIFIED_UNIVERSE_COUNT_CURRENT: $ClassifiedCount"
$Rf += "RAW_PRICE_OK_COUNT_CURRENT: $PriceOkCount"
$Rf += "RAW_PRICE_FAIL_COUNT_CURRENT: $PriceFailCount"
$Rf += "OLD_MAIN_COMPUTE_COUNT_STABLE: $OldMainCount"
$Rf += "CURRENT_MAIN_COMPUTE_COUNT: $NewMainCount"
$Rf += "MAIN_COMPUTE_REMOVED_COUNT: $($MainRemoved.Count)"
$Rf += "MAIN_COMPUTE_ADDED_COUNT: $($MainAdded.Count)"
$Rf += "OLD_SECOND_STAGE_COUNT_STABLE: $OldSecondCount"
$Rf += "CURRENT_SECOND_STAGE_COUNT: $NewSecondCount"
$Rf += "SECOND_STAGE_REMOVED_COUNT: $($SecondRemoved.Count)"
$Rf += "SECOND_STAGE_ADDED_COUNT: $($SecondAdded.Count)"
$Rf += ""
$Rf += "START HERE:"
$Rf += $SummaryMd
$Rf += ""
$Rf += "FULL CSV:"
$Rf += $OutCsv

$Rf | Set-Content -Path $ReadFirst -Encoding UTF8

Write-Host ""
Write-Host "=== V17.7D MAIN COMPUTE DELTA AUDIT READY ==="
Write-Host "DELTA_AUDIT_STATUS: $AuditStatus"
Write-Host "RAW_UNIVERSE_COUNT_CURRENT: $RawCount"
Write-Host "CLASSIFIED_UNIVERSE_COUNT_CURRENT: $ClassifiedCount"
Write-Host "RAW_PRICE_OK_COUNT_CURRENT: $PriceOkCount"
Write-Host "RAW_PRICE_FAIL_COUNT_CURRENT: $PriceFailCount"
Write-Host "OLD_MAIN_COMPUTE_COUNT_STABLE: $OldMainCount"
Write-Host "CURRENT_MAIN_COMPUTE_COUNT: $NewMainCount"
Write-Host "MAIN_COMPUTE_REMOVED_COUNT: $($MainRemoved.Count)"
Write-Host "MAIN_COMPUTE_ADDED_COUNT: $($MainAdded.Count)"
Write-Host "OLD_SECOND_STAGE_COUNT_STABLE: $OldSecondCount"
Write-Host "CURRENT_SECOND_STAGE_COUNT: $NewSecondCount"
Write-Host "SECOND_STAGE_REMOVED_COUNT: $($SecondRemoved.Count)"
Write-Host "SECOND_STAGE_ADDED_COUNT: $($SecondAdded.Count)"
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
Write-Host "=== V17.7D MAIN COMPUTE DELTA AUDIT DONE ==="
