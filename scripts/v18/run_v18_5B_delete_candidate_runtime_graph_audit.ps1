$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$ClassifierCsv = Join-Path $Root "outputs\v18\ops\V18_5A_R2_CURRENT_RUNTIME_DECOUPLING_CLASSIFIER.csv"
$RuntimeGraphCsv = Join-Path $Root "outputs\v18\ops\V18_4C_CURRENT_RUNTIME_DEPENDENCY_GRAPH.csv"
$RuntimeAuditMd = Join-Path $Root "outputs\v18\ops\V18_4C_CURRENT_RUNTIME_DEPENDENCY_AUDIT.md"

$OutDir = Join-Path $Root "outputs\v18\ops"
$OutCsv = Join-Path $OutDir "V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.csv"
$OutMd = Join-Path $OutDir "V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.md"
$ReadFirst = Join-Path $OutDir "V18_5B_READ_FIRST.txt"

if (!(Test-Path $ClassifierCsv)) {
    throw "MISSING CLASSIFIER CSV: $ClassifierCsv"
}

if (!(Test-Path $RuntimeGraphCsv)) {
    throw "MISSING RUNTIME GRAPH CSV: $RuntimeGraphCsv. Run V18.4J-R1 or V18.4C runtime audit first."
}

function Normalize-Rel {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    $p = $Value.Trim()
    $p = $p.Trim('"')
    $p = $p.Trim("'")
    $p = $p -replace '/', '\'

    $prefix = $Root + "\"

    if ($p.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $p = $p.Substring($prefix.Length)
    }

    if ($p.StartsWith(".\")) {
        $p = $p.Substring(2)
    }

    return $p
}

function Get-AllText {
    param($Row)

    $parts = New-Object System.Collections.Generic.List[string]

    foreach ($p in $Row.PSObject.Properties) {
        if ($null -ne $p.Value) {
            [void]$parts.Add("$($p.Name)=$($p.Value)")
        }
    }

    return ($parts.ToArray() -join " | ")
}

function Get-FirstPathLikeValue {
    param($Row)

    foreach ($p in $Row.PSObject.Properties) {
        if ($null -ne $p.Value) {
            $v = Normalize-Rel "$($p.Value)"
            $vl = $v.ToLowerInvariant()

            if (
                $vl -match '^(scripts|src|state|outputs|archive)\\' -or
                $vl -match '^d:\\us-tech-quant\\'
            ) {
                return $v
            }
        }
    }

    $all = Get-AllText $Row
    $m = [regex]::Match($all, '(D:\\us-tech-quant\\)?(scripts|src|state|outputs|archive)[\\/][^\s;,"<>|]+')

    if ($m.Success) {
        return Normalize-Rel $m.Value
    }

    return ""
}

function Get-RowPathCandidates {
    param($Row)

    $list = New-Object System.Collections.Generic.List[string]

    foreach ($p in $Row.PSObject.Properties) {
        if ($null -ne $p.Value) {
            $raw = "$($p.Value)"
            $norm = Normalize-Rel $raw
            $nl = $norm.ToLowerInvariant()

            if ($nl -match '^(scripts|src|state|outputs|archive)\\') {
                if (!$list.Contains($norm)) {
                    [void]$list.Add($norm)
                }
            }
        }
    }

    $all = Get-AllText $Row
    $matches = [regex]::Matches($all, '(D:\\us-tech-quant\\)?(scripts|src|state|outputs|archive)[\\/][^\s;,"<>|]+')

    foreach ($m in $matches) {
        $norm = Normalize-Rel $m.Value
        if (!$list.Contains($norm)) {
            [void]$list.Add($norm)
        }
    }

    return $list.ToArray()
}

function Get-GraphExistingCodeSet {
    param($Rows)

    $set = New-Object 'System.Collections.Generic.HashSet[string]' ([System.StringComparer]::OrdinalIgnoreCase)

    foreach ($r in $Rows) {
        $paths = Get-RowPathCandidates $r

        foreach ($p in $paths) {
            $pl = $p.ToLowerInvariant()

            if (
                $pl -match '^(scripts|src)\\' -and
                ($pl.EndsWith(".ps1") -or $pl.EndsWith(".py") -or $pl.EndsWith(".bat") -or $pl.EndsWith(".cmd"))
            ) {
                [void]$set.Add($p)
            }
        }
    }

    return $set
}

function Get-GraphText {
    param($Rows)

    $parts = New-Object System.Collections.Generic.List[string]

    foreach ($r in $Rows) {
        [void]$parts.Add((Get-AllText $r))
    }

    return ($parts.ToArray() -join "`n")
}

function Get-CandidateStatus {
    param(
        [string]$CandidateRel,
        [System.Collections.Generic.HashSet[string]]$RuntimeCodeSet,
        [string]$GraphText
    )

    $candidateNorm = Normalize-Rel $CandidateRel
    $candidateLeaf = Split-Path $candidateNorm -Leaf

    $existsNow = Test-Path (Join-Path $Root $candidateNorm)

    $directHit = $RuntimeCodeSet.Contains($candidateNorm)

    $escapedRel = [regex]::Escape($candidateNorm)
    $escapedLeaf = [regex]::Escape($candidateLeaf)

    $textRelHit = [regex]::IsMatch($GraphText, $escapedRel, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
    $textLeafHit = [regex]::IsMatch($GraphText, $escapedLeaf, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)

    if ($directHit -or $textRelHit -or $textLeafHit) {
        return [pscustomobject]@{
            ExistsNow = $existsNow
            RuntimeHit = "YES"
            RuntimeHitMode = if ($directHit) { "CODE_SET" } elseif ($textRelHit) { "GRAPH_TEXT_REL" } else { "GRAPH_TEXT_LEAF" }
            DeleteRecommendation = "DO_NOT_DELETE_RUNTIME_HIT"
            ArchiveRecommendation = "NO"
            Risk = "HIGH"
        }
    }

    if ($existsNow) {
        return [pscustomobject]@{
            ExistsNow = $existsNow
            RuntimeHit = "NO"
            RuntimeHitMode = "NONE"
            DeleteRecommendation = "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT"
            ArchiveRecommendation = "YES_ARCHIVE_FIRST_NOT_PERMANENT_DELETE"
            Risk = "MEDIUM"
        }
    }

    return [pscustomobject]@{
        ExistsNow = $existsNow
        RuntimeHit = "NO"
        RuntimeHitMode = "NONE"
        DeleteRecommendation = "ALREADY_MISSING_OR_ARCHIVED"
        ArchiveRecommendation = "NO_ACTION"
        Risk = "LOW"
    }
}

function Clean-Md {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    $x = $Value -replace '\|', '/'
    $x = $x -replace '\r?\n', ' '

    if ($x.Length -gt 260) {
        $x = $x.Substring(0, 260) + "..."
    }

    return $x
}

function Add-Table {
    param(
        [System.Text.StringBuilder]$Sb,
        $Rows,
        [string[]]$Cols
    )

    $arr = New-Object System.Collections.Generic.List[object]

    if ($null -ne $Rows) {
        if ($Rows -is [System.Collections.IEnumerable] -and -not ($Rows -is [string])) {
            foreach ($item in $Rows) {
                if ($null -ne $item) {
                    [void]$arr.Add($item)
                }
            }
        }
        else {
            [void]$arr.Add($Rows)
        }
    }

    if ($arr.Count -eq 0) {
        [void]$Sb.AppendLine("_none_")
        [void]$Sb.AppendLine("")
        return
    }

    [void]$Sb.AppendLine("| " + ($Cols -join " | ") + " |")
    [void]$Sb.AppendLine("|" + (($Cols | ForEach-Object { "---" }) -join "|") + "|")

    foreach ($r in $arr) {
        $vals = New-Object System.Collections.Generic.List[string]

        foreach ($c in $Cols) {
            $cell = ""

            if ($null -ne $r.PSObject -and $null -ne $r.PSObject.Properties) {
                $prop = $r.PSObject.Properties | Where-Object { $_.Name -eq $c } | Select-Object -First 1

                if ($null -ne $prop -and $null -ne $prop.Value) {
                    $cell = Clean-Md "$($prop.Value)"
                }
            }

            [void]$vals.Add($cell)
        }

        [void]$Sb.AppendLine("| " + (($vals.ToArray()) -join " | ") + " |")
    }

    [void]$Sb.AppendLine("")
}

$ClassifierRows = Import-Csv $ClassifierCsv
$GraphRows = Import-Csv $RuntimeGraphCsv

$RuntimeCodeSet = Get-GraphExistingCodeSet $GraphRows
$GraphText = Get-GraphText $GraphRows

$CandidateRows = $ClassifierRows |
    Where-Object { $_.Action -eq "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" }

$CandidateFiles = $CandidateRows |
    Select-Object -ExpandProperty SourceRel -Unique |
    Where-Object { $_ -and $_.Trim() -ne "" } |
    Sort-Object

$Results = New-Object System.Collections.Generic.List[object]

foreach ($candidate in $CandidateFiles) {
    $status = Get-CandidateStatus $candidate $RuntimeCodeSet $GraphText

    $classifierHitCount = @($CandidateRows | Where-Object { $_.SourceRel -eq $candidate }).Count

    [void]$Results.Add([pscustomobject]@{
        CandidateRel = $candidate
        ExistsNow = $status.ExistsNow
        ClassifierHitCount = $classifierHitCount
        RuntimeHit = $status.RuntimeHit
        RuntimeHitMode = $status.RuntimeHitMode
        DeleteRecommendation = $status.DeleteRecommendation
        ArchiveRecommendation = $status.ArchiveRecommendation
        Risk = $status.Risk
    })
}

$Results.ToArray() | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$TotalCandidates = $Results.Count
$RuntimeHitCount = @($Results | Where-Object { $_.RuntimeHit -eq "YES" }).Count
$ZeroRuntimeHitCount = @($Results | Where-Object { $_.DeleteRecommendation -eq "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT" }).Count
$MissingCount = @($Results | Where-Object { $_.DeleteRecommendation -eq "ALREADY_MISSING_OR_ARCHIVED" }).Count

$Summary = @(
    [pscustomobject]@{ Metric = "TOTAL_UNIQUE_CANDIDATE_FILES"; Value = $TotalCandidates },
    [pscustomobject]@{ Metric = "RUNTIME_HIT_COUNT"; Value = $RuntimeHitCount },
    [pscustomobject]@{ Metric = "ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT"; Value = $ZeroRuntimeHitCount },
    [pscustomobject]@{ Metric = "ALREADY_MISSING_OR_ARCHIVED_COUNT"; Value = $MissingCount }
)

$ArchiveCandidates = $Results |
    Where-Object { $_.DeleteRecommendation -eq "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT" } |
    Sort-Object CandidateRel

$RuntimeHits = $Results |
    Where-Object { $_.RuntimeHit -eq "YES" } |
    Sort-Object CandidateRel

$Missing = $Results |
    Where-Object { $_.DeleteRecommendation -eq "ALREADY_MISSING_OR_ARCHIVED" } |
    Sort-Object CandidateRel

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5B Delete Candidate Runtime Graph Audit")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_DELETE_CANDIDATE_RUNTIME_AUDIT_READY")
[void]$Sb.AppendLine("- CLASSIFIER_INPUT: $ClassifierCsv")
[void]$Sb.AppendLine("- RUNTIME_GRAPH_INPUT: $RuntimeGraphCsv")
[void]$Sb.AppendLine("- RULE: archive only files with zero runtime graph hit; do not permanently delete here.")
[void]$Sb.AppendLine("")

[void]$Sb.AppendLine("## 2. Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $Summary @("Metric", "Value")

[void]$Sb.AppendLine("## 3. Archive Candidates With Zero Runtime Hit")
[void]$Sb.AppendLine("")
Add-Table $Sb $ArchiveCandidates @("CandidateRel", "ExistsNow", "ClassifierHitCount", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 4. Runtime Hits - Do Not Delete")
[void]$Sb.AppendLine("")
Add-Table $Sb $RuntimeHits @("CandidateRel", "ExistsNow", "ClassifierHitCount", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 5. Already Missing Or Archived")
[void]$Sb.AppendLine("")
Add-Table $Sb $Missing @("CandidateRel", "ExistsNow", "ClassifierHitCount", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 6. Full Result")
[void]$Sb.AppendLine("")
Add-Table $Sb $Results @("CandidateRel", "ExistsNow", "ClassifierHitCount", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 7. Next Action")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("If ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT is greater than zero, next step is V18.5C archive-only move with restore manifest.")
[void]$Sb.AppendLine("After archive-only move, run V18.4J-R1 final daily read center wrapper again.")
[void]$Sb.AppendLine("Only after a successful full-chain validation should permanent deletion be considered.")
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$Read = @()
$Read += "V18_5B_STATUS: OK_DELETE_CANDIDATE_RUNTIME_AUDIT_READY"
$Read += "CLASSIFIER_INPUT: $ClassifierCsv"
$Read += "RUNTIME_GRAPH_INPUT: $RuntimeGraphCsv"
$Read += "CSV: $OutCsv"
$Read += "REPORT: $OutMd"
$Read += "TOTAL_UNIQUE_CANDIDATE_FILES: $TotalCandidates"
$Read += "RUNTIME_HIT_COUNT: $RuntimeHitCount"
$Read += "ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT: $ZeroRuntimeHitCount"
$Read += "ALREADY_MISSING_OR_ARCHIVED_COUNT: $MissingCount"
$Read += ""
$Read += "NEXT:"
$Read += "If archive candidates exist, run V18.5C archive-only cleanup, then validate V18.4J-R1."

$Read | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5B DELETE CANDIDATE RUNTIME GRAPH AUDIT READY ==="
Write-Host "TOTAL_UNIQUE_CANDIDATE_FILES:" $TotalCandidates
Write-Host "RUNTIME_HIT_COUNT:" $RuntimeHitCount
Write-Host "ZERO_RUNTIME_HIT_ARCHIVE_CANDIDATE_COUNT:" $ZeroRuntimeHitCount
Write-Host "ALREADY_MISSING_OR_ARCHIVED_COUNT:" $MissingCount
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host ""

Write-Host "=== ARCHIVE CANDIDATES ==="
$ArchiveCandidates | Format-Table -AutoSize

Write-Host ""
Write-Host "=== RUNTIME HITS - DO NOT DELETE ==="
$RuntimeHits | Format-Table -AutoSize

