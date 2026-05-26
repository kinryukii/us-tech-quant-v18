$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$OutDir = Join-Path $Root "outputs\v18\ops"

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$CsvOut = Join-Path $OutDir "V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.csv"
$MdOut = Join-Path $OutDir "V18_5A_CURRENT_RUNTIME_DECOUPLING_AUDIT.md"

Write-Host ""
Write-Host "=== V18.5A RUNTIME DECOUPLING AUDIT START ==="

$SearchRoots = @(
    "scripts",
    "src",
    "state"
)

$Patterns = @(
    "outputs\\v16",
    "outputs\\v17",
    "outputs\\v18\\factor_lab",
    "outputs\\v18\\factor_shadow",
    "outputs\\v18\\factor_validation",
    "outputs\\v18\\manifests",
    "outputs\\v18\\cockpit",
    "outputs\\v18\\daily",
    "data\\prices",
    "data\\events",
    "V17_7B",
    "V18_3A",
    "V18_3D",
    "V18_CURRENT_RAW105_FACTOR_PACK_RANKING",
    "V18_3D_RAW105_FACTOR_PACK_RANKING",
    "V18_CURRENT_FINAL_DAILY",
    "V18_CURRENT_READ_FIRST"
)

$Rows = @()

foreach ($RelRoot in $SearchRoots) {
    $SearchRoot = Join-Path $Root $RelRoot

    if (!(Test-Path $SearchRoot)) {
        continue
    }

    $Files = Get-ChildItem -Path $SearchRoot -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object {
            $_.Extension -in @(".ps1", ".py", ".txt", ".md", ".csv", ".json")
        }

    foreach ($File in $Files) {
        $Text = ""
        try {
            $Text = Get-Content $File.FullName -Raw -ErrorAction Stop
        }
        catch {
            continue
        }

        foreach ($Pattern in $Patterns) {
            if ($Text -match [regex]::Escape($Pattern)) {
                $LineNo = 0
                $Lines = Get-Content $File.FullName -ErrorAction SilentlyContinue

                foreach ($Line in $Lines) {
                    $LineNo += 1

                    if ($Line -match [regex]::Escape($Pattern)) {
                        $RelFile = $File.FullName.Replace($Root, "").TrimStart("\")

                        $DependencyClass = "UNKNOWN"

                        if ($Pattern -match "outputs\\v16|outputs\\v17|factor_lab|factor_shadow|factor_validation|data\\prices|data\\events|V17_7B|V18_3A|V18_3D") {
                            $DependencyClass = "LEGACY_RUNTIME_DEPENDENCY_CANDIDATE"
                        }

                        if ($Pattern -match "V18_CURRENT_READ_FIRST|V18_CURRENT_FINAL_DAILY") {
                            $DependencyClass = "CURRENT_OUTPUT_REFERENCE"
                        }

                        $Rows += [pscustomobject]@{
                            file = $RelFile
                            line = $LineNo
                            pattern = $Pattern
                            dependency_class = $DependencyClass
                            text = $Line.Trim()
                        }
                    }
                }
            }
        }
    }
}

$Rows = $Rows | Sort-Object file, line, pattern

$Rows | Export-Csv -Path $CsvOut -NoTypeInformation -Encoding UTF8

$LegacyRows = @($Rows | Where-Object { $_.dependency_class -eq "LEGACY_RUNTIME_DEPENDENCY_CANDIDATE" })
$CurrentRows = @($Rows | Where-Object { $_.dependency_class -eq "CURRENT_OUTPUT_REFERENCE" })

$FilesHit = @($Rows | Select-Object -ExpandProperty file -Unique)
$LegacyFilesHit = @($LegacyRows | Select-Object -ExpandProperty file -Unique)

$LinesOut = @()
$LinesOut += "# V18.5A Runtime Dependency Decoupling Audit"
$LinesOut += ""
$LinesOut += "Generated at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
$LinesOut += ""
$LinesOut += "## 1. Status"
$LinesOut += ""
$LinesOut += "- V18_5A_STATUS: AUDIT_READY"
$LinesOut += "- TOTAL_REFERENCE_COUNT: $($Rows.Count)"
$LinesOut += "- FILES_HIT_COUNT: $($FilesHit.Count)"
$LinesOut += "- LEGACY_RUNTIME_REFERENCE_COUNT: $($LegacyRows.Count)"
$LinesOut += "- LEGACY_RUNTIME_FILES_HIT_COUNT: $($LegacyFilesHit.Count)"
$LinesOut += "- CURRENT_OUTPUT_REFERENCE_COUNT: $($CurrentRows.Count)"
$LinesOut += "- CSV: $CsvOut"
$LinesOut += ""
$LinesOut += "## 2. Interpretation"
$LinesOut += ""
$LinesOut += "This audit identifies old-looking paths that are still referenced by scripts or state files."
$LinesOut += "Anything listed under LEGACY_RUNTIME_DEPENDENCY_CANDIDATE must not be deleted before migration."
$LinesOut += ""
$LinesOut += "## 3. Legacy Runtime Dependency Files"
$LinesOut += ""

if ($LegacyFilesHit.Count -eq 0) {
    $LinesOut += "- None"
}
else {
    foreach ($F in $LegacyFilesHit) {
        $Count = @($LegacyRows | Where-Object { $_.file -eq $F }).Count
        $LinesOut += "- $F : $Count references"
    }
}

$LinesOut += ""
$LinesOut += "## 4. Top References"
$LinesOut += ""
$LinesOut += "| file | line | pattern | class | text |"
$LinesOut += "|---|---:|---|---|---|"

$TopRows = $Rows | Select-Object -First 80

foreach ($R in $TopRows) {
    $SafeText = $R.text.Replace("|", "/")
    $LinesOut += "| $($R.file) | $($R.line) | $($R.pattern) | $($R.dependency_class) | $SafeText |"
}

$LinesOut += ""
$LinesOut += "## 5. Next Step"
$LinesOut += ""
$LinesOut += "If legacy runtime references are found, the next step is V18.5B runtime input migration."
$LinesOut += "That step should copy required legacy runtime inputs into state\\runtime_inputs and patch readers to prefer canonical inputs."
$LinesOut += ""
$LinesOut += "Do not delete outputs\\v16, outputs\\v17, outputs\\v18\\factor_lab, factor_shadow, factor_validation, data\\prices, or data\\events until this audit shows zero runtime references."

Set-Content -Path $MdOut -Value $LinesOut -Encoding UTF8

Write-Host ""
Write-Host "=== V18.5A RUNTIME DECOUPLING AUDIT READY ==="
Write-Host "TOTAL_REFERENCE_COUNT:" $Rows.Count
Write-Host "FILES_HIT_COUNT:" $FilesHit.Count
Write-Host "LEGACY_RUNTIME_REFERENCE_COUNT:" $LegacyRows.Count
Write-Host "LEGACY_RUNTIME_FILES_HIT_COUNT:" $LegacyFilesHit.Count
Write-Host "CSV:" $CsvOut
Write-Host "REPORT:" $MdOut

Write-Host ""
Write-Host "=== V18.5A RUNTIME DECOUPLING AUDIT DONE ==="