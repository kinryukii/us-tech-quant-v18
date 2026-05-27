$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$InputCsv = Join-Path $Root "outputs\v18\ops\V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv"
$OutDir = Join-Path $Root "outputs\v18\ops"

$OutCsv = Join-Path $OutDir "V18_5A_R2_CURRENT_RUNTIME_DECOUPLING_CLASSIFIER.csv"
$OutMd = Join-Path $OutDir "V18_5A_R2_CURRENT_RUNTIME_DECOUPLING_CLASSIFIER.md"
$ReadFirst = Join-Path $OutDir "V18_5A_R2_READ_FIRST.txt"

if (!(Test-Path $InputCsv)) {
    throw "MISSING INPUT CSV: $InputCsv"
}

function Normalize-PathText {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ""
    }

    $p = $Value.Trim()
    $p = $p.Trim('"')
    $p = $p.Trim("'")
    $p = $p -replace '/', '\'

    $rootPrefix = $Root + "\"

    if ($p.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        $p = $p.Substring($rootPrefix.Length)
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

function Get-ValueByNames {
    param(
        $Row,
        [string[]]$Names
    )

    foreach ($name in $Names) {
        $prop = $Row.PSObject.Properties | Where-Object { $_.Name -eq $name } | Select-Object -First 1
        if ($null -ne $prop -and $null -ne $prop.Value -and "$($prop.Value)".Trim() -ne "") {
            return "$($prop.Value)"
        }
    }

    foreach ($prop in $Row.PSObject.Properties) {
        foreach ($name in $Names) {
            if ($prop.Name.ToLowerInvariant().Contains($name.ToLowerInvariant())) {
                if ($null -ne $prop.Value -and "$($prop.Value)".Trim() -ne "") {
                    return "$($prop.Value)"
                }
            }
        }
    }

    return ""
}

function Looks-Like-ProjectPath {
    param([string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }

    $v = Normalize-PathText $Value
    $vl = $v.ToLowerInvariant()

    if ($vl -match '^(scripts|src|state|outputs|archive)\\') {
        return $true
    }

    if ($vl -match 'd:\\us-tech-quant\\') {
        return $true
    }

    return $false
}

function Get-SourcePath {
    param($Row)

    $direct = Get-ValueByNames $Row @(
        "SourceRel",
        "SourcePath",
        "SourceFile",
        "Source",
        "source_file",
        "source_path",
        "file",
        "File",
        "FilePath",
        "Path",
        "Script",
        "ScriptPath"
    )

    if (Looks-Like-ProjectPath $direct) {
        return Normalize-PathText $direct
    }

    foreach ($p in $Row.PSObject.Properties) {
        if (Looks-Like-ProjectPath "$($p.Value)") {
            return Normalize-PathText "$($p.Value)"
        }
    }

    $all = Get-AllText $Row
    $m = [regex]::Match($all, '(D:\\us-tech-quant\\)?(scripts|src|state|outputs|archive)[\\/][^\s;,"<>|]+')
    if ($m.Success) {
        return Normalize-PathText $m.Value
    }

    return "UNKNOWN_SOURCE"
}

function Get-ReferenceText {
    param($Row)

    $ref = Get-ValueByNames $Row @(
        "ReferenceText",
        "Reference",
        "ReferencePath",
        "TargetPath",
        "MatchedText",
        "Match",
        "Pattern",
        "LineText",
        "RawText",
        "Text"
    )

    if ($ref.Trim() -ne "") {
        return "$ref"
    }

    return Get-AllText $Row
}

function Get-LineNumber {
    param($Row)

    return Get-ValueByNames $Row @(
        "Line",
        "line",
        "LineNumber",
        "line_number",
        "Row",
        "RowNumber"
    )
}

function Get-SourceZone {
    param([string]$SourceRel)

    $s = Normalize-PathText $SourceRel
    $sl = $s.ToLowerInvariant()

    if ($sl -eq "unknown_source") { return "UNKNOWN" }

    if ($sl.StartsWith("archive\")) { return "ARCHIVE" }
    if ($sl.StartsWith("outputs\")) { return "GENERATED_OUTPUT" }
    if ($sl.StartsWith("state\")) { return "STATE_FILE" }

    if ($sl.StartsWith("scripts\v18\")) { return "CURRENT_V18_CODE" }
    if ($sl.StartsWith("src\v18\")) { return "CURRENT_V18_CODE" }
    if ($sl.StartsWith("src\qutumn\")) { return "CURRENT_QUTUMN_CODE" }

    if ($sl -match '^scripts\\run_v18') { return "CURRENT_V18_ROOT_SCRIPT" }
    if ($sl -match '^scripts\\run_v17') { return "LEGACY_V17_ROOT_SCRIPT" }
    if ($sl -match '^scripts\\run_v16') { return "LEGACY_V16_ROOT_SCRIPT" }

    if ($sl.StartsWith("scripts\internal\")) { return "INTERNAL_SCRIPT" }
    if ($sl.StartsWith("scripts\")) { return "ROOT_SCRIPT" }
    if ($sl.StartsWith("src\")) { return "SRC_CODE" }

    return "UNKNOWN"
}

function Get-Family {
    param(
        [string]$SourceRel,
        [string]$Text
    )

    $s = Normalize-PathText $SourceRel
    $sl = $s.ToLowerInvariant()
    $t = "$SourceRel | $Text"
    $tl = ($t -replace '/', '\').ToLowerInvariant()

    if ($sl -match 'run_v18_5a_runtime_decoupling_audit\.ps1') {
        return "SELF_AUDIT_SCRIPT"
    }

    if ($sl.StartsWith("state\v18\") -and $sl -match 'worldquant_factor_forward_snapshot') {
        return "V18_GENERATED_FACTOR_FORWARD_STATE"
    }

    if ($sl.StartsWith("state\v18\")) {
        return "V18_STATE_DATA"
    }

    if ($sl.StartsWith("outputs\v18\")) {
        return "V18_GENERATED_OUTPUT"
    }

    if ($tl -match '\\archive\\stable\\' -or $tl -match '^archive\\stable\\') {
        return "ARCHIVE_STABLE"
    }

    if ($tl -match '\\archive\\deprecated\\' -or $tl -match '^archive\\deprecated\\') {
        return "ARCHIVE_DEPRECATED"
    }

    if (
        $tl -match 'run_v18_3c_r1_factor_shadow_daily_quiet_wrapper\.ps1' -or
        $tl -match 'run_v18_3c_r1_factor_shadow_quiet_wrapper\.ps1'
    ) {
        return "OLD_V18_3C_FALLBACK_WRAPPER"
    }

    if (
        $tl -match 'v17_2_base_official_daily_path\.txt' -or
        $tl -match 'v17_4_base_official_daily_path\.txt'
    ) {
        return "DYNAMIC_STATE_BRIDGE"
    }

    if ($tl -match 'state\\v16\\event_calendar\.csv') {
        return "V16_EVENT_CALENDAR_COMPAT"
    }

    if ($tl -match 'scripts\\run_v16[^\\]*\.(ps1|py|bat|cmd)') {
        return "V16_ROOT_SCRIPT"
    }

    if ($tl -match 'scripts\\run_v17[^\\]*\.(ps1|py|bat|cmd)') {
        return "V17_ROOT_SCRIPT"
    }

    if ($tl -match 'scripts\\v17\\') {
        return "V17_SCRIPT_DIR"
    }

    if ($tl -match 'outputs\\v16\\') {
        return "V16_OUTPUT"
    }

    if ($tl -match 'outputs\\v17\\') {
        return "V17_OUTPUT"
    }

    if ($tl -match 'state\\v16\\') {
        return "V16_STATE"
    }

    if ($tl -match 'state\\v17\\') {
        return "V17_STATE"
    }

    if ($tl -match '\bv16[._ -]') {
        return "V16_TEXT_REFERENCE"
    }

    if ($tl -match '\bv17[._ -]') {
        return "V17_TEXT_REFERENCE"
    }

    return "OTHER"
}

function Get-Action {
    param(
        [string]$SourceZone,
        [string]$Family
    )

    if ($Family -eq "SELF_AUDIT_SCRIPT") {
        return "IGNORE_SELF_AUDIT_DEFINITION"
    }

    if ($SourceZone -eq "ARCHIVE" -or $Family -eq "ARCHIVE_STABLE" -or $Family -eq "ARCHIVE_DEPRECATED") {
        return "IGNORE_ARCHIVE_REFERENCE"
    }

    if ($SourceZone -eq "GENERATED_OUTPUT" -or $Family -eq "V18_GENERATED_OUTPUT") {
        return "IGNORE_GENERATED_OUTPUT_REFERENCE"
    }

    if ($SourceZone -eq "STATE_FILE" -or $Family -eq "V18_GENERATED_FACTOR_FORWARD_STATE" -or $Family -eq "V18_STATE_DATA") {
        return "IGNORE_STATE_DATA_REFERENCE"
    }

    if ($Family -eq "DYNAMIC_STATE_BRIDGE" -or $Family -eq "V16_EVENT_CALENDAR_COMPAT") {
        return "KEEP_PROTECTED_COMPAT_BRIDGE"
    }

    if ($Family -eq "OLD_V18_3C_FALLBACK_WRAPPER") {
        return "PATCH_TO_CURRENT_V18_WRAPPER"
    }

    if (
        ($SourceZone -eq "CURRENT_V18_CODE" -or $SourceZone -eq "CURRENT_V18_ROOT_SCRIPT" -or $SourceZone -eq "CURRENT_QUTUMN_CODE") -and
        ($Family -eq "V16_ROOT_SCRIPT" -or $Family -eq "V17_ROOT_SCRIPT" -or $Family -eq "V17_SCRIPT_DIR")
    ) {
        return "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY"
    }

    if (
        ($SourceZone -eq "CURRENT_V18_CODE" -or $SourceZone -eq "CURRENT_V18_ROOT_SCRIPT" -or $SourceZone -eq "CURRENT_QUTUMN_CODE") -and
        ($Family -eq "V16_OUTPUT" -or $Family -eq "V17_OUTPUT" -or $Family -eq "V16_STATE" -or $Family -eq "V17_STATE")
    ) {
        return "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION"
    }

    if (
        ($SourceZone -eq "LEGACY_V16_ROOT_SCRIPT" -or $SourceZone -eq "LEGACY_V17_ROOT_SCRIPT" -or $SourceZone -eq "ROOT_SCRIPT" -or $SourceZone -eq "INTERNAL_SCRIPT") -and
        ($Family -eq "V16_ROOT_SCRIPT" -or $Family -eq "V17_ROOT_SCRIPT" -or $Family -eq "V16_OUTPUT" -or $Family -eq "V17_OUTPUT" -or $Family -eq "V16_STATE" -or $Family -eq "V17_STATE")
    ) {
        return "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT"
    }

    if ($Family -eq "V16_TEXT_REFERENCE" -or $Family -eq "V17_TEXT_REFERENCE") {
        return "TEXT_REFERENCE_REVIEW_LOW_PRIORITY"
    }

    return "MANUAL_REVIEW"
}

function Get-DeletePermission {
    param([string]$Action)

    switch ($Action) {
        "IGNORE_SELF_AUDIT_DEFINITION" { return "NO_ACTION" }
        "IGNORE_ARCHIVE_REFERENCE" { return "NO_ACTION" }
        "IGNORE_GENERATED_OUTPUT_REFERENCE" { return "NO_ACTION" }
        "IGNORE_STATE_DATA_REFERENCE" { return "NO_ACTION" }
        "KEEP_PROTECTED_COMPAT_BRIDGE" { return "NO_KEEP" }
        "PATCH_TO_CURRENT_V18_WRAPPER" { return "NO_PATCH_FIRST" }
        "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" { return "NO_PATCH_FIRST" }
        "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" { return "NO_PATCH_FIRST" }
        "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" { return "MAYBE_AFTER_ZERO_RUNTIME_HIT" }
        "TEXT_REFERENCE_REVIEW_LOW_PRIORITY" { return "LOW_PRIORITY_REVIEW" }
        default { return "REVIEW_FIRST" }
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
$Plan = New-Object System.Collections.Generic.List[object]

foreach ($r in $Rows) {
    $source = Get-SourcePath $r
    $ref = Get-ReferenceText $r
    $line = Get-LineNumber $r

    $zone = Get-SourceZone $source
    $family = Get-Family $source $ref
    $action = Get-Action $zone $family
    $deletePermission = Get-DeletePermission $action

    [void]$Plan.Add([pscustomobject]@{
        SourceRel = $source
        SourceZone = $zone
        Line = $line
        Family = $family
        Action = $action
        DeletePermission = $deletePermission
        ReferenceText = $ref
    })
}

$Plan.ToArray() | Export-Csv -NoTypeInformation -Encoding UTF8 $OutCsv

$TotalRows = $Plan.Count

$ActionSummary = $Plan.ToArray() |
    Group-Object Action |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Action = $_.Name
            Count = $_.Count
        }
    }

$FamilySummary = $Plan.ToArray() |
    Group-Object Family |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            Family = $_.Name
            Count = $_.Count
        }
    }

$ZoneSummary = $Plan.ToArray() |
    Group-Object SourceZone |
    Sort-Object Count -Descending |
    ForEach-Object {
        [pscustomobject]@{
            SourceZone = $_.Name
            Count = $_.Count
        }
    }

$TopFiles = $Plan.ToArray() |
    Group-Object SourceRel |
    Sort-Object Count -Descending |
    Select-Object -First 40 |
    ForEach-Object {
        [pscustomobject]@{
            SourceRel = $_.Name
            Count = $_.Count
        }
    }

$HardDeps = $Plan.ToArray() |
    Where-Object { $_.Action -eq "V18_5B_PATCH_DIRECT_LEGACY_SCRIPT_DEPENDENCY" } |
    Select-Object -First 100 SourceRel, SourceZone, Line, Family, Action, ReferenceText

$AbstractionDeps = $Plan.ToArray() |
    Where-Object { $_.Action -eq "V18_5B_PATCH_OUTPUT_STATE_ABSTRACTION" } |
    Select-Object -First 100 SourceRel, SourceZone, Line, Family, Action, ReferenceText

$WrapperPatch = $Plan.ToArray() |
    Where-Object { $_.Action -eq "PATCH_TO_CURRENT_V18_WRAPPER" } |
    Select-Object -First 100 SourceRel, SourceZone, Line, Family, Action, ReferenceText

$DeleteCandidates = $Plan.ToArray() |
    Where-Object { $_.Action -eq "LEGACY_ROOT_SCRIPT_CANDIDATE_AFTER_RUNTIME_AUDIT" } |
    Select-Object -First 100 SourceRel, SourceZone, Line, Family, Action, DeletePermission, ReferenceText

$Manual = $Plan.ToArray() |
    Where-Object { $_.Action -eq "MANUAL_REVIEW" } |
    Select-Object -First 100 SourceRel, SourceZone, Line, Family, Action, ReferenceText

$Sb = New-Object System.Text.StringBuilder

[void]$Sb.AppendLine("# V18.5A-R2 Runtime Decoupling Classifier")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("## 1. Status")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("- STATUS: OK_SCHEMA_AWARE_CLASSIFIER_READY")
[void]$Sb.AppendLine("- INPUT: $InputCsv")
[void]$Sb.AppendLine("- TOTAL_ROWS_CLASSIFIED: $TotalRows")
[void]$Sb.AppendLine("- PURPOSE: classify runtime references using relative-path-aware source zones.")
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

[void]$Sb.AppendLine("## 5. Top Files")
[void]$Sb.AppendLine("")
Add-Table $Sb $TopFiles @("SourceRel", "Count")

[void]$Sb.AppendLine("## 6. Direct Legacy Script Dependencies")
[void]$Sb.AppendLine("")
Add-Table $Sb $HardDeps @("SourceRel", "SourceZone", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 7. Output Or State Abstraction Dependencies")
[void]$Sb.AppendLine("")
Add-Table $Sb $AbstractionDeps @("SourceRel", "SourceZone", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 8. Old Wrapper Patch Candidates")
[void]$Sb.AppendLine("")
Add-Table $Sb $WrapperPatch @("SourceRel", "SourceZone", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 9. Legacy Root Script Candidates After Runtime Audit")
[void]$Sb.AppendLine("")
Add-Table $Sb $DeleteCandidates @("SourceRel", "SourceZone", "Line", "Family", "Action", "DeletePermission", "ReferenceText")

[void]$Sb.AppendLine("## 10. Manual Review Samples")
[void]$Sb.AppendLine("")
Add-Table $Sb $Manual @("SourceRel", "SourceZone", "Line", "Family", "Action", "ReferenceText")

[void]$Sb.AppendLine("## 11. Next Action")
[void]$Sb.AppendLine("")
[void]$Sb.AppendLine("If Direct Legacy Script Dependencies or Old Wrapper Patch Candidates are non-zero, patch those first.")
[void]$Sb.AppendLine("If they are zero, proceed to V18.5B delete-candidate audit based on runtime graph, not raw text references.")
[void]$Sb.AppendLine("State snapshot rows and generated output rows are ignored for code deletion decisions.")
[void]$Sb.AppendLine("")

$Sb.ToString() | Set-Content -Encoding UTF8 $OutMd

$Read = @()
$Read += "V18_5A_R2_STATUS: OK_SCHEMA_AWARE_CLASSIFIER_READY"
$Read += "INPUT: $InputCsv"
$Read += "CSV: $OutCsv"
$Read += "REPORT: $OutMd"
$Read += "TOTAL_ROWS_CLASSIFIED: $TotalRows"
$Read += ""
$Read += "READ:"
$Read += $OutMd

$Read | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.5A-R2 RUNTIME DECOUPLING CLASSIFIER READY ==="
Write-Host "TOTAL_ROWS_CLASSIFIED:" $TotalRows
Write-Host "CSV:" $OutCsv
Write-Host "REPORT:" $OutMd
Write-Host "READ_FIRST:" $ReadFirst
Write-Host ""

Write-Host "=== ACTION SUMMARY ==="
$ActionSummary | Format-Table -AutoSize

Write-Host ""
Write-Host "=== SOURCE ZONE SUMMARY ==="
$ZoneSummary | Format-Table -AutoSize

Write-Host ""
Write-Host "=== FAMILY SUMMARY TOP ==="
$FamilySummary | Select-Object -First 20 | Format-Table -AutoSize
