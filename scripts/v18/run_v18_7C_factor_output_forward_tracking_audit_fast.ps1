
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

Write-Host ""
Write-Host "=== V18.7C FAST FACTOR OUTPUT + FORWARD TRACKING AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: TARGETED_CURRENT_FILES_ONLY"

$RuntimeGraph = Join-Path $OpsDir "V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"

$runtimeCodeCount = 0
$missingRefCount = 0

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

function Test-FactorTextMatch {
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

function Get-CsvHeaderColumns {
    param([string]$Path)

    try {
        $first = Get-Content -LiteralPath $Path -First 1 -ErrorAction Stop

        if ([string]::IsNullOrWhiteSpace($first)) {
            return @()
        }

        return @(
            $first -split "," |
                ForEach-Object { $_.Trim().Trim('"') } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )
    }
    catch {
        return @()
    }
}

function Get-FastNonNullStats {
    param(
        [string]$Path,
        [string[]]$Columns
    )

    $rowCount = 0
    $nonNull = 0
    $numeric = 0

    if ($Columns.Count -eq 0) {
        return [pscustomobject]@{
            rows = 0
            non_null = 0
            numeric = 0
        }
    }

    try {
        $sample = Get-Content -LiteralPath $Path -TotalCount 500 -ErrorAction Stop

        if ($sample.Count -le 1) {
            return [pscustomobject]@{
                rows = 0
                non_null = 0
                numeric = 0
            }
        }

        $rows = $sample | ConvertFrom-Csv

        foreach ($r in $rows) {
            $rowCount += 1

            foreach ($c in $Columns) {
                $prop = $r.PSObject.Properties[$c]

                if ($null -ne $prop) {
                    $v = [string]$prop.Value

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
    }
    catch {}

    return [pscustomobject]@{
        rows = $rowCount
        non_null = $nonNull
        numeric = $numeric
    }
}

$TargetDirs = @(
    (Join-Path $Root "outputs\v18\factor_pack"),
    (Join-Path $Root "outputs\v18\factor_shadow"),
    (Join-Path $Root "outputs\v18\outcome_summary"),
    (Join-Path $Root "outputs\v18\forward_outcome"),
    (Join-Path $Root "outputs\v18\promotion_merge"),
    (Join-Path $Root "outputs\v18\daily_integrated"),
    (Join-Path $Root "outputs\v18\read_center"),
    (Join-Path $Root "state\v18")
)

$CsvFiles = @()
$TextFiles = @()

foreach ($d in $TargetDirs) {
    if (Test-Path $d) {
        $CsvFiles += Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.csv" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\archive\\" -and
                $_.FullName -notmatch "\\deprecated\\" -and
                $_.FullName -notmatch "\\patch_backup\\"
            }

        $TextFiles += Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.md","*.txt","*.json" -ErrorAction SilentlyContinue |
            Where-Object {
                $_.FullName -notmatch "\\archive\\" -and
                $_.FullName -notmatch "\\deprecated\\" -and
                $_.FullName -notmatch "\\patch_backup\\"
            }
    }
}

Write-Host "TARGET_CSV_FILE_COUNT: $($CsvFiles.Count)"
Write-Host "TARGET_TEXT_FILE_COUNT: $($TextFiles.Count)"

$Rows = @()

foreach ($factor in $FactorDefs) {
    $columnHitFiles = @()
    $columnHitDetails = @()
    $forwardHitFiles = @()
    $topRankHitFiles = @()
    $textHitFiles = @()

    $totalMatchedColumns = 0
    $totalNonNull = 0
    $totalNumeric = 0
    $totalRowsScanned = 0

    foreach ($csv in $CsvFiles) {
        $cols = Get-CsvHeaderColumns -Path $csv.FullName

        $matchedCols = @(
            $cols |
                Where-Object { Test-FactorTextMatch -Text $_ -Factor $factor }
        )

        if ($matchedCols.Count -gt 0) {
            $columnHitFiles += $csv.FullName
            $totalMatchedColumns += $matchedCols.Count

            $stats = Get-FastNonNullStats -Path $csv.FullName -Columns $matchedCols
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
                if (Test-FactorTextMatch -Text $c -Factor $factor) {
                    $hit = $true
                    break
                }
            }

            if (-not $hit) {
                try {
                    $sample = Get-Content -LiteralPath $csv.FullName -TotalCount 80 -ErrorAction SilentlyContinue
                    foreach ($line in $sample) {
                        if (Test-FactorTextMatch -Text $line -Factor $factor) {
                            $hit = $true
                            break
                        }
                    }
                }
                catch {}
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
            $hit = $false

            foreach ($c in $cols) {
                if (Test-FactorTextMatch -Text $c -Factor $factor) {
                    $hit = $true
                    break
                }
            }

            if (-not $hit) {
                try {
                    $sample2 = Get-Content -LiteralPath $csv.FullName -TotalCount 80 -ErrorAction SilentlyContinue
                    foreach ($line in $sample2) {
                        if (Test-FactorTextMatch -Text $line -Factor $factor) {
                            $hit = $true
                            break
                        }
                    }
                }
                catch {}
            }

            if ($hit) {
                $topRankHitFiles += $csv.FullName
            }
        }
    }

    foreach ($tf in $TextFiles) {
        try {
            $sampleText = Get-Content -LiteralPath $tf.FullName -TotalCount 120 -ErrorAction SilentlyContinue

            $hit = $false
            foreach ($line in $sampleText) {
                if (Test-FactorTextMatch -Text $line -Factor $factor) {
                    $hit = $true
                    break
                }
            }

            if ($hit) {
                $textHitFiles += $tf.FullName

                $lower = $tf.FullName.ToLowerInvariant()

                if ($lower -like "*forward*" -or $lower -like "*tracker*" -or $lower -like "*outcome*" -or $lower -like "*promotion*") {
                    $forwardHitFiles += $tf.FullName
                }

                if ($lower -like "*factor_pack*" -or $lower -like "*factor_shadow*" -or $lower -like "*top*" -or $lower -like "*rank*") {
                    $topRankHitFiles += $tf.FullName
                }
            }
        }
        catch {}
    }

    $outputColumnStatus = "OUTPUT_COLUMN_NOT_FOUND"
    if (($columnHitFiles | Select-Object -Unique).Count -gt 0) {
        $outputColumnStatus = "OUTPUT_COLUMN_FOUND"
    }

    $outputValueStatus = "NO_NON_NULL_VALUES"
    if ($totalNonNull -gt 0) {
        $outputValueStatus = "HAS_NON_NULL_VALUES"
    }

    $forwardStatus = "NOT_FOUND_IN_FORWARD_TRACKING"
    if (($forwardHitFiles | Select-Object -Unique).Count -gt 0) {
        $forwardStatus = "FOUND_IN_FORWARD_TRACKING_OR_OUTCOME_FILES"
    }

    $topRankStatus = "NOT_FOUND_IN_TOP_OR_RANK_OUTPUTS"
    if (($topRankHitFiles | Select-Object -Unique).Count -gt 0) {
        $topRankStatus = "FOUND_IN_TOP_OR_RANK_OUTPUTS"
    }

    $Rows += [pscustomobject]@{
        factor_code = $factor.code
        factor_name = $factor.name
        output_column_status = $outputColumnStatus
        output_value_status = $outputValueStatus
        top_rank_output_status = $topRankStatus
        forward_tracking_status = $forwardStatus
        matched_column_count = $totalMatchedColumns
        output_non_null_value_count = $totalNonNull
        output_numeric_value_count = $totalNumeric
        scanned_sample_rows = $totalRowsScanned
        column_hit_file_count = ($columnHitFiles | Select-Object -Unique).Count
        text_hit_file_count = ($textHitFiles | Select-Object -Unique).Count
        forward_hit_file_count = ($forwardHitFiles | Select-Object -Unique).Count
        top_rank_hit_file_count = ($topRankHitFiles | Select-Object -Unique).Count
        column_hit_files = (($columnHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        forward_hit_files = (($forwardHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        top_rank_hit_files = (($topRankHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        column_hit_details = ($columnHitDetails -join " || ")
        official_decision_impact = "NONE"
    }
}

$SelectedFactor = ""
$SelectedFactorFiles = @()

$SelectedSearchDirs = @(
    (Join-Path $Root "outputs\v18\factor_shadow"),
    (Join-Path $Root "outputs\v18\factor_pack"),
    (Join-Path $Root "outputs\v18\outcome_summary"),
    (Join-Path $Root "outputs\v18\daily_integrated")
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
            }
            catch {}
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
$md += "Generated: ``$Stamp``"
$md += ""
$md += "## 1. Status"
$md += ""
$md += "- V18_4E_STATUS: ``OK_FACTOR_OUTPUT_FORWARD_AUDIT_READY``"
$md += "- AUDIT_ENGINE: ``V18.7C_FAST_TARGETED``"
$md += "- RUNTIME_CODE_COUNT: ``$runtimeCodeCount``"
$md += "- MISSING_REFERENCE_COUNT: ``$missingRefCount``"
$md += "- WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: ``$expectedCount``"
$md += "- OUTPUT_COLUMN_FOUND_COUNT: ``$outputColumnFoundCount``"
$md += "- NON_NULL_VALUE_FACTOR_COUNT: ``$nonNullFoundCount``"
$md += "- TOP_OR_RANK_OUTPUT_FOUND_COUNT: ``$rankFoundCount``"
$md += "- FORWARD_TRACKING_FOUND_COUNT: ``$forwardFoundCount``"
$md += "- CURRENT_SELECTED_FACTOR: ``$SelectedFactor``"
$md += "- TARGET_CSV_FILE_COUNT: ``$($CsvFiles.Count)``"
$md += "- TARGET_TEXT_FILE_COUNT: ``$($TextFiles.Count)``"
$md += ""
$md += "## 2. Factor Output / Forward Coverage"
$md += ""
$md += "| factor | name | output column | non-null | top/rank output | forward tracking | matched cols | non-null values |"
$md += "|---|---|---|---|---|---|---:|---:|"

foreach ($r in $Rows) {
    $md += "| $($r.factor_code) | $($r.factor_name) | $($r.output_column_status) | $($r.output_value_status) | $($r.top_rank_output_status) | $($r.forward_tracking_status) | $($r.matched_column_count) | $($r.output_non_null_value_count) |"
}

$md += ""
$md += "## 3. Interpretation"
$md += ""
$md += "- V18.7C uses targeted current output/state directories instead of scanning the entire outputs/state tree."
$md += "- This is intended to preserve the audit contract while reducing repeated filesystem and CSV IO."
$md += "- OFFICIAL_DECISION_IMPACT remains NONE."
$md += ""
$md += "## 4. Selected Factor Sources"
$md += ""

foreach ($f in ($SelectedFactorFiles | Select-Object -Unique | Sort-Object)) {
    $md += "- ``$f``"
}

$md -join "`r`n" | Set-Content -Encoding UTF8 -Path $MdOut
Copy-Item -Force $MdOut $CurrentMd

Write-Host ""
Write-Host "=== V18.7C FAST FACTOR OUTPUT + FORWARD TRACKING AUDIT READY ==="
Write-Host "RUNTIME_CODE_COUNT: $runtimeCodeCount"
Write-Host "MISSING_REFERENCE_COUNT: $missingRefCount"
Write-Host "WORLDQUANT_STYLE_FACTOR_COUNT_EXPECTED: $expectedCount"
Write-Host "OUTPUT_COLUMN_FOUND_COUNT: $outputColumnFoundCount"
Write-Host "NON_NULL_VALUE_FACTOR_COUNT: $nonNullFoundCount"
Write-Host "TOP_OR_RANK_OUTPUT_FOUND_COUNT: $rankFoundCount"
Write-Host "FORWARD_TRACKING_FOUND_COUNT: $forwardFoundCount"
Write-Host "CURRENT_SELECTED_FACTOR: $SelectedFactor"
Write-Host "CSV: $CurrentCsv"
Write-Host "READ: $CurrentMd"
Write-Host "=== V18.7C FAST FACTOR OUTPUT + FORWARD TRACKING AUDIT DONE ==="
