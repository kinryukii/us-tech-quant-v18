param()

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$SnapshotName = "V18_8E_R3_stable_current_official_daily_with_simulation_$Stamp"
$SnapshotRoot = Join-Path $Root "archive\stable\$SnapshotName"

$OpsDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$CurrentReadFirst = Join-Path $OpsDir "V18_8E_READ_FIRST.txt"
$CurrentReport = Join-Path $OpsDir "V18_8E_CURRENT_STABLE_SNAPSHOT_REPORT.md"

$SnapshotReadme = Join-Path $SnapshotRoot "V18_8E_R3_STABLE_SNAPSHOT_README.txt"
$Manifest = Join-Path $SnapshotRoot "V18_8E_R3_STABLE_MANIFEST.csv"
$RestoreScript = Join-Path $SnapshotRoot "restore_v18_8E_R2_stable_snapshot.ps1"

Write-Host ""
Write-Host "=== V18.8E-R3 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT: $SnapshotRoot"
Write-Host ""

New-Item -ItemType Directory -Force -Path $SnapshotRoot | Out-Null

$Layers = @(
    "scripts\v18",
    "outputs\v18\read_center",
    "outputs\v18\simulation",
    "outputs\v18\ops",
    "outputs\v18\daily_integrated",
    "outputs\v18\promotion_merge",
    "outputs\v18\factor_audit",
    "outputs\v18\factor_pack",
    "outputs\v18\technical_timing",
    "outputs\v18\technical_timing_read_center",
    "outputs\v18\technical_timing_backtest",
    "outputs\v18\technical_timing_forward",
    "state\v18"
)

$CriticalFiles = @(
    "scripts\v18\run_v18_current_official_daily.ps1",
    "scripts\v18\run_v18_8C_official_daily_fast_with_simulation.ps1",
    "scripts\v18\run_v18_8B_current_simulation_cabin.ps1",
    "scripts\v18\v18_8B_current_simulation_cabin.py",
    "scripts\v18\run_v18_7D_official_daily_fast_main_with_technical.ps1",
    "outputs\v18\read_center\V18_8C_READ_FIRST.txt",
    "outputs\v18\read_center\V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION.md",
    "outputs\v18\simulation\V18_8B_READ_FIRST.txt",
    "outputs\v18\simulation\V18_CURRENT_SIM_CABIN.md",
    "state\v18\simulation\V18_CURRENT_SIM_ACCOUNT.csv",
    "state\v18\simulation\V18_CURRENT_PAPER_POSITIONS.csv",
    "state\v18\simulation\V18_CURRENT_PAPER_TRADE_LOG.csv"
)

$CopyAudit = @()

function Copy-LayerSafe {
    param([string]$RelPath)

    $src = Join-Path $Root $RelPath
    $dst = Join-Path $SnapshotRoot $RelPath

    if (-not (Test-Path $src)) {
        $script:CopyAudit += [pscustomobject]@{
            RelPath = $RelPath
            Exists = $false
            Type = "Missing"
            Copied = $false
            FileCountAfterCopy = 0
            Detail = "SOURCE_MISSING"
        }
        return
    }

    $item = Get-Item -LiteralPath $src -Force

    if ($item.PSIsContainer) {
        New-Item -ItemType Directory -Force -Path $dst | Out-Null

        $children = Get-ChildItem -LiteralPath $src -Force -ErrorAction SilentlyContinue
        foreach ($child in $children) {
            Copy-Item -LiteralPath $child.FullName -Destination $dst -Recurse -Force -ErrorAction Stop
        }

        $count = @(Get-ChildItem -LiteralPath $dst -Recurse -File -Force -ErrorAction SilentlyContinue).Count

        $script:CopyAudit += [pscustomobject]@{
            RelPath = $RelPath
            Exists = $true
            Type = "Directory"
            Copied = $true
            FileCountAfterCopy = $count
            Detail = "COPIED_DIRECTORY_CONTENTS"
        }
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Force -ErrorAction Stop

        $script:CopyAudit += [pscustomobject]@{
            RelPath = $RelPath
            Exists = $true
            Type = "File"
            Copied = $true
            FileCountAfterCopy = 1
            Detail = "COPIED_FILE"
        }
    }
}

Write-Host "=== COPY STABLE LAYERS ==="
foreach ($layer in $Layers) {
    Write-Host "COPY: $layer"
    Copy-LayerSafe -RelPath $layer
}

$MissingCritical = @()
foreach ($f in $CriticalFiles) {
    $p = Join-Path $SnapshotRoot $f
    if (-not (Test-Path $p)) {
        $MissingCritical += $f
    }
}

Write-Host ""
Write-Host "=== PARSE CHECK POWERSHELL SCRIPTS ==="

$ParseFailures = @()
$EmptyPsFiles = @()
$psRoot = Join-Path $SnapshotRoot "scripts\v18"
$psFiles = @()

if (Test-Path $psRoot) {
    $psFiles = @(Get-ChildItem -LiteralPath $psRoot -File -Filter "*.ps1" -ErrorAction SilentlyContinue)
}

foreach ($f in $psFiles) {
    $raw = ""

    try {
        $raw = Get-Content -Raw -LiteralPath $f.FullName -ErrorAction Stop
    } catch {
        $raw = ""
    }

    if ([string]::IsNullOrWhiteSpace($raw)) {
        $EmptyPsFiles += $f.FullName
        Write-Host "SKIP_EMPTY_PS1: $($f.FullName)"
        continue
    }

    $parseErrors = $null
    [System.Management.Automation.PSParser]::Tokenize($raw, [ref]$parseErrors) | Out-Null

    if ($parseErrors -and $parseErrors.Count -gt 0) {
        $ParseFailures += $f.FullName
        Write-Host "PARSE_FAIL: $($f.FullName)"
    } else {
        Write-Host "OK_PARSE: $($f.FullName)"
    }
}

Write-Host ""
Write-Host "=== PYTHON COMPILE CHECK ==="

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$PyCompileFailures = @()
$pyFiles = @()
if (Test-Path $psRoot) {
    $pyFiles = @(Get-ChildItem -LiteralPath $psRoot -File -Filter "*.py" -ErrorAction SilentlyContinue)
}

foreach ($f in $pyFiles) {
    & $Python -m py_compile $f.FullName
    if ($LASTEXITCODE -ne 0) {
        $PyCompileFailures += $f.FullName
        Write-Host "PY_COMPILE_FAIL: $($f.FullName)"
    } else {
        Write-Host "OK_PY_COMPILE: $($f.FullName)"
    }
}

Write-Host ""
Write-Host "=== ACTIVE LEGACY CHECK ==="

$LegacyCandidates = @()

$LegacyPaths = @(
    "outputs\v15",
    "outputs\v16",
    "state\v15",
    "state\v16",
    "configs\v15",
    "configs\v16"
)

foreach ($p in $LegacyPaths) {
    $full = Join-Path $Root $p
    if (Test-Path $full) {
        $LegacyCandidates += $full
    }
}

$LegacyScriptPatterns = @(
    "run_v15*.ps1",
    "run_v15*.py",
    "run_v15*.bat",
    "run_v16*.ps1",
    "run_v16*.py",
    "run_v16*.bat",
    "show_v16*.ps1",
    "show_v16*.py"
)

foreach ($pat in $LegacyScriptPatterns) {
    Get-ChildItem (Join-Path $Root "scripts") -File -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
        $LegacyCandidates += $_.FullName
    }
}

foreach ($x in $LegacyCandidates) {
    Write-Host "LEGACY_REMAIN: $x"
}

Write-Host ""
Write-Host "=== WRITE RESTORE SCRIPT ==="

$RestoreLines = @()
$RestoreLines += 'param([string]$Root = "D:\us-tech-quant")'
$RestoreLines += ''
$RestoreLines += '$ErrorActionPreference = "Stop"'
$RestoreLines += '$Snapshot = $PSScriptRoot'
$RestoreLines += ''
$RestoreLines += '$Layers = @('
foreach ($layer in $Layers) {
    $RestoreLines += ('    "{0}",' -f $layer)
}
$RestoreLines += ')'
$RestoreLines += ''
$RestoreLines += 'Write-Host ""'
$RestoreLines += 'Write-Host "=== RESTORE V18.8E-R3 STABLE SNAPSHOT START ==="'
$RestoreLines += 'Write-Host "SNAPSHOT: $Snapshot"'
$RestoreLines += 'Write-Host "ROOT: $Root"'
$RestoreLines += ''
$RestoreLines += 'foreach ($layer in $Layers) {'
$RestoreLines += '    $src = Join-Path $Snapshot $layer'
$RestoreLines += '    $dst = Join-Path $Root $layer'
$RestoreLines += '    if (Test-Path $src) {'
$RestoreLines += '        Write-Host "RESTORE: $layer"'
$RestoreLines += '        $item = Get-Item -LiteralPath $src -Force'
$RestoreLines += '        if ($item.PSIsContainer) {'
$RestoreLines += '            New-Item -ItemType Directory -Force -Path $dst | Out-Null'
$RestoreLines += '            $children = Get-ChildItem -LiteralPath $src -Force -ErrorAction SilentlyContinue'
$RestoreLines += '            foreach ($child in $children) {'
$RestoreLines += '                Copy-Item -LiteralPath $child.FullName -Destination $dst -Recurse -Force'
$RestoreLines += '            }'
$RestoreLines += '        } else {'
$RestoreLines += '            New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null'
$RestoreLines += '            Copy-Item -LiteralPath $src -Destination $dst -Force'
$RestoreLines += '        }'
$RestoreLines += '    }'
$RestoreLines += '}'
$RestoreLines += ''
$RestoreLines += 'Write-Host "=== RESTORE V18.8E-R3 STABLE SNAPSHOT DONE ==="'

$RestoreLines -join "`n" | Set-Content -Encoding UTF8 $RestoreScript

$CopiedFiles = @(Get-ChildItem -LiteralPath $SnapshotRoot -Recurse -File -Force -ErrorAction SilentlyContinue)
$CopiedFileCount = $CopiedFiles.Count

$MissingCount = @($CopyAudit | Where-Object { $_.Exists -eq $false }).Count
$MissingCriticalCount = @($MissingCritical).Count
$ParseFailCount = @($ParseFailures).Count
$PyCompileFailCount = @($PyCompileFailures).Count
$LegacyActiveCount = @($LegacyCandidates).Count

$Status = "OK_STABLE_SNAPSHOT_READY"
if ($MissingCriticalCount -gt 0 -or $ParseFailCount -gt 0 -or $PyCompileFailCount -gt 0 -or $CopiedFileCount -eq 0) {
    $Status = "FAIL_STABLE_SNAPSHOT_VALIDATION"
} elseif ($LegacyActiveCount -gt 0) {
    $Status = "WARN_STABLE_SNAPSHOT_READY_WITH_ACTIVE_LEGACY_REMAINS"
}

$Readme = @()
$Readme += "V18.8E-R3 STABLE SNAPSHOT README"
$Readme += ""
$Readme += "STATUS: $Status"
$Readme += "SNAPSHOT:"
$Readme += $SnapshotRoot
$Readme += ""
$Readme += "CREATED_AT: $Stamp"
$Readme += "COPIED_FILE_COUNT: $CopiedFileCount"
$Readme += "MISSING_LAYER_COUNT: $MissingCount"
$Readme += "MISSING_CRITICAL_COUNT: $MissingCriticalCount"
$Readme += "PARSE_FAIL_COUNT: $ParseFailCount"
$Readme += "PY_COMPILE_FAIL_COUNT: $PyCompileFailCount"
$Readme += "ACTIVE_LEGACY_REMAIN_COUNT: $LegacyActiveCount"
$Readme += ""
$Readme += "MANIFEST:"
$Readme += $Manifest
$Readme += ""
$Readme += "RESTORE_SCRIPT:"
$Readme += $RestoreScript
$Readme += ""
$Readme += "INTERPRETATION:"
$Readme += "This snapshot preserves the clean V18.8 baseline after legacy purge, V18 simulation cabin rebuild, official daily simulation integration, and current official entry unification."
$Readme += "V18 current official daily entry points to V18.8C."
$Readme += "Simulation remains shadow-only and does not modify official decisions."

$Readme -join "`n" | Set-Content -Encoding UTF8 $SnapshotReadme

Write-Host ""
Write-Host "=== BUILD MANIFEST ==="

$ManifestRows = @()
$files = @(Get-ChildItem -LiteralPath $SnapshotRoot -Recurse -File -Force -ErrorAction SilentlyContinue)

foreach ($f in $files) {
    $rel = $f.FullName.Substring($SnapshotRoot.Length).TrimStart("\")
    $hash = ""
    try {
        $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $f.FullName).Hash
    } catch {
        $hash = "HASH_FAIL"
    }

    $ManifestRows += [pscustomobject]@{
        RelPath = $rel
        SizeBytes = $f.Length
        LastWriteTimeUtc = $f.LastWriteTimeUtc.ToString("yyyy-MM-dd HH:mm:ss")
        Sha256 = $hash
    }
}

$ManifestRows | Export-Csv -NoTypeInformation -Encoding UTF8 $Manifest

$Report = @()
$Report += "# V18.8E-R3 Stable Snapshot Report"
$Report += ""
$Report += "- STATUS: ``$Status``"
$Report += "- SNAPSHOT: ``$SnapshotRoot``"
$Report += "- CREATED_AT: ``$Stamp``"
$Report += "- COPIED_FILE_COUNT: ``$CopiedFileCount``"
$Report += "- MISSING_LAYER_COUNT: ``$MissingCount``"
$Report += "- MISSING_CRITICAL_COUNT: ``$MissingCriticalCount``"
$Report += "- PARSE_FAIL_COUNT: ``$ParseFailCount``"
$Report += "- PY_COMPILE_FAIL_COUNT: ``$PyCompileFailCount``"
$Report += "- ACTIVE_LEGACY_REMAIN_COUNT: ``$LegacyActiveCount``"
$Report += "- MANIFEST: ``$Manifest``"
$Report += "- RESTORE_SCRIPT: ``$RestoreScript``"
$Report += ""
$Report += "## Copied Layers"
$Report += ""
$Report += "| RelPath | Exists | Type | Copied | FileCountAfterCopy | Detail |"
$Report += "|---|---:|---|---:|---:|---|"
foreach ($x in $CopyAudit) {
    $Report += "| $($x.RelPath) | $($x.Exists) | $($x.Type) | $($x.Copied) | $($x.FileCountAfterCopy) | $($x.Detail) |"
}
$Report += ""
$Report += "## Missing Critical Files"
$Report += ""
if ($MissingCriticalCount -eq 0) {
    $Report += "- NONE"
} else {
    foreach ($x in $MissingCritical) {
        $Report += "- ``$x``"
    }
}
$Report += ""
$Report += "## Active Legacy Remains"
$Report += ""
if ($LegacyActiveCount -eq 0) {
    $Report += "- NONE"
} else {
    foreach ($x in $LegacyCandidates) {
        $Report += "- ``$x``"
    }
}

$Report -join "`n" | Set-Content -Encoding UTF8 $CurrentReport

$RF = @()
$RF += "V18.8E-R3 STABLE SNAPSHOT"
$RF += ""
$RF += "STATUS: $Status"
$RF += "SNAPSHOT:"
$RF += $SnapshotRoot
$RF += ""
$RF += "COPIED_FILE_COUNT: $CopiedFileCount"
$RF += "MISSING_LAYER_COUNT: $MissingCount"
$RF += "MISSING_CRITICAL_COUNT: $MissingCriticalCount"
$RF += "PARSE_FAIL_COUNT: $ParseFailCount"
$RF += "PY_COMPILE_FAIL_COUNT: $PyCompileFailCount"
$RF += "ACTIVE_LEGACY_REMAIN_COUNT: $LegacyActiveCount"
$RF += ""
$RF += "README:"
$RF += $SnapshotReadme
$RF += ""
$RF += "MANIFEST:"
$RF += $Manifest
$RF += ""
$RF += "RESTORE_SCRIPT:"
$RF += $RestoreScript
$RF += ""
$RF += "REPORT:"
$RF += $CurrentReport

$RF -join "`n" | Set-Content -Encoding UTF8 $CurrentReadFirst

Write-Host ""
Write-Host "=== V18.8E-R3 STABLE SNAPSHOT READY ==="
Write-Host "STATUS: $Status"
Write-Host "SNAPSHOT: $SnapshotRoot"
Write-Host "COPIED_FILE_COUNT: $CopiedFileCount"
Write-Host "MISSING_LAYER_COUNT: $MissingCount"
Write-Host "MISSING_CRITICAL_COUNT: $MissingCriticalCount"
Write-Host "PARSE_FAIL_COUNT: $ParseFailCount"
Write-Host "PY_COMPILE_FAIL_COUNT: $PyCompileFailCount"
Write-Host "ACTIVE_LEGACY_REMAIN_COUNT: $LegacyActiveCount"
Write-Host "README: $SnapshotReadme"
Write-Host "MANIFEST: $Manifest"
Write-Host "RESTORE_SCRIPT: $RestoreScript"
Write-Host "READ_FIRST: $CurrentReadFirst"
Write-Host "REPORT: $CurrentReport"
Write-Host ""

if ($Status -like "FAIL*") {
    throw $Status
}

