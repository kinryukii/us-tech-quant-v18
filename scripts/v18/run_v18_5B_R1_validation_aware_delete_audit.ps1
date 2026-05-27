$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$InputCsv = Join-Path $Root "outputs\v18\ops\V18_5B_CURRENT_DELETE_CANDIDATE_RUNTIME_AUDIT.csv"

$OutDir = Join-Path $Root "outputs\v18\ops"
$OutCsv = Join-Path $OutDir "V18_5B_R1_CURRENT_VALIDATION_AWARE_DELETE_AUDIT.csv"
$OutMd = Join-Path $OutDir "V18_5B_R1_CURRENT_VALIDATION_AWARE_DELETE_AUDIT.md"
$ReadFirst = Join-Path $OutDir "V18_5B_R1_READ_FIRST.txt"

if (!(Test-Path $InputCsv)) {
    throw "MISSING INPUT CSV: $InputCsv"
}

$ProtectedDynamic = @(
    "scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1"
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
$Results = New-Object System.Collections.Generic.List[object]

foreach ($r in $Rows) {
    $rel = Normalize-Rel $r.CandidateRel
    $isProtected = $false

    foreach ($p in $ProtectedDynamic) {
        if ($rel.Equals((Normalize-Rel $p), [System.StringComparison]::OrdinalIgnoreCase)) {
            $isProtected = $true
            break
        }
    }

    $existsNow = Test-Path (Join-Path $Root $rel)

    if ($isProtected) {
        $deleteRecommendation = "DO_NOT_DELETE_PROTECTED_DYNAMIC_RUNTIME_DEPENDENCY"
        $archiveRecommendation = "NO_VALIDATION_FAILED_WHEN_ARCHIVED"
        $runtimeHit = "YES_DYNAMIC_PROTECTED"
        $runtimeHitMode = "FULL_CHAIN_VALIDATION"
        $risk = "HIGH"
        $validationNote = "V18.5C archive caused V18.4J-R1 failure through upstream V17.7G-R1; restored and full chain passed."
    }
    else {
        $deleteRecommendation = $r.DeleteRecommendation
        $archiveRecommendation = $r.ArchiveRecommendation
        $runtimeHit = $r.RuntimeHit
        $runtimeHitMode = $r.RuntimeHitMode
        $risk = $r.Risk
        $validationNote = ""
    }

    [void]$Results.Add([pscustomobject]@{
        CandidateRel = $rel
        ExistsNow = $existsNow
        ClassifierHitCount = $r.ClassifierHitCount
        RuntimeHit = $runtimeHit
        RuntimeHitMode = $runtimeHitMode
        DeleteRecommendation = $deleteRecommendation
        ArchiveRecommendation = $archiveRecommendation
        Risk = $risk
        ProtectedDynamic = $isProtected
        ValidationNote = $validationNote
    })
}

$Results.ToArray() | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$Total = $Results.Count
$ProtectedCount = @($Results | Where-Object { $_.ProtectedDynamic -eq $true }).Count
$RuntimeHitCount = @($Results | Where-Object { $_.RuntimeHit -like "YES*" }).Count
$ArchiveCandidateCount = @($Results | Where-Object { $_.DeleteRecommendation -eq "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT" }).Count
$DoNotDeleteCount = @($Results | Where-Object { $_.DeleteRecommendation -like "DO_NOT_DELETE*" }).Count

$Summary = @(
    [pscustomobject]@{ Metric = "TOTAL_UNIQUE_CANDIDATE_FILES"; Value = $Total },
    [pscustomobject]@{ Metric = "RUNTIME_OR_DYNAMIC_HIT_COUNT"; Value = $RuntimeHitCount },
    [pscustomobject]@{ Metric = "PROTECTED_DYNAMIC_DEPENDENCY_COUNT"; Value = $ProtectedCount },
    [pscustomobject]@{ Metric = "ZERO_RUNTIME_ARCHIVE_CANDIDATE_COUNT_AFTER_VALIDATION"; Value = $ArchiveCandidateCount },
    [pscustomobject]@{ Metric = "DO_NOT_DELETE_COUNT"; Value = $DoNotDeleteCount }
)

$ProtectedRows = $Results | Where-Object { $_.ProtectedDynamic -eq $true }
$ArchiveRows = $Results | Where-Object { $_.DeleteRecommendation -eq "ARCHIVE_CANDIDATE_ZERO_RUNTIME_HIT" }
$DoNotDeleteRows = $Results | Where-Object { $_.DeleteRecommendation -like "DO_NOT_DELETE*" }

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5B-R1 Validation-Aware Delete Audit")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_VALIDATION_AWARE_DELETE_AUDIT_READY")
[void]$Sb.AppendLine("- INPUT: $InputCsv")
[void]$Sb.AppendLine("- RULE: full-chain validation overrides static zero-runtime graph.")
[void]$Sb.AppendLine("- RESULT: current safe archive/delete candidate count should be zero.")
[void]$Sb.AppendLine("")

[void]$Sb.AppendLine("## 2. Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $Summary @("Metric", "Value")

[void]$Sb.AppendLine("## 3. Protected Dynamic Runtime Dependencies")
[void]$Sb.AppendLine("")
Add-Table $Sb $ProtectedRows @("CandidateRel", "ExistsNow", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk", "ValidationNote")

[void]$Sb.AppendLine("## 4. Remaining Archive Candidates")
[void]$Sb.AppendLine("")
Add-Table $Sb $ArchiveRows @("CandidateRel", "ExistsNow", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 5. Do Not Delete")
[void]$Sb.AppendLine("")
Add-Table $Sb $DoNotDeleteRows @("CandidateRel", "ExistsNow", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk")

[void]$Sb.AppendLine("## 6. Full Result")
[void]$Sb.AppendLine("")
Add-Table $Sb $Results @("CandidateRel", "ExistsNow", "RuntimeHit", "RuntimeHitMode", "DeleteRecommendation", "ArchiveRecommendation", "Risk", "ProtectedDynamic")

[void]$Sb.AppendLine("## 7. Next Action")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("No more archive/delete actions should be performed from this candidate set.")
[void]$Sb.AppendLine("Next safe cleanup direction is generated-output retention, not runtime code deletion.")
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$Read = @()
$Read += "V18_5B_R1_STATUS: OK_VALIDATION_AWARE_DELETE_AUDIT_READY"
$Read += "INPUT: $InputCsv"
$Read += "CSV: $OutCsv"
$Read += "REPORT: $OutMd"
$Read += "TOTAL_UNIQUE_CANDIDATE_FILES: $Total"
$Read += "RUNTIME_OR_DYNAMIC_HIT_COUNT: $RuntimeHitCount"
$Read += "PROTECTED_DYNAMIC_DEPENDENCY_COUNT: $ProtectedCount"
$Read += "ZERO_RUNTIME_ARCHIVE_CANDIDATE_COUNT_AFTER_VALIDATION: $ArchiveCandidateCount"
$Read += "DO_NOT_DELETE_COUNT: $DoNotDeleteCount"
$Read += "CONCLUSION: NO_MORE_RUNTIME_CODE_DELETE_CANDIDATES"

$Read | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5B-R1 VALIDATION-AWARE DELETE AUDIT READY ==="
Write-Host "TOTAL_UNIQUE_CANDIDATE_FILES:" $Total
Write-Host "RUNTIME_OR_DYNAMIC_HIT_COUNT:" $RuntimeHitCount
Write-Host "PROTECTED_DYNAMIC_DEPENDENCY_COUNT:" $ProtectedCount
Write-Host "ZERO_RUNTIME_ARCHIVE_CANDIDATE_COUNT_AFTER_VALIDATION:" $ArchiveCandidateCount
Write-Host "DO_NOT_DELETE_COUNT:" $DoNotDeleteCount
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host ""

Write-Host "=== PROTECTED DYNAMIC DEPENDENCIES ==="
$ProtectedRows | Format-Table -AutoSize

Write-Host ""
Write-Host "=== REMAINING ARCHIVE CANDIDATES ==="
$ArchiveRows | Format-Table -AutoSize
