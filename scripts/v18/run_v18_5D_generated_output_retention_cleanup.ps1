param(
    [switch]$Apply,
    [int]$KeepLatest = 3,
    [int]$KeepLogs = 10
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$OutDir = Join-Path $Root "outputs\v18\ops"
$OutCsv = Join-Path $OutDir "V18_5D_CURRENT_GENERATED_OUTPUT_RETENTION_CLEANUP.csv"
$OutMd = Join-Path $OutDir "V18_5D_CURRENT_GENERATED_OUTPUT_RETENTION_CLEANUP.md"
$ReadFirst = Join-Path $OutDir "V18_5D_READ_FIRST.txt"

$Mode = if ($Apply) { "APPLY" } else { "DRYRUN" }

$ScanRoots = @(
    (Join-Path -Path $Root -ChildPath "outputs\v18"),
    (Join-Path -Path $Root -ChildPath "state\v18")
)

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

function Is-ProtectedName {
    param([string]$Name)

    $n = $Name.ToUpperInvariant()

    if ($n -match "CURRENT") { return $true }
    if ($n -match "READ_FIRST") { return $true }
    if ($n -match "MANIFEST") { return $true }
    if ($n -match "RESTORE") { return $true }
    if ($n -match "STABLE") { return $true }
    if ($n -match "CHECKPOINT") { return $true }

    return $false
}

function Is-AllowedGeneratedFile {
    param([System.IO.FileInfo]$File)

    $rel = Normalize-Rel $File.FullName
    $rl = $rel.ToLowerInvariant()

    if ($rl.StartsWith("scripts\")) { return $false }
    if ($rl.StartsWith("src\")) { return $false }
    if ($rl.StartsWith("archive\")) { return $false }

    if (!($rl.StartsWith("outputs\v18\") -or $rl.StartsWith("state\v18\"))) {
        return $false
    }

    return $true
}

function Get-Category {
    param([System.IO.FileInfo]$File)

    $rel = Normalize-Rel $File.FullName
    $name = $File.Name
    $ext = $File.Extension.ToLowerInvariant()

    if ($rel.ToLowerInvariant().StartsWith("state\v18\") -and $name -match "WORLDQUANT_FACTOR_FORWARD_SNAPSHOT_[0-9]{8}_[0-9]{6}") {
        return "STATE_V18_FACTOR_FORWARD_TIMESTAMP_SNAPSHOT"
    }

    if ($rel.ToLowerInvariant().StartsWith("state\v18\") -and $name -match "[0-9]{8}_[0-9]{6}") {
        return "STATE_V18_TIMESTAMP_SNAPSHOT"
    }

    if ($rel.ToLowerInvariant().StartsWith("outputs\v18\") -and $ext -eq ".log") {
        return "OUTPUTS_V18_LOG"
    }

    if ($rel.ToLowerInvariant().StartsWith("outputs\v18\") -and $name -match "[0-9]{8}_[0-9]{6}") {
        return "OUTPUTS_V18_TIMESTAMP_OUTPUT"
    }

    if ($ext -eq ".tmp" -or $ext -eq ".bak") {
        return "TEMP_OR_BACKUP_FILE"
    }

    return "NO_RETENTION_PATTERN"
}

function Get-GroupKey {
    param(
        [System.IO.FileInfo]$File,
        [string]$Category
    )

    $rel = Normalize-Rel $File.FullName
    $dir = Normalize-Rel $File.DirectoryName
    $name = $File.Name

    if ($Category -eq "OUTPUTS_V18_LOG") {
        $base = $name -replace "[0-9]{8}_[0-9]{6}", "TIMESTAMP"
        return "$dir\$base"
    }

    if ($Category -eq "TEMP_OR_BACKUP_FILE") {
        return "$dir\TEMP_OR_BACKUP"
    }

    $base2 = $name -replace "[0-9]{8}_[0-9]{6}", "TIMESTAMP"
    return "$dir\$base2"
}

function Get-KeepCount {
    param([string]$Category)

    if ($Category -eq "OUTPUTS_V18_LOG") {
        return $KeepLogs
    }

    if ($Category -eq "TEMP_OR_BACKUP_FILE") {
        return 0
    }

    return $KeepLatest
}

function Clean-Md {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    $x = $Value -replace '\|','/'
    $x = $x -replace '\r?\n',' '

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
            $prop = $r.PSObject.Properties | Where-Object { $_.Name -eq $c } | Select-Object -First 1

            if ($null -ne $prop -and $null -ne $prop.Value) {
                $cell = Clean-Md "$($prop.Value)"
            }

            [void]$vals.Add($cell)
        }

        [void]$Sb.AppendLine("| " + (($vals.ToArray()) -join " | ") + " |")
    }

    [void]$Sb.AppendLine("")
}

$BaseItems = New-Object System.Collections.Generic.List[object]
$TotalScanned = 0
$ProtectedCount = 0
$NoPatternCount = 0

foreach ($scanRoot in $ScanRoots) {
    if (!(Test-Path $scanRoot)) {
        continue
    }

    $files = Get-ChildItem -Path $scanRoot -File -Recurse -Force -ErrorAction SilentlyContinue

    foreach ($f in $files) {
        $TotalScanned++

        if (!(Is-AllowedGeneratedFile $f)) {
            continue
        }

        if (Is-ProtectedName $f.Name) {
            $ProtectedCount++
            continue
        }

        $category = Get-Category $f

        if ($category -eq "NO_RETENTION_PATTERN") {
            $NoPatternCount++
            continue
        }

        $groupKey = Get-GroupKey $f $category

        [void]$BaseItems.Add([pscustomobject]@{
            RelPath = Normalize-Rel $f.FullName
            FullPath = $f.FullName
            DirectoryRel = Normalize-Rel $f.DirectoryName
            FileName = $f.Name
            Extension = $f.Extension.ToLowerInvariant()
            Category = $category
            GroupKey = $groupKey
            LastWriteTime = $f.LastWriteTime
            SizeBytes = $f.Length
        })
    }
}

$Results = New-Object System.Collections.Generic.List[object]

$Groups = $BaseItems.ToArray() | Group-Object GroupKey

foreach ($g in $Groups) {
    $sorted = $g.Group | Sort-Object LastWriteTime -Descending
    $rank = 0

    foreach ($item in $sorted) {
        $rank++
        $keepCount = Get-KeepCount $item.Category

        if ($rank -le $keepCount) {
            $decision = "KEEP_RETENTION_LATEST"
            $status = "KEPT"
            $sha = ""
        }
        else {
            $decision = if ($Apply) { "DELETE" } else { "DRYRUN_WOULD_DELETE" }
            $sha = ""

            if (Test-Path $item.FullPath) {
                try {
                    $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $item.FullPath).Hash
                }
                catch {
                    $sha = "HASH_FAIL"
                }
            }

            if ($Apply) {
                try {
                    Remove-Item -LiteralPath $item.FullPath -Force
                    $status = "DELETED"
                }
                catch {
                    $status = "DELETE_FAIL: $($_.Exception.Message)"
                }
            }
            else {
                $status = "DRYRUN"
            }
        }

        [void]$Results.Add([pscustomobject]@{
            RelPath = $item.RelPath
            Category = $item.Category
            GroupKey = $item.GroupKey
            RankNewestFirst = $rank
            KeepCount = $keepCount
            Decision = $decision
            Status = $status
            SizeBytes = $item.SizeBytes
            LastWriteTime = $item.LastWriteTime
            Sha256 = $sha
        })
    }
}

$Results.ToArray() | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$DeleteRows = $Results.ToArray() | Where-Object { $_.Decision -eq "DELETE" -or $_.Decision -eq "DRYRUN_WOULD_DELETE" }
$DeletedRows = $Results.ToArray() | Where-Object { $_.Status -eq "DELETED" }
$FailRows = $Results.ToArray() | Where-Object { $_.Status -like "DELETE_FAIL*" }
$KeptRows = $Results.ToArray() | Where-Object { $_.Decision -eq "KEEP_RETENTION_LATEST" }

$CandidateCount = ($DeleteRows | Measure-Object).Count
$DeletedCount = ($DeletedRows | Measure-Object).Count
$FailCount = ($FailRows | Measure-Object).Count
$KeptRetentionCount = ($KeptRows | Measure-Object).Count
$CandidateBytes = ($DeleteRows | Measure-Object -Property SizeBytes -Sum).Sum
if ($null -eq $CandidateBytes) { $CandidateBytes = 0 }

$CandidateMB = [math]::Round(($CandidateBytes / 1MB), 3)

$Summary = @(
    [pscustomobject]@{ Metric = "MODE"; Value = $Mode },
    [pscustomobject]@{ Metric = "TOTAL_FILES_SCANNED"; Value = $TotalScanned },
    [pscustomobject]@{ Metric = "MATCHED_RETENTION_ITEMS"; Value = $Results.Count },
    [pscustomobject]@{ Metric = "PROTECTED_BY_NAME_COUNT"; Value = $ProtectedCount },
    [pscustomobject]@{ Metric = "NO_RETENTION_PATTERN_COUNT"; Value = $NoPatternCount },
    [pscustomobject]@{ Metric = "KEEP_LATEST_PER_TIMESTAMP_GROUP"; Value = $KeepLatest },
    [pscustomobject]@{ Metric = "KEEP_LOGS_PER_LOG_GROUP"; Value = $KeepLogs },
    [pscustomobject]@{ Metric = "DELETE_CANDIDATE_COUNT"; Value = $CandidateCount },
    [pscustomobject]@{ Metric = "DELETE_CANDIDATE_MB"; Value = $CandidateMB },
    [pscustomobject]@{ Metric = "DELETED_COUNT"; Value = $DeletedCount },
    [pscustomobject]@{ Metric = "FAIL_COUNT"; Value = $FailCount }
)

$CategorySummary = $Results.ToArray() |
    Group-Object Category |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Category = $_.Name
            Count = $_.Count
        }
    }

$DecisionSummary = $Results.ToArray() |
    Group-Object Decision |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Decision = $_.Name
            Count = $_.Count
        }
    }

$TopDelete = $DeleteRows |
    Sort-Object SizeBytes -Descending |
    Select-Object -First 120 RelPath, Category, RankNewestFirst, KeepCount, Decision, Status, SizeBytes, LastWriteTime

$TopKept = $KeptRows |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 80 RelPath, Category, RankNewestFirst, KeepCount, Decision, Status, SizeBytes, LastWriteTime

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5D Generated Output Retention Cleanup")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_GENERATED_OUTPUT_RETENTION_CLEANUP_READY")
[void]$Sb.AppendLine("- MODE: $Mode")
[void]$Sb.AppendLine("- RULE: generated outputs/state only; scripts/src/archive are not scanned.")
[void]$Sb.AppendLine("- PROTECTED: CURRENT, READ_FIRST, MANIFEST, RESTORE, STABLE, CHECKPOINT.")
[void]$Sb.AppendLine("")

[void]$Sb.AppendLine("## 2. Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $Summary @("Metric", "Value")

[void]$Sb.AppendLine("## 3. Category Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $CategorySummary @("Category", "Count")

[void]$Sb.AppendLine("## 4. Decision Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $DecisionSummary @("Decision", "Count")

[void]$Sb.AppendLine("## 5. Delete Candidates")
[void]$Sb.AppendLine("")
Add-Table $Sb $TopDelete @("RelPath", "Category", "RankNewestFirst", "KeepCount", "Decision", "Status", "SizeBytes", "LastWriteTime")

[void]$Sb.AppendLine("## 6. Kept Latest Samples")
[void]$Sb.AppendLine("")
Add-Table $Sb $TopKept @("RelPath", "Category", "RankNewestFirst", "KeepCount", "Decision", "Status", "SizeBytes", "LastWriteTime")

[void]$Sb.AppendLine("## 7. Next Action")
[void]$Sb.AppendLine("")
if ($Apply) {
    [void]$Sb.AppendLine("Run V18.4J-R1 final daily read center wrapper to validate full chain after generated-output cleanup.")
    [void]$Sb.AppendLine("Then rerun this script in DryRun mode to confirm remaining candidate count is acceptable.")
}
else {
    [void]$Sb.AppendLine("Review DryRun delete candidates. If correct, rerun with -Apply.")
}
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$Read = @()
$Read += "V18_5D_STATUS: OK_GENERATED_OUTPUT_RETENTION_CLEANUP_READY"
$Read += "MODE: $Mode"
$Read += "CSV: $OutCsv"
$Read += "REPORT: $OutMd"
$Read += "TOTAL_FILES_SCANNED: $TotalScanned"
$Read += "MATCHED_RETENTION_ITEMS: $($Results.Count)"
$Read += "DELETE_CANDIDATE_COUNT: $CandidateCount"
$Read += "DELETE_CANDIDATE_MB: $CandidateMB"
$Read += "DELETED_COUNT: $DeletedCount"
$Read += "FAIL_COUNT: $FailCount"
$Read += "KEEP_LATEST_PER_TIMESTAMP_GROUP: $KeepLatest"
$Read += "KEEP_LOGS_PER_LOG_GROUP: $KeepLogs"

$Read | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5D GENERATED OUTPUT RETENTION CLEANUP READY ==="
Write-Host "MODE:" $Mode
Write-Host "TOTAL_FILES_SCANNED:" $TotalScanned
Write-Host "MATCHED_RETENTION_ITEMS:" $Results.Count
Write-Host "DELETE_CANDIDATE_COUNT:" $CandidateCount
Write-Host "DELETE_CANDIDATE_MB:" $CandidateMB
Write-Host "DELETED_COUNT:" $DeletedCount
Write-Host "FAIL_COUNT:" $FailCount
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host ""

Write-Host "=== DELETE CANDIDATES TOP ==="
$TopDelete | Format-Table -AutoSize

