param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$OutDir = Join-Path $Root "outputs\v18\factor_audit"
$StateDir = Join-Path $Root "state\v18"
New-Item -ItemType Directory -Force -Path $OutDir, $StateDir | Out-Null

$FactorCodes = @("F006","F007","F008","F009","F010","F011")

$FactorAliases = @{
    "F006" = @("F006", "F006_SHORT_REV_5D", "SHORT_REV_5D", "short_rev", "short_reversal", "rev_5d")
    "F007" = @("F007", "F007_PULLBACK_IN_UPTREND", "PULLBACK_IN_UPTREND", "pullback", "uptrend")
    "F008" = @("F008", "F008_VOLUME_ABNORMAL_5_20", "VOLUME_ABNORMAL_5_20", "volume_abnormal", "vol_abnormal", "volume_5_20")
    "F009" = @("F009", "F009_VOLUME_PRICE_CONFIRM", "VOLUME_PRICE_CONFIRM", "volume_price", "price_confirm")
    "F010" = @("F010", "F010_XSEC_COMPOSITE_RANK", "XSEC_COMPOSITE_RANK", "xsec_composite", "composite_rank")
    "F011" = @("F011", "F011_TS_MOMENTUM_60_120", "TS_MOMENTUM_60_120", "ts_momentum", "momentum_60_120")
}

function Get-CsvColumns {
    param([string]$Path)

    try {
        $first = Get-Content -LiteralPath $Path -First 1
        if ([string]::IsNullOrWhiteSpace($first)) { return @() }

        return @(
            $first -split "," |
                ForEach-Object { $_.Trim().Trim('"') } |
                Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
        )
    } catch {
        return @()
    }
}

function Match-FactorColumns {
    param(
        [string[]]$Columns,
        [string]$FactorCode
    )

    $aliases = $FactorAliases[$FactorCode]
    $matched = @()

    foreach ($c in $Columns) {
        $lc = $c.ToLowerInvariant()

        foreach ($a in $aliases) {
            if ($lc -like "*$($a.ToLowerInvariant())*") {
                $matched += $c
                break
            }
        }
    }

    return @($matched | Select-Object -Unique)
}

function Get-RecentCsvFiles {
    param(
        [string[]]$Dirs
    )

    $files = @()

    foreach ($d in $Dirs) {
        if (Test-Path $d) {
            $files += Get-ChildItem -LiteralPath $d -Recurse -File -Include "*.csv" -ErrorAction SilentlyContinue |
                Where-Object {
                    $_.FullName -notmatch "\\archive\\" -and
                    $_.FullName -notmatch "\\deprecated\\"
                }
        }
    }

    return @($files | Sort-Object LastWriteTime -Descending)
}

Write-Host ""
Write-Host "=== V18.4F FORWARD TRACKER FACTOR COVERAGE START ==="

$SearchDirs = @(
    (Join-Path $Root "outputs\v18"),
    (Join-Path $Root "state\v18")
)

$CsvFiles = Get-RecentCsvFiles -Dirs $SearchDirs

$ForwardFiles = @(
    $CsvFiles |
        Where-Object {
            $p = $_.FullName.ToLowerInvariant()
            $p -like "*forward*" -or
            $p -like "*tracker*" -or
            $p -like "*outcome*" -or
            $p -like "*promotion*"
        }
)

$FactorOutputFiles = @(
    $CsvFiles |
        Where-Object {
            $p = $_.FullName.ToLowerInvariant()
            $p -like "*factor*" -or
            $p -like "*shadow*" -or
            $p -like "*pack*" -or
            $p -like "*rank*" -or
            $p -like "*top*"
        }
)

$CoverageRows = @()

foreach ($fcode in $FactorCodes) {
    $forwardHitFiles = @()
    $factorOutputHitFiles = @()
    $forwardColumns = @()
    $factorOutputColumns = @()

    foreach ($file in $ForwardFiles) {
        $cols = Get-CsvColumns -Path $file.FullName
        $matched = Match-FactorColumns -Columns $cols -FactorCode $fcode

        if ($matched.Count -gt 0) {
            $forwardHitFiles += $file.FullName
            $forwardColumns += $matched
        } else {
            try {
                $sample = Get-Content -LiteralPath $file.FullName -TotalCount 80 -ErrorAction SilentlyContinue
                foreach ($line in $sample) {
                    foreach ($alias in $FactorAliases[$fcode]) {
                        if ($line.ToLowerInvariant() -like "*$($alias.ToLowerInvariant())*") {
                            $forwardHitFiles += $file.FullName
                            break
                        }
                    }
                }
            } catch {}
        }
    }

    foreach ($file in $FactorOutputFiles) {
        $cols = Get-CsvColumns -Path $file.FullName
        $matched = Match-FactorColumns -Columns $cols -FactorCode $fcode

        if ($matched.Count -gt 0) {
            $factorOutputHitFiles += $file.FullName
            $factorOutputColumns += $matched
        }
    }

    $CoverageRows += [pscustomobject]@{
        factor_code = $fcode
        factor_output_file_count = ($factorOutputHitFiles | Select-Object -Unique).Count
        factor_output_columns = (($factorOutputColumns | Select-Object -Unique | Sort-Object) -join "; ")
        factor_output_files = (($factorOutputHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        forward_file_count = ($forwardHitFiles | Select-Object -Unique).Count
        forward_columns = (($forwardColumns | Select-Object -Unique | Sort-Object) -join "; ")
        forward_files = (($forwardHitFiles | Select-Object -Unique | Sort-Object) -join "; ")
        coverage_status = if (($forwardHitFiles | Select-Object -Unique).Count -gt 0) { "FORWARD_COVERED" } else { "FORWARD_MISSING" }
    }
}

# Pick best factor output CSV: most F006-F011 matched columns, then newest.
$CandidateFactorFiles = @()

foreach ($file in $FactorOutputFiles) {
    $cols = Get-CsvColumns -Path $file.FullName
    $score = 0

    foreach ($fcode in $FactorCodes) {
        $matched = Match-FactorColumns -Columns $cols -FactorCode $fcode
        if ($matched.Count -gt 0) {
            $score += 1
        }
    }

    if ($score -gt 0) {
        $CandidateFactorFiles += [pscustomobject]@{
            path = $file.FullName
            factor_match_count = $score
            last_write_time = $file.LastWriteTime
        }
    }
}

$BestFactorFile = $CandidateFactorFiles |
    Sort-Object factor_match_count, last_write_time -Descending |
    Select-Object -First 1

$ExpandedSnapshot = Join-Path $StateDir "V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv"
$ExpandedSnapshotStamped = Join-Path $StateDir ("V18_4F_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_" + $Stamp + ".csv")

$ExpandedRows = @()

if ($BestFactorFile) {
    $bestPath = $BestFactorFile.path
    $cols = Get-CsvColumns -Path $bestPath

    $tickerCol = $null
    foreach ($candidate in @("ticker","symbol","name")) {
        $hit = $cols | Where-Object { $_.ToLowerInvariant() -eq $candidate } | Select-Object -First 1
        if ($hit) {
            $tickerCol = $hit
            break
        }
    }

    if (-not $tickerCol) {
        $tickerCol = $cols | Where-Object { $_.ToLowerInvariant() -like "*ticker*" -or $_.ToLowerInvariant() -like "*symbol*" } | Select-Object -First 1
    }

    $rows = Import-Csv -LiteralPath $bestPath

    foreach ($r in $rows) {
        $ticker = ""
        if ($tickerCol -and ($r.PSObject.Properties.Name -contains $tickerCol)) {
            $ticker = [string]$r.$tickerCol
        }

        $obj = [ordered]@{
            snapshot_date = (Get-Date -Format "yyyy-MM-dd")
            source_factor_file = $bestPath
            ticker = $ticker
        }

        foreach ($fcode in $FactorCodes) {
            $matchedCols = Match-FactorColumns -Columns $cols -FactorCode $fcode
            $value = ""

            foreach ($mc in $matchedCols) {
                if ($r.PSObject.Properties.Name -contains $mc) {
                    $candidateValue = [string]$r.$mc
                    if (-not [string]::IsNullOrWhiteSpace($candidateValue)) {
                        $value = $candidateValue
                        break
                    }
                }
            }

            $obj[$fcode + "_value"] = $value
        }

        $ExpandedRows += [pscustomobject]$obj
    }

    if ($ExpandedRows.Count -gt 0) {
        $ExpandedRows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $ExpandedSnapshotStamped
        Copy-Item -Force $ExpandedSnapshotStamped $ExpandedSnapshot
    }
}

$CoverageCsv = Join-Path $OutDir ("V18_4F_FORWARD_FACTOR_COVERAGE_" + $Stamp + ".csv")
$CoverageMd = Join-Path $OutDir ("V18_4F_FORWARD_FACTOR_COVERAGE_" + $Stamp + ".md")
$CurrentCoverageCsv = Join-Path $OutDir "V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.csv"
$CurrentCoverageMd = Join-Path $OutDir "V18_4F_CURRENT_FORWARD_FACTOR_COVERAGE.md"

$CoverageRows | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $CoverageCsv
Copy-Item -Force $CoverageCsv $CurrentCoverageCsv

$coveredCount = @($CoverageRows | Where-Object { $_.coverage_status -eq "FORWARD_COVERED" }).Count
$missingCount = @($CoverageRows | Where-Object { $_.coverage_status -eq "FORWARD_MISSING" }).Count
$outputAvailableCount = @($CoverageRows | Where-Object { $_.factor_output_file_count -gt 0 }).Count

$md = @()
$md += "# V18.4F Forward Tracker Factor Coverage"
$md += ""
$md += "生成时间：$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
$md += ""
$md += "## 1. 结论"
$md += ""
$md += "- WORLDQUANT_FACTOR_COUNT: ``$($FactorCodes.Count)``"
$md += "- FACTOR_OUTPUT_AVAILABLE_COUNT: ``$outputAvailableCount``"
$md += "- FORWARD_COVERED_COUNT: ``$coveredCount``"
$md += "- FORWARD_MISSING_COUNT: ``$missingCount``"
$md += "- BEST_FACTOR_OUTPUT_FILE: ``$($BestFactorFile.path)``"
$md += "- EXPANDED_FORWARD_SNAPSHOT: ``$ExpandedSnapshot``"
$md += "- EXPANDED_FORWARD_SNAPSHOT_ROWS: ``$($ExpandedRows.Count)``"
$md += ""
$md += "## 2. 覆盖表"
$md += ""
$md += "| factor | factor output files | forward files | status |"
$md += "|---|---:|---:|---|"

foreach ($r in $CoverageRows) {
    $md += "| $($r.factor_code) | $($r.factor_output_file_count) | $($r.forward_file_count) | $($r.coverage_status) |"
}

$md += ""
$md += "## 3. 解释"
$md += ""
$md += "V18.4F 不改变 official decision。它只检查 F006-F011 是否被 forward / tracker / outcome / promotion 文件覆盖。"
$md += ""
$md += "如果 FORWARD_MISSING_COUNT 大于 0，说明现有 V18.4A forward tracker 没有完整捕获所有 WorldQuant 风格因子。"
$md += ""
$md += "本脚本生成旁路扩展快照 V18_4F_CURRENT_WORLDQUANT_FACTOR_FORWARD_SNAPSHOT.csv，用来保存当前 F006-F011 的 ticker-level 因子值，后续可以接入 V18.4A tracker 或 promotion evaluator。"
$md += ""
$md += "## 4. 输出文件"
$md += ""
$md += "- COVERAGE_CSV: ``$CoverageCsv``"
$md += "- COVERAGE_MD: ``$CoverageMd``"
$md += "- EXPANDED_FORWARD_SNAPSHOT: ``$ExpandedSnapshot``"

$md -join "`r`n" | Set-Content -Encoding UTF8 -Path $CoverageMd
Copy-Item -Force $CoverageMd $CurrentCoverageMd

Write-Host ""
Write-Host "=== V18.4F FORWARD TRACKER FACTOR COVERAGE READY ==="
Write-Host "WORLDQUANT_FACTOR_COUNT: $($FactorCodes.Count)"
Write-Host "FACTOR_OUTPUT_AVAILABLE_COUNT: $outputAvailableCount"
Write-Host "FORWARD_COVERED_COUNT: $coveredCount"
Write-Host "FORWARD_MISSING_COUNT: $missingCount"
Write-Host "EXPANDED_FORWARD_SNAPSHOT_ROWS: $($ExpandedRows.Count)"
Write-Host "BEST_FACTOR_OUTPUT_FILE: $($BestFactorFile.path)"
Write-Host ""
Write-Host "READ:"
Write-Host $CurrentCoverageMd
Write-Host "CSV:"
Write-Host $CurrentCoverageCsv
Write-Host "EXPANDED SNAPSHOT:"
Write-Host $ExpandedSnapshot
