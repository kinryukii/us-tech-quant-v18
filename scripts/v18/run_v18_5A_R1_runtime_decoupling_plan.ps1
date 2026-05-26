$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$InputCsv = Join-Path $Root "outputs\v18\ops\V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv"
$OutDir = Join-Path $Root "outputs\v18\ops"

$OutCsv = Join-Path $OutDir "V18_5A_R1_CURRENT_RUNTIME_DECOUPLING_PLAN.csv"
$OutMd  = Join-Path $OutDir "V18_5A_R1_CURRENT_RUNTIME_DECOUPLING_PLAN.md"
$ReadFirst = Join-Path $OutDir "V18_5A_R1_READ_FIRST.txt"

if (!(Test-Path $InputCsv)) {
    throw "MISSING INPUT CSV: $InputCsv. Run V18.5A audit first."
}

function Get-FirstPropValue {
    param($Row, [string[]]$Names)

    foreach ($n in $Names) {
        $p = $Row.PSObject.Properties[$n]
        if ($null -ne $p -and $null -ne $p.Value -and "$($p.Value)".Trim() -ne "") {
            return "$($p.Value)"
        }
    }

    foreach ($prop in $Row.PSObject.Properties) {
        foreach ($n in $Names) {
            if ($prop.Name -match [regex]::Escape($n)) {
                if ($null -ne $prop.Value -and "$($prop.Value)".Trim() -ne "") {
                    return "$($prop.Value)"
                }
            }
        }
    }

    return ""
}

function Get-AllText {
    param($Row)

    $parts = New-Object System.Collections.Generic.List[string]

    foreach ($p in $Row.PSObject.Properties) {
        if ($null -ne $p.Value) {
            $parts.Add("$($p.Name)=$($p.Value)")
        }
    }

    return ($parts -join " | ")
}

function Get-SourcePath {
    param($Row)

    $source = Get-FirstPropValue $Row @(
        "source_file",
        "source_path",
        "SourceFile",
        "SourcePath",
        "File",
        "FilePath",
        "Path",
        "Script",
        "ScriptPath"
    )

    if ($source.Trim() -ne "") {
        return $source
    }

    $all = Get-AllText $Row
    $m = [regex]::Match($all, 'D:\\us-tech-quant\\[^\s;,"<>]+')

    if ($m.Success) {
        return $m.Value
    }

    return "UNKNOWN_SOURCE"
}

function Get-ReferenceText {
    param($Row)

    $ref = Get-FirstPropValue $Row @(
        "reference",
        "Reference",
        "ReferencePath",
        "TargetPath",
        "MatchedText",
        "Match",
        "LineText",
        "Text",
        "RawText"
    )

    if ($ref.Trim() -ne "") {
        return $ref
    }

    return Get-AllText $Row
}

function To-Rel {
    param([string]$PathValue)

    if ([string]::IsNullOrWhiteSpace($PathValue)) {
        return "UNKNOWN"
    }

    $prefix = $Root + "\"

    if ($PathValue.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $PathValue.Substring($prefix.Length)
    }

    return $PathValue
}

function Get-SourceZone {
    param([string]$Source)

    $s = $Source.ToLowerInvariant()

    if ($s -match '\\archive\\') { return "ARCHIVE" }
    if ($s -match '\\outputs\\') { return "GENERATED_OUTPUT" }
    if ($s -match '\\state\\') { return "STATE_FILE" }
    if ($s -match '\\scripts\\v18\\') { return "CURRENT_V18_CODE" }
    if ($s -match '\\scripts\\internal\\') { return "INTERNAL_SCRIPT" }
    if ($s -match '\\scripts\\') { return "ROOT_SCRIPT" }

    return "UNKNOWN"
}

function Get-Family {
    param([string]$Text)

    $t = $Text.ToLowerInvariant()

    if ($t -match '\\archive\\stable\\') { return "ARCHIVE_STABLE" }
    if ($t -match '\\archive\\deprecated\\') { return "ARCHIVE_DEPRECATED" }

    if (
        $t -match 'run_v18_3c_r1_factor_shadow_daily_quiet_wrapper\.ps1' -or
        $t -match 'run_v18_3c_r1_factor_shadow_quiet_wrapper\.ps1'
    ) {
        return "OLD_V18_3C_FALLBACK_WRAPPER"
    }

    if (
        $t -match 'v17_2_base_official_daily_path\.txt' -or
        $t -match 'v17_4_base_official_daily_path\.txt'
    ) {
        return "DYNAMIC_STATE_BRIDGE"
    }

    if (
        $t -match 'state\\v16\\event_calendar\.csv' -or
        $t -match 'state/v16/event_calendar\.csv'
    ) {
        return "V16_EVENT_CALENDAR_COMPAT"
    }

    if ($t -match '\\scripts\\run_v16' -or $t -match 'scripts/run_v16') { return "V16_ROOT_SCRIPT" }
    if ($t -match '\\scripts\\run_v17' -or $t -match 'scripts/run_v17') { return "V17_ROOT_SCRIPT" }

    if ($t -match '\\scripts\\v17\\' -or $t -match 'scripts/v17/') { return "V17_SCRIPT_DIR" }

    if ($t -match '\\outputs\\v16\\' -or $t -match 'outputs/v16/') { return "V16_OUTPUT" }
    if ($t -match '\\outputs\\v17\\' -or $t -match 'outputs/v17/') { return "V17_OUTPUT" }

    if ($t -match '\\state\\v16\\' -or $t -match 'state/v16/') { return "V16_STATE" }
    if ($t -match '\\state\\v17\\' -or $t -match 'state/v17/') { return "V17_STATE" }

    if ($t -match 'v16') { return "V16_TEXT_REFERENCE" }
    if ($t -match 'v17') { return "V17_TEXT_REFERENCE" }

    return "OTHER"
}

function Get-Action {
    param(
        [string]$SourceZone,
        [string]$Family,
        [string]$Text
    )

    if (
        $SourceZone -eq "ARCHIVE" -or
        $Family -eq "ARCHIVE_STABLE" -or
        $Family -eq "ARCHIVE_DEPRECATED"
    ) {
        return "IGNORE_ARCHIVE_REFERENCE"
    }

    if ($SourceZone -eq "GENERATED_OUTPUT") {
        return "IGNORE_GENERATED_REPORT_REFERENCE"
    }

    if (
        $Family -eq "DYNAMIC_STATE_BRIDGE" -or
        $Family -eq "V16_EVENT_CALENDAR_COMPAT"
    ) {
        return "KEEP_PROTECTED_COMPAT_BRIDGE"
    }

    if ($Family -eq "OLD_V18_3C_FALLBACK_WRAPPER") {
        return "PATCH_TO_CURRENT_V18_WRAPPER"
    }

    if (
        $SourceZone -eq "CURRENT_V18_CODE" -and
        (
            $Family -eq "V16_ROOT_SCRIPT" -or
            $Family -eq "V17_ROOT_SCRIPT" -or
            $Family -eq "V17_SCRIPT_DIR"
        )
    ) {
        return "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY"
    }

    if (
        $SourceZone -eq "CURRENT_V18_CODE" -and
        (
            $Family -eq "V16_OUTPUT" -or
            $Family -eq "V17_OUTPUT" -or
            $Family -eq "V16_STATE" -or
            $Family -eq "V17_STATE"
        )
    ) {
        return "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION"
    }

    if (
        ($SourceZone -eq "ROOT_SCRIPT" -or $SourceZone -eq "INTERNAL_SCRIPT") -and
        (
            $Family -eq "V16_ROOT_SCRIPT" -or
            $Family -eq "V17_ROOT_SCRIPT" -or
            $Family -eq "V17_SCRIPT_DIR" -or
            $Family -eq "V16_OUTPUT" -or
            $Family -eq "V17_OUTPUT" -or
            $Family -eq "V16_STATE" -or
            $Family -eq "V17_STATE"
        )
    ) {
        return "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT"
    }

    if (
        $Family -eq "V16_TEXT_REFERENCE" -or
        $Family -eq "V17_TEXT_REFERENCE"
    ) {
        return "TEXT_REFERENCE_REVIEW_LOW_PRIORITY"
    }

    return "MANUAL_REVIEW"
}

function Get-Risk {
    param([string]$Action)

    switch ($Action) {
        "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" { return "HIGH" }
        "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" { return "MEDIUM" }
        "PATCH_TO_CURRENT_V18_WRAPPER" { return "MEDIUM" }
        "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" { return "MEDIUM" }
        "KEEP_PROTECTED_COMPAT_BRIDGE" { return "KEEP" }
        "IGNORE_ARCHIVE_REFERENCE" { return "LOW_IGNORE" }
        "IGNORE_GENERATED_REPORT_REFERENCE" { return "LOW_IGNORE" }
        "TEXT_REFERENCE_REVIEW_LOW_PRIORITY" { return "LOW" }
        default { return "REVIEW" }
    }
}

function Get-DeletePermission {
    param([string]$Action)

    switch ($Action) {
        "IGNORE_ARCHIVE_REFERENCE" { return "NO_ACTION_FROM_RUNTIME" }
        "IGNORE_GENERATED_REPORT_REFERENCE" { return "NO_ACTION_FROM_RUNTIME" }
        "KEEP_PROTECTED_COMPAT_BRIDGE" { return "NO_KEEP" }
        "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" { return "NO_PATCH_FIRST" }
        "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" { return "NO_PATCH_FIRST" }
        "PATCH_TO_CURRENT_V18_WRAPPER" { return "NO_PATCH_FIRST" }
        "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" { return "MAYBE_AFTER_ZERO_RUNTIME_HIT" }
        default { return "REVIEW_FIRST" }
    }
}

function Get-DecouplingTarget {
    param(
        [string]$Action,
        [string]$Family
    )

    switch ($Action) {
        "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" {
            return "Replace direct V16/V17 script calls with V18 canonical wrapper or compatibility shim."
        }
        "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" {
            return "Move direct V16/V17 output/state reads behind V18 current aliases or one compatibility layer."
        }
        "PATCH_TO_CURRENT_V18_WRAPPER" {
            return "Patch obsolete V18.3C fallback wrapper names to run_v18_3C_factor_shadow_daily_wrapper.ps1."
        }
        "KEEP_PROTECTED_COMPAT_BRIDGE" {
            return "Keep for now; this is a known compatibility bridge."
        }
        "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" {
            return "Candidate for archive/delete only after V18 runtime graph confirms zero current dependency."
        }
        "IGNORE_ARCHIVE_REFERENCE" {
            return "Ignore for active runtime cleanup; archive content is historical."
        }
        "IGNORE_GENERATED_REPORT_REFERENCE" {
            return "Ignore for code cleanup; generated report text can be overwritten by retention policy."
        }
        default {
            return "Manual review."
        }
    }
}

function Clean-Md {
    param([string]$s)

    if ($null -eq $s) {
        return ""
    }

    return (($s -replace '\|','/') -replace '\r?\n',' ')
}

function Add-Table {
    param(
        [System.Text.StringBuilder]$Sb,
        $Rows,
        [string[]]$Cols
    )

    $arr = New-Object System.Collections.Generic.List[object]

    if ($null -ne $Rows) {
        foreach ($item in @($Rows)) {
            if ($null -ne $item) {
                [void]$arr.Add($item)
            }
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
        if ($null -eq $r) {
            continue
        }

        $vals = New-Object System.Collections.Generic.List[string]

        foreach ($c in $Cols) {
            $cell = ""

            if ($null -ne $r.PSObject -and $null -ne $r.PSObject.Properties) {
                $prop = $r.PSObject.Properties | Where-Object { $_.Name -eq $c } | Select-Object -First 1

                if ($null -ne $prop -and $null -ne $prop.Value) {
                    $cell = Clean-Md ([string]$prop.Value)
                }
            }

            [void]$vals.Add($cell)
        }

        [void]$Sb.AppendLine("| " + (($vals.ToArray()) -join " | ") + " |")
    }

    [void]$Sb.AppendLine("")
}

$Rows = Import-Csv $InputCsv

$Plan = New-Object System.Collections.Generic.List[object]

foreach ($r in $Rows) {
    $source = Get-SourcePath $r
    $refText = Get-ReferenceText $r
    $all = Get-AllText $r
    $combined = "$source | $refText | $all"

    $sourceZone = Get-SourceZone $source
    $family = Get-Family $combined
    $action = Get-Action $sourceZone $family $combined
    $risk = Get-Risk $action
    $deletePermission = Get-DeletePermission $action
    $target = Get-DecouplingTarget $action $family

    $line = Get-FirstPropValue $r @(
        "line",
        "Line",
        "LineNumber",
        "line_number",
        "Row",
        "RowNumber"
    )

    $Plan.Add([pscustomobject]@{
        SourcePath = $source
        SourceRel = To-Rel $source
        SourceZone = $sourceZone
        Line = $line
        Family = $family
        Action = $action
        Risk = $risk
        DeletePermission = $deletePermission
        DecouplingTarget = $target
        ReferenceText = $refText
    })
}

$Plan | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$TotalRows = $Plan.Count

$ActionSummary = $Plan |
    Group-Object Action |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Action = $_.Name
            Count = $_.Count
        }
    }

$FamilySummary = $Plan |
    Group-Object Family |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Family = $_.Name
            Count = $_.Count
        }
    }

$ZoneSummary = $Plan |
    Group-Object SourceZone |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            SourceZone = $_.Name
            Count = $_.Count
        }
    }

$TopFiles = $Plan |
    Group-Object SourceRel |
    Sort-Object Count -Descending |
    Select-Object -First 30 |
    ForEach-Object {
        [pscustomobject]@{
            SourceRel = $_.Name
            Count = $_.Count
        }
    }

$HardDeps = $Plan |
    Where-Object { $_.Action -eq "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" } |
    Select-Object -First 80 SourceRel, Line, Family, Action, ReferenceText

$AbstractionDeps = $Plan |
    Where-Object { $_.Action -eq "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" } |
    Select-Object -First 80 SourceRel, Line, Family, Action, ReferenceText

$PatchWrappers = $Plan |
    Where-Object { $_.Action -eq "PATCH_TO_CURRENT_V18_WRAPPER" } |
    Select-Object -First 80 SourceRel, Line, Family, Action, ReferenceText

$LegacyRootCandidates = $Plan |
    Where-Object { $_.Action -eq "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" } |
    Select-Object -First 80 SourceRel, Line, Family, Action, ReferenceText

$Protected = $Plan |
    Where-Object { $_.Action -eq "KEEP_PROTECTED_COMPAT_BRIDGE" } |
    Select-Object -First 80 SourceRel, Line, Family, Action, ReferenceText

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5A-R1 Runtime Decoupling Plan")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_DECOUPLING_PLAN_READY")
[void]$Sb.AppendLine("- INPUT: $InputCsv")
[void]$Sb.AppendLine("- TOTAL_ROWS_CLASSIFIED: $TotalRows")
[void]$Sb.AppendLine("- PURPOSE: classify legacy runtime references before delete/archive/patch decisions.")
[void]$Sb.AppendLine("")

[void]$Sb.AppendLine("## 2. Action Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $ActionSummary @("Action", "Count")

[void]$Sb.AppendLine("## 3. Family Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $FamilySummary @("Family", "Count")

[void]$Sb.AppendLine("## 4. Source Zone Summary")
[void]$Sb.AppendLine("")
Add-Table $Sb $ZoneSummary @("SourceZone", "Count")

[void]$Sb.AppendLine("## 5. Top Files By Legacy Reference Count")
[void]$Sb.AppendLine("")
Add-Table $Sb $TopFiles @("SourceRel", "Count")

[void]$Sb.AppendLine("## 6. High Priority: Direct Legacy Script Dependencies")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("These should be patched before any delete action.")
[void]$Sb.AppendLine("")
Add-Table $Sb $HardDeps @("SourceRel", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 7. Medium Priority: Output/State Abstraction Dependencies")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("These should move behind V18 current aliases or a single compatibility shim.")
[void]$Sb.AppendLine("")
Add-Table $Sb $AbstractionDeps @("SourceRel", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 8. Wrapper Name Patch Candidates")
[void]$Sb.AppendLine("")
Add-Table $Sb $PatchWrappers @("SourceRel", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 9. Legacy Root Script Candidates")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("These are not approved for deletion yet. They become delete/archive candidates only after runtime graph says zero current dependency.")
[void]$Sb.AppendLine("")
Add-Table $Sb $LegacyRootCandidates @("SourceRel", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 10. Protected Compatibility Bridges")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Keep these unless upstream runtime is rewritten.")
[void]$Sb.AppendLine("")
Add-Table $Sb $Protected @("SourceRel", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 11. Next Action")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Recommended next step:")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("1. Patch only V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY and PATCH_TO_CURRENT_V18_WRAPPER first.")
[void]$Sb.AppendLine("2. Do not delete protected compatibility bridges.")
[void]$Sb.AppendLine("3. Re-run V18.4J-R1 final daily read center wrapper.")
[void]$Sb.AppendLine("4. Re-run V18.5A audit and this V18.5A-R1 plan.")
[void]$Sb.AppendLine("5. Only then consider archive/delete candidates.")
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$ReadText = @()
$ReadText += "V18_5A_R1_STATUS: OK_DECOUPLING_PLAN_READY"
$ReadText += "INPUT: $InputCsv"
$ReadText += "CSV: $OutCsv"
$ReadText += "REPORT: $OutMd"
$ReadText += ""
$ReadText += "READ THIS FIRST:"
$ReadText += $OutMd
$ReadText += ""
$ReadText += "NEXT:"
$ReadText += "Patch direct legacy script dependencies first. Do not delete yet."

$ReadText | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5A-R1 RUNTIME DECOUPLING PLAN READY ==="
Write-Host "TOTAL_ROWS_CLASSIFIED:" $TotalRows
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host ""


