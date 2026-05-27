param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$InputCsv = Join-Path $Root "outputs\v18\ops\V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.csv"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ArchiveRoot = Join-Path $Root "archive\deprecated\v18_5C_zero_runtime_archive_$Stamp"

$OutDir = Join-Path $Root "outputs\v18\ops"
$OutCsv = Join-Path $OutDir "V18_5C_CURRENT_ARCHIVE_ZERO_RUNTIME_CANDIDATES.csv"
$OutMd = Join-Path $OutDir "V18_5C_CURRENT_ARCHIVE_ZERO_RUNTIME_CANDIDATES.md"
$ReadFirst = Join-Path $OutDir "V18_5C_READ_FIRST.txt"

if (!(Test-Path $InputCsv)) {
    throw "MISSING INPUT CSV: $InputCsv. Run V18.5B first."
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

function Get-SafeDestPath {
    param(
        [string]$ArchiveRootValue,
        [string]$RelPath
    )

    $safeRel = Normalize-Rel $RelPath
    return Join-Path $ArchiveRootValue $safeRel
}

function Clean-Md {
    param([string]$Value)

    if ($null -eq $Value) {
        return ""
    }

    return (($Value -replace '\|','/') -replace '\r?\n',' ')
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

$Rows = Import-Csv $InputCsv

$Candidates = $Rows |
    Where-Object {
        $_.DeleteRecommendation -eq "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT" -and
        $_.ArchiveRecommendation -eq "YES_ARCHIVE_FIRST_NOT_PERMANENT_DELETE"
    }

$Results = New-Object System.Collections.Generic.List[object]

foreach ($c in $Candidates) {
    $rel = Normalize-Rel $c.CandidateRel

    if ([string]::IsNullOrWhiteSpace($rel)) {
        [void]$Results.Add([pscustomobject]@{
            CandidateRel = $rel
            SourcePath = ""
            ArchivePath = ""
            ExistsBefore = $false
            Action = if ($Apply) { "APPLY" } else { "DRYRUN" }
            Status = "SKIP_EMPTY_PATH"
            Sha256 = ""
            SizeBytes = ""
        })
        continue
    }

    if ($rel -notmatch '^(scripts|src)\\') {
        [void]$Results.Add([pscustomobject]@{
            CandidateRel = $rel
            SourcePath = ""
            ArchivePath = ""
            ExistsBefore = $false
            Action = if ($Apply) { "APPLY" } else { "DRYRUN" }
            Status = "SKIP_NOT_CODE_PATH"
            Sha256 = ""
            SizeBytes = ""
        })
        continue
    }

    $src = Join-Path $Root $rel
    $dst = Get-SafeDestPath $ArchiveRoot $rel

    $exists = Test-Path $src

    $sha = ""
    $size = ""

    if ($exists) {
        $file = Get-Item $src
        $size = $file.Length
        $sha = (Get-FileHash -Algorithm SHA256 $src).Hash
    }

    if (!$exists) {
        $status = "ALREADY_MISSING"
    }
    elseif ($Apply) {
        $dstDir = Split-Path $dst -Parent
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
        Move-Item -LiteralPath $src -Destination $dst -Force
        $status = "ARCHIVED"
    }
    else {
        $status = "DRYRUN_WOULD_ARCHIVE"
    }

    [void]$Results.Add([pscustomobject]@{
        CandidateRel = $rel
        SourcePath = $src
        ArchivePath = $dst
        ExistsBefore = $exists
        Action = if ($Apply) { "APPLY" } else { "DRYRUN" }
        Status = $status
        Sha256 = $sha
        SizeBytes = $size
    })
}

$Results.ToArray() | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$ArchivedCount = @($Results | Where-Object { $_.Status -eq "ARCHIVED" }).Count
$DryRunCount = @($Results | Where-Object { $_.Status -eq "DRYRUN_WOULD_ARCHIVE" }).Count
$MissingCount = @($Results | Where-Object { $_.Status -eq "ALREADY_MISSING" }).Count
$FailCount = @($Results | Where-Object { $_.Status -like "FAIL*" }).Count

$RestoreScript = Join-Path $ArchiveRoot "restore_v18_5C_zero_runtime_archive.ps1"

if ($Apply) {
    New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null

    $restoreLines = New-Object System.Collections.Generic.List[string]
    [void]$restoreLines.Add('$ErrorActionPreference = "Stop"')
    [void]$restoreLines.Add('$Root = "D:\us-tech-quant"')
    [void]$restoreLines.Add('$ArchiveRoot = "' + $ArchiveRoot + '"')
    [void]$restoreLines.Add('')

    foreach ($r in $Results) {
        if ($r.Status -eq "ARCHIVED") {
            $rel = $r.CandidateRel
            [void]$restoreLines.Add('$src = Join-Path $ArchiveRoot "' + $rel + '"')
            [void]$restoreLines.Add('$dst = Join-Path $Root "' + $rel + '"')
            [void]$restoreLines.Add('if (Test-Path $src) {')
            [void]$restoreLines.Add('    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null')
            [void]$restoreLines.Add('    Move-Item -LiteralPath $src -Destination $dst -Force')
            [void]$restoreLines.Add('    Write-Host "RESTORED: " $dst')
            [void]$restoreLines.Add('}')
            [void]$restoreLines.Add('')
        }
    }

    $restoreLines | Set-Content -Encoding UTF8 $RestoreScript
    [scriptblock]::Create((Get-Content $RestoreScript -Raw)) | Out-Null
}

$Summary = @(
    [pscustomobject]@{ Metric = "MODE"; Value = if ($Apply) { "APPLY" } else { "DRYRUN" } },
    [pscustomobject]@{ Metric = "CANDIDATE_COUNT"; Value = $Results.Count },
    [pscustomobject]@{ Metric = "DRYRUN_WOULD_ARCHIVE_COUNT"; Value = $DryRunCount },
    [pscustomobject]@{ Metric = "ARCHIVED_COUNT"; Value = $ArchivedCount },
    [pscustomobject]@{ Metric = "ALREADY_MISSING_COUNT"; Value = $MissingCount },
    [pscustomobject]@{ Metric = "FAIL_COUNT"; Value = $FailCount },
    [pscustomobject]@{ Metric = "ARCHIVE_ROOT"; Value = $ArchiveRoot },
    [pscustomobject]@{ Metric = "RESTORE_SCRIPT"; Value = if ($Apply) { $RestoreScript } else { "created only in Apply mode" } }
)

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5C Archive Zero-Runtime Candidates")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_ARCHIVE_ZERO_RUNTIME_CANDIDATES_READY")
[void]$Sb.AppendLine("- MODE: " + $(if ($Apply) { "APPLY" } else { "DRYRUN" }))
[void]$Sb.AppendLine("- INPUT: $InputCsv")
[void]$Sb.AppendLine("- RULE: archive-only; no permanent delete.")
[void]$Sb.AppendLine("")

[void]$Sb.AppendLine("## 2. Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $Summary @("Metric", "Value")

[void]$Sb.AppendLine("## 3. Results")
[void]$Sb.AppendLine("")
Add-Table $Sb $Results @("CandidateRel", "ExistsBefore", "Action", "Status", "SourcePath", "ArchivePath", "Sha256", "SizeBytes")

[void]$Sb.AppendLine("## 4. Next Action")
[void]$Sb.AppendLine("")
if ($Apply) {
    [void]$Sb.AppendLine("Run V18.4J-R1 final daily read center wrapper to validate full chain after archive.")
    [void]$Sb.AppendLine("If validation fails, use the restore script listed above.")
}
else {
    [void]$Sb.AppendLine("Review DryRun results. If correct, rerun this script with -Apply.")
}
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$Read = @()
$Read += "V18_5C_STATUS: OK_ARCHIVE_ZERO_RUNTIME_CANDIDATES_READY"
$Read += "MODE: " + $(if ($Apply) { "APPLY" } else { "DRYRUN" })
$Read += "INPUT: $InputCsv"
$Read += "CSV: $OutCsv"
$Read += "REPORT: $OutMd"
$Read += "CANDIDATE_COUNT: $($Results.Count)"
$Read += "DRYRUN_WOULD_ARCHIVE_COUNT: $DryRunCount"
$Read += "ARCHIVED_COUNT: $ArchivedCount"
$Read += "ALREADY_MISSING_COUNT: $MissingCount"
$Read += "FAIL_COUNT: $FailCount"
$Read += "ARCHIVE_ROOT: $ArchiveRoot"
$Read += "RESTORE_SCRIPT: " + $(if ($Apply) { $RestoreScript } else { "created only in Apply mode" })

$Read | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5C ARCHIVE ZERO-RUNTIME CANDIDATES READY ==="
Write-Host "MODE:" $(if ($Apply) { "APPLY" } else { "DRYRUN" })
Write-Host "CANDIDATE_COUNT:" $Results.Count
Write-Host "DRYRUN_WOULD_ARCHIVE_COUNT:" $DryRunCount
Write-Host "ARCHIVED_COUNT:" $ArchivedCount
Write-Host "ALREADY_MISSING_COUNT:" $MissingCount
Write-Host "FAIL_COUNT:" $FailCount
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host "ARCHIVE_ROOT:" $ArchiveRoot
if ($Apply) {
    Write-Host "RESTORE_SCRIPT:" $RestoreScript
}
Write-Host ""

$Results | Format-Table -AutoSize
