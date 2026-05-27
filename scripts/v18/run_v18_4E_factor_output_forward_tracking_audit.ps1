param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$SkipRuntimeRefresh,
    [switch]$SkipFactorPackRefresh
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$OutDir = Join-Path $Root "outputs\v18\factor_audit"
$OpsDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$RuntimeAuditScript = Join-Path $Root "scripts\v18\run_v18_4C_runtime_dependency_audit.ps1"
$FactorAuditScript = Join-Path $Root "scripts\v18\run_v18_4D_factor_pack_audit.ps1"

Write-Host ""
Write-Host "=== V18.4E FACTOR OUTPUT + FORWARD TRACKING AUDIT START ==="

if (Test-Path $RuntimeAuditScript) {
    if (-not $SkipRuntimeRefresh) {
    Write-Host ""
    Write-Host "STEP 1: refresh V18.4C runtime audit"
    powershell -NoProfile -ExecutionPolicy Bypass -File $RuntimeAuditScript
}
else {
    Write-Host ""
    Write-Host "STEP 1 SKIPPED: refresh V18.4C runtime audit; use current runtime graph"
}
}

if (Test-Path $FactorAuditScript) {
    if (-not $SkipFactorPackRefresh) {
    Write-Host ""
    Write-Host "STEP 2: refresh V18.4D factor pack audit"
    powershell -NoProfile -ExecutionPolicy Bypass -File $FactorAuditScript
}
else {
    Write-Host ""
    Write-Host "STEP 2 SKIPPED: refresh V18.4D factor pack audit; use current factor pack audit"
}
}

$RuntimeGraph = Join-Path $OpsDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"

$runtimeCodeCount = ""
$missingRefCount = ""

if (Test-Path $RuntimeGraph) {
    $runtimeRows = Import-Csv -LiteralPath $RuntimeGraph
    $runtimeCodeCount = @(
        $runtimeRows |
            Where-Object { $_.exists -eq "True" -and $_.callee -match '\.(ps1|py|bat|cmd)$' } |
            Select-Object -ExpandProperty callee -Unique
    ).Count

    $missingRefCount = @(
        $runtimeRows |
            Where-Object { $_.exists -eq "False" }
    ).Count
}

$FactorDefs = @(
    [pscustomobject]@{
        code = "F006"
        name = "SHORT_REV_5D"
        aliases = @("F006_SHORT_REV_5D", "SHORT_REV_5D", "short_rev", "short_reversal", "rev_5d")
    },
    [pscustomobject]@{
        code = "F007"
        name = "PULLBACK_IN_UPTREND"
        aliases = @("F007_PULLBACK_IN_UPTREND", "PULLBACK_IN_UPTREND", "pullback", "uptrend")
    },
    [pscustomobject]@{
        code = "F008"
        name = "VOLUME_ABNORMAL_5_20"
        aliases = @("F008_VOLUME_ABNORMAL_5_20", "VOLUME_ABNORMAL_5_20", "volume_abnormal", "vol_abnormal", "volume_5_20")
    },
    [pscustomobject]@{
        code = "F009"
        name = "VOLUME_PRICE_CONFIRM"
        aliases = @("F009_VOLUME_PRICE_CONFIRM", "VOLUME_PRICE_CONFIRM", "volume_price", "price_confirm")
    },
    [pscustomobject]@{
        code = "F010"
        name = "XSEC_COMPOSITE_RANK"
        aliases = @("F010_XSEC_COMPOSITE_RANK", "XSEC_COMPOSITE_RANK", "xsec_composite", "composite_rank")
    },
    [pscustomobject]@{
        code = "F011"
        name = "TS_MOMENTUM_60_120"
        aliases = @("F011_TS_MOMENTUM_60_120", "TS_MOMENTUM_60_120", "ts_momentum", "momentum_60_120")
    }
)

$SearchDirs = @(
    (Join-Path $Root "outputs\v18"),
    (Join-Path $Root "state\v18")
)

$CsvFiles = @()

foreach ($d in $SearchDirs) {
    if (Test-Path $d) {
        $CsvFiles += Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.csv" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\archive\\" -and
                $_.FullName -notmatch "\\deprecated\\"
            }
    }
}

$TextFiles = @()

foreach ($d in $SearchDirs) {
    if (Test-Path $d) {
        $TextFiles += Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.md","*.txt","*.json" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\archive\\" -and
                $_.FullName -notmatch "\\deprecated\\"
            }
    }
}

function Get-CsvHeaderColumns {
    param([string]$Path)

    try {
        $first = Get-Content -LiteralPath $Path -First 1
        if ([string]::IsNullOrWhiteSpace($first)) {
            return @()
        }

        return @(
            $first -split "," |
                ForEach-Object { $_.Trim().Trim('"') } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )
    } catch {
        return @()
    }
}

function Test-ColumnMatch {
    param(
        [string]$Column,
        [object]$Factor
    )

    $c = $Column.ToLowerInvariant()

    if ($c -like "*$($Factor.code.ToLowerInvariant())*") {
        return $true
    }

    if ($c -like "*$($Factor.name.ToLowerInvariant())*") {
        return $true
    }

    foreach ($a in $Factor.aliases) {
        if ($c -like "*$($a.ToLowerInvariant())*") {
            return $true
        }
    }

    return $false
}

function Test-TextMatch {
    param(
        [string]$Text,
        [object]$Factor
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $false
    }

    $t = $Text.ToLowerInvariant()

    if ($t -like "*$($Factor.code.ToLowerInvariant())*") {
        return $true
    }

    if ($t -like "*$($Factor.name.ToLowerInvariant())*") {
        return $true
    }

    foreach ($a in $Factor.aliases) {
        if ($t -like "*$($a.ToLowerInvariant())*") {
            return $true
        }
    }

    return $false
}

function Get-NonNullStats {
    param(
        [string]$Path,
        [string[]]$Columns
    )

    $nonNull = 0
    $numeric = 0
    $rowCount = 0

    if ($Columns.Count -eq 0) {
        return [pscustomobject]@{
            rows = 0
            non_null = 0
            numeric = 0
        }
    }

    try {
        $rows = Import-Csv -LiteralPath $Path
        foreach ($r in $rows) {
            $rowCount += 1

            foreach ($c in $Columns) {
                if ($r.PSObject.Properties.Name -contains $c) {
                    $v = [string]$r.$c

                    if (-not [string]::IsNullOrWhiteSpace($v)) {
                        $nonNull += 1

                        $tmp = 0.0
                        if ([double]::TryParse($v, [ref]$tmp)) {
                            $numeric += 1
                        }
                    }
                }
            }
        }
    } catch {
        # skip bad csv
    }

    return [pscustomobject]@{
        rows = $rowCount
        non_null = $nonNull
        numeric = $numeric
    }
}

$Rows = @()

foreach ($factor in $FactorDefs) {
    $columnHitFiles = @()
    $columnHitDetails = @()
    $textHitFiles = @()
    $forwardHitFiles = @()
    $topRankHitFiles = @()

    $totalMatchedColumns = 0
    $totalNonNull = 0
    $totalNumeric = 0
    $totalRowsScanned = 0

    foreach ($csv in $CsvFiles) {
        $cols = Get-CsvHeaderColumns -Path $csv.FullName

        $matchedCols = @(
            $cols |
                Where-Object { Test-ColumnMatch -Column $_ -Factor $factor }
        )

        if ($matchedCols.Count -gt 0) {
            $columnHitFiles += $csv.FullName
            $totalMatchedColumns += $matchedCols.Count

            $stats = Get-NonNullStats -Path $csv.FullName -Columns $matchedCols
            $totalNonNull += $stats.non_null
            $totalNumeric += $stats.numeric
            $totalRowsScanned += $stats.rows

            $columnHitDetails += "$($csv.FullName) => $($matchedCols -join '|')"
        }

        $pathLower = $csv.FullName.ToLowerInvariant()
        $isForwardFile = (
            $pathLower -like "*forward*" -or
            $pathLower -like "*tracker*" -or
            $pathLower -like "*outcome*" -or
            $pathLower -like "*promotion*"
        )

        if ($isForwardFile) {
            $hit = $false

            foreach ($c in $cols) {
                if (Test-ColumnMatch -Column $c -Factor $factor) {
                    $hit = $true
                    break
                }
            }

            if (-not $hit) {
                try {
                    $sample = Get-Content -LiteralPath $csv.FullName -TotalCount 50 -ErrorAction SilentlyContinue
                    foreach ($line in $sample) {
                        if (Test-TextMatch -Text $line -Factor $factor) {
                            $hit = $true
                            break
                        }
                    }
                } catch {}
            }

            if ($hit) {
                $forwardHitFiles += $csv.FullName
            }
        }

        $isRankFile = (
            $pathLower -like "*factor_pack*" -or
            $pathLower -like "*factor_shadow*" -or
            $pathLower -like "*top*" -or
            $pathLower -like "*rank*"
        )

        if ($isRankFile) {
            $rankHit = $false

            foreach ($c in $cols) {
                if (Test-ColumnMatch -Column $c -Factor $factor) {
                    $rankHit = $true
                    break
                }
            }

            if (-not $rankHit) {
                try {
                    $sample2 = Get-Content -LiteralPath $csv.FullName -TotalCount 100 -ErrorAction SilentlyContinue
                    foreach ($line in $sample2) {
                        if (Test-TextMatch -Text $line -Factor $factor) {
                            $rankHit = $true
                            break
                        }
                    }
                } catch {}
            }

            if ($rankHit) {
                $topRankHitFiles += $csv.FullName
            }
        }
    }

    foreach ($tf in $TextFiles) {
        try {
            $match = Select-String -LiteralPath $tf.FullName -Pattern $factor.code,$factor.name -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1

            if (-not $match) {
                foreach ($a in $factor.aliases) {
                    $match = Select-String -LiteralPath $tf.FullName -Pattern $a -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1
                    if ($match) { break }
                }
            }

            if ($match) {
                $textHitFiles += $tf.FullName

                $lower = $tf.FullName.ToLowerInvariant()
                if ($lower -like "*forward*" -or $lower -like "*tracker*" -or $lower -like "*outcome*" -or $lower -like "*promotion*") {
                    $forwardHitFiles += $tf.FullName
                }

                if ($lower -like "*factor_pack*" -or $lower -like "*factor_shadow*" -or $lower -like "*top*" -or $lower -like "*rank*") {
                    $topRankHitFiles += $tf.FullName
                }
            }
        } catch {
            # skip
        }
    }

    $columnStatus = "NO_OUTPUT_COLUMN_FOUND"
    if (($columnHitFiles | Select-Object -Unique).Count -gt 0) {
        $columnStatus = "OUTPUT_COLUMN_FOUND"
    }

    $valueStatus = "NO_NON_NULL_VALUES"
    if ($totalNonNull -gt 0) {
        $valueStatus = "HAS_NON_NULL_VALUES"
    }

    $forwardStatus = "NOT_FOUND_IN_FORWARD_TRACKING"
    if (($forwardHitFiles | Select-Object -Unique).Count -gt 0) {
        $forwardStatus = "FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES"
    }

    $rankStatus = "NOT_FOUND_IN_TOP_OR_RANK_OUTPUTS"
    if (($topRankHitFiles | Select-Object -Unique).Count -gt 0) {
        $rankStatus = "FOUND_IN_TOP_OR_RANK_OUTPUTS"
    }

    $Rows += [pscustomobject]@{
        factor_code = $factor.code
        factor_name = $factor.name
        output_column_status = $columnStatus
        output_value_status = $valueStatus
        forward_tracking_status = $forwardStatus
        top_rank_output_status = $rankStatus
        matched_column_count = $totalMatchedColumns
        output_non_null_value_count = $totalNonNull
        output_numeric_value_count = $totalNumeric
        scanned_row_count = $totalRowsScanned
        column_hit_file_count = ($columnHitFiles | Select-Object -Unique).Count
        text_hit_file_count = ($textHitFiles | Select-Object -Unique).Count
        forward_hit_file_count = ($forwardHitFiles | Select-Object -Unique).Count
        top_rank_hit_file_count = ($topRankHitFiles | Select-Object -Unique).Count
        column_hit_files = (($columnHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        forward_hit_files = (($forwardHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        top_rank_hit_files = (($topRankHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        column_hit_details = (($columnHitDetails | Sort-Object) -join "; ")
    }
}

$SelectedFactor = ""
$SelectedFactorFiles = @()

$SelectedSearchDirs = @(
    (Join-Path $Root "outputs\v18\daily_integrated"),
    (Join-Path $Root "outputs\v18\factor_shadow"),
    (Join-Path $Root "outputs\v18\factor_pack"),
    (Join-Path $Root "outputs\v18\outcome_summary")
)

foreach ($d in $SelectedSearchDirs) {
    if (Test-Path $d) {
        $files = Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.md","*.txt","*.csv" -ErrorAction SilentlyContinue
        foreach ($f in $files) {
            try {
                $m = Select-String -LiteralPath $f.FullName -Pattern "SELECTED_FACTOR" -SimpleMatch -ErrorAction SilentlyContinue | Select-Object -First 1
                if ($m) {
                    $SelectedFactorFiles += $f.FullName

                    if ($m.Line -match 'SELECTED_FACTOR\s*[:=]\s*`?([A-Za-z0-9_]+)`?') {
                        $SelectedFactor = $matches[1]
                    }
                }
            } catch {}
        }
    }
}

$CsvOut = Join-Path $OutDir "V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_$Stamp.csv"
$MdOut = Join-Path $OutDir "V18_4E_FACTOR_OUTPUT_FORWARD_AUDIT_$Stamp.md"
$CurrentCsv = Join-Path $OutDir "V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.csv"
$CurrentMd = Join-Path $OutDir "V18_4E_CURRENT_FACTOR_OUTPUT_FORWARD_AUDIT.md"

$Rows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $CsvOut
Copy-Item -Force $CsvOut $CurrentCsv

$expectedCount = $FactorDefs.Count
$outputColumnFoundCount = @($Rows | Where-Object { $_.output_column_status -eq "OUTPUT_COLUMN_FOUND" }).Count
$nonNullFoundCount = @($Rows | Where-Object { $_.output_value_status -eq "HAS_NON_NULL_VALUES" }).Count
$forwardFoundCount = @($Rows | Where-Object { $_.forward_tracking_status -eq "FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES" }).Count
$rankFoundCount = @($Rows | Where-Object { $_.top_rank_output_status -eq "FOUND_IN_TOP_OR_RANK_OUTPUTS" }).Count

$md = @()

$md += "# V18.4E Factor Output + Forward Tracking Audit"
$md += ""
$md += "生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += ""

$md += "## 1. 结论"
$md += ""
$md += "- RUNTIME_CODE_COUNT: ``$runtimeCodeCount``"
$md += "- MISSING_REFERENCE_COUNT: ``$missingRefCount``"
$md += "- WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: ``$expectedCount``"
$md += "- OUTPUT_COLUMN_FOUND_COUNT: ``$outputColumnFoundCount``"
$md += "- NON_NULL_VALUE_FACTOR_COUNT: ``$nonNullFoundCount``"
$md += "- TOP_OR_RANK_OUTPUT_FOUND_COUNT: ``$rankFoundCount``"
$md += "- FORWARD_TRACKING_FOUND_COUNT: ``$forwardFoundCount``"
$md += "- CURRENT_SELECTED_FACTOR: ``$SelectedFactor``"
$md += "- OFFICIAL_DECISION_IMPACT: ``NONE_UNLESS_PROMOTED``"
$md += ""

$md += "## 2. 因子输出覆盖表"
$md += ""
$md += "| factor | name | output column | non-null | top/rank output | forward tracking | matched cols | non-null values |"
$md += "|---|---|---|---|---|---|---:|---:|"

foreach ($r in $Rows) {
    $md += "| $($r.factor_code) | $($r.factor_name) | $($r.output_column_status) | $($r.output_value_status) | $($r.top_rank_output_status) | $($r.forward_tracking_status) | $($r.matched_column_count) | $($r.output_non_null_value_count) |"
}

$md += ""
$md += "## 3. 解释"
$md += ""
$md += "V18.4D 证明 F006-F011 在当前 runtime graph 里。V18.4E 进一步检查这些因子是否在输出 CSV / 文本 / forward outcome 相关文件里出现。"
$md += ""
$md += "如果某个因子是 OUTPUT_COLUMN_FOUND 且 HAS_NON_NULL_VALUES，说明它不只是代码里存在，而是已经产生了实际输出值。"
$md += ""
$md += "如果某个因子是 FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES，说明它已经被 forward tracker / outcome / promotion 相关文件覆盖。"
$md += ""
$md += "如果某个因子只在代码里存在、没有输出列，那下一步需要修 V18.3D factor pack 的输出 CSV。"
$md += ""
$md += "如果某个因子有输出列但没有 forward tracking，下一步需要修 V18.4A forward tracker 的 factor capture 字段。"
$md += ""

$md += "## 4. Selected Factor 来源文件"
$md += ""

foreach ($f in ($SelectedFactorFiles | Select-Object -Unique | Sort-Object)) {
    $md += "- ``$f``"
}

$md += ""

$md += "## 5. 输出文件"
$md += ""
$md += "- CSV: ``$CsvOut``"
$md += "- MD: ``$MdOut``"

$md -join "`r`n" | Set-Content -Encoding UTF8 -Path $MdOut
Copy-Item -Force $MdOut $CurrentMd

Write-Host ""
Write-Host "=== V18.4E FACTOR OUTPUT + FORWARD TRACKING AUDIT READY ==="
Write-Host "RUNTIME_CODE_COUNT: $runtimeCodeCount"
Write-Host "MISSING_REFERENCE_COUNT: $missingRefCount"
Write-Host "WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: $expectedCount"
Write-Host "OUTPUT_COLUMN_FOUND_COUNT: $outputColumnFoundCount"
Write-Host "NON_NULL_VALUE_FACTOR_COUNT: $nonNullFoundCount"
Write-Host "TOP_OR_RANK_OUTPUT_FOUND_COUNT: $rankFoundCount"
Write-Host "FORWARD_TRACKING_FOUND_COUNT: $forwardFoundCount"
Write-Host "CURRENT_SELECTED_FACTOR: $SelectedFactor"
Write-Host ""
Write-Host "READ:"
Write-Host $CurrentMd
Write-Host "CSV:"
Write-Host $CurrentCsv

