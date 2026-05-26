param(
    [switch]$Apply,
    [switch]$IncludeV17DashboardLegacy
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$OutDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Report = Join-Path $OutDir "V18_8A_CURRENT_LEGACY_V15_V16_PURGE_REPORT.md"
$Csv    = Join-Path $OutDir "V18_8A_CURRENT_LEGACY_V15_V16_PURGE_AUDIT.csv"
$ReadFirst = Join-Path $OutDir "V18_8A_READ_FIRST.txt"

Write-Host ""
Write-Host "=== V18.8A LEGACY V15/V16 PURGE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply) { 'APPLY_DELETE' } else { 'DRYRUN' })"
Write-Host ""

# Active legacy only.
# Do NOT mutate archive\stable internals, because that corrupts stable restore anchors.
$Targets = @(
    "outputs\v15",
    "outputs\v16",
    "state\v15",
    "state\v16",
    "configs\v15",
    "configs\v16"
)

# Legacy scripts.
$ScriptPatterns = @(
    "run_v15*.ps1",
    "run_v15*.py",
    "run_v15*.bat",
    "run_v16*.ps1",
    "run_v16*.py",
    "run_v16*.bat",
    "show_v16*.ps1",
    "show_v16*.py"
)

# V16 portfolio/feedback source remnants.
$SourceTargets = @(
    "src\qutumn\cli\run_position_review.py",
    "src\qutumn\cli\run_trade_feedback.py",
    "src\qutumn\portfolio\position_review.py",
    "src\qutumn\portfolio\trade_feedback.py"
)

# Optional: old V17 dashboard/effectiveness layer that depended on V16 dashboard lineage.
$V17LegacyTargets = @(
    "outputs\v17\factor_effectiveness",
    "scripts\run_v17_3_factor_performance_dashboard.ps1",
    "scripts\run_v17_3_factor_performance_dashboard.py",
    "scripts\run_v17_3_1_factor_dashboard_status_semantics.ps1",
    "scripts\run_v17_3_1B_factor_dashboard_status_semantics.ps1"
)

$Items = New-Object System.Collections.Generic.List[object]

function Add-ItemCandidate {
    param(
        [string]$Category,
        [string]$Path
    )

    $Full = Join-Path $Root $Path
    if (Test-Path $Full) {
        $Resolved = Resolve-Path $Full
        foreach ($r in $Resolved) {
            $item = Get-Item $r.Path -Force
            $size = 0
            if ($item.PSIsContainer) {
                $size = (Get-ChildItem $item.FullName -Recurse -File -Force -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
            } else {
                $size = $item.Length
            }

            $Items.Add([pscustomobject]@{
                Category = $Category
                Type = $(if ($item.PSIsContainer) { "Directory" } else { "File" })
                Exists = $true
                SizeMB = [math]::Round(($size / 1MB), 4)
                FullName = $item.FullName
            }) | Out-Null
        }
    } else {
        $Items.Add([pscustomobject]@{
            Category = $Category
            Type = "Missing"
            Exists = $false
            SizeMB = 0
            FullName = $Full
        }) | Out-Null
    }
}

foreach ($t in $Targets) {
    Add-ItemCandidate -Category "ACTIVE_V15_V16_DIR" -Path $t
}

foreach ($pat in $ScriptPatterns) {
    Get-ChildItem (Join-Path $Root "scripts") -File -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
        $Items.Add([pscustomobject]@{
            Category = "ACTIVE_V15_V16_SCRIPT"
            Type = "File"
            Exists = $true
            SizeMB = [math]::Round(($_.Length / 1MB), 4)
            FullName = $_.FullName
        }) | Out-Null
    }
}

foreach ($t in $SourceTargets) {
    Add-ItemCandidate -Category "V16_SOURCE_REMAINS" -Path $t
}

# Remove pycache files specifically related to deleted V16 source remnants.
Get-ChildItem (Join-Path $Root "src") -Recurse -File -Force -ErrorAction SilentlyContinue | Where-Object {
    $_.FullName -match "__pycache__" -and $_.Name -match "position_review|trade_feedback"
} | ForEach-Object {
    $Items.Add([pscustomobject]@{
        Category = "V16_PYCACHE_REMAINS"
        Type = "File"
        Exists = $true
        SizeMB = [math]::Round(($_.Length / 1MB), 4)
        FullName = $_.FullName
    }) | Out-Null
}

if ($IncludeV17DashboardLegacy) {
    foreach ($t in $V17LegacyTargets) {
        Add-ItemCandidate -Category "OPTIONAL_V17_DASHBOARD_LEGACY" -Path $t
    }
}

# Never delete v18 current scripts/outputs in this purge.
$DeleteCandidates = $Items | Where-Object {
    $_.Exists -eq $true -and
    $_.FullName -notmatch "\\scripts\\v18\\" -and
    $_.FullName -notmatch "\\outputs\\v18\\" -and
    $_.FullName -notmatch "\\state\\v18\\" -and
    $_.FullName -notmatch "\\archive\\stable\\"
}

$Items | Export-Csv -NoTypeInformation -Encoding UTF8 $Csv

$TotalCount = @($DeleteCandidates).Count
$TotalMB = [math]::Round((($DeleteCandidates | Measure-Object SizeMB -Sum).Sum), 4)

if ($Apply) {
    foreach ($x in $DeleteCandidates) {
        if (Test-Path $x.FullName) {
            Remove-Item -LiteralPath $x.FullName -Recurse -Force -ErrorAction Stop
        }
    }
}

$Mode = if ($Apply) { "APPLY_DELETE" } else { "DRYRUN" }
$Status = if ($Apply) { "OK_LEGACY_V15_V16_PURGED" } else { "OK_DRYRUN_READY" }

$md = @()
$md += "# V18.8A Legacy V15/V16 Purge Report"
$md += ""
$md += "- STATUS: ``$Status``"
$md += "- MODE: ``$Mode``"
$md += "- GENERATED_AT: ``$Stamp``"
$md += "- DELETE_CANDIDATE_COUNT: ``$TotalCount``"
$md += "- DELETE_CANDIDATE_MB: ``$TotalMB``"
$md += "- CSV: ``$Csv``"
$md += ""
$md += "## Policy"
$md += ""
$md += "- Active V15/V16 directories, scripts, configs, and V16 simulation/feedback source remnants are candidates."
$md += "- V18 active files are protected."
$md += "- archive\\stable internals are protected to avoid corrupting restore snapshots."
$md += "- V17 dashboard legacy is optional via ``-IncludeV17DashboardLegacy``."
$md += ""
$md += "## Candidates"
$md += ""
$md += "| Category | Type | SizeMB | FullName |"
$md += "|---|---|---:|---|"
foreach ($x in $DeleteCandidates | Sort-Object Category, FullName) {
    $md += "| $($x.Category) | $($x.Type) | $($x.SizeMB) | ``$($x.FullName)`` |"
}
$md -join "`n" | Set-Content -Encoding UTF8 $Report

$rf = @()
$rf += "V18.8A LEGACY V15/V16 PURGE"
$rf += ""
$rf += "STATUS: $Status"
$rf += "MODE: $Mode"
$rf += "DELETE_CANDIDATE_COUNT: $TotalCount"
$rf += "DELETE_CANDIDATE_MB: $TotalMB"
$rf += ""
$rf += "REPORT:"
$rf += $Report
$rf += ""
$rf += "CSV:"
$rf += $Csv
$rf -join "`n" | Set-Content -Encoding UTF8 $ReadFirst

Write-Host ""
Write-Host "=== V18.8A LEGACY V15/V16 PURGE READY ==="
Write-Host "STATUS: $Status"
Write-Host "MODE: $Mode"
Write-Host "DELETE_CANDIDATE_COUNT: $TotalCount"
Write-Host "DELETE_CANDIDATE_MB: $TotalMB"
Write-Host "REPORT: $Report"
Write-Host "CSV: $Csv"
Write-Host "READ_FIRST: $ReadFirst"
Write-Host ""

if (-not $Apply) {
    Write-Host "NEXT:"
    Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply"
}
