param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.6E-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"

Set-Location $Root

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotName = "V18_6E_R2_stable_final_read_center_with_technical_$Stamp"
$SnapshotRoot = Join-Path $Root "archive\stable\$SnapshotName"

New-Item -ItemType Directory -Force -Path $SnapshotRoot | Out-Null

$Manifest = New-Object System.Collections.Generic.List[object]
$MissingCount = 0
$CopyFailCount = 0
$CopiedFileCount = 0

function Add-ManifestRow {
    param(
        [string]$RelPath,
        [string]$ItemType,
        [string]$Status,
        [int64]$SizeBytes,
        [string]$Note
    )

    $script:Manifest.Add([pscustomobject]@{
        rel_path = $RelPath
        item_type = $ItemType
        status = $Status
        size_bytes = $SizeBytes
        note = $Note
    }) | Out-Null
}

function Copy-RelPath {
    param([string]$RelPath)

    $src = Join-Path $Root $RelPath
    $dst = Join-Path $SnapshotRoot $RelPath

    if (!(Test-Path $src)) {
        $script:MissingCount += 1
        Add-ManifestRow -RelPath $RelPath -ItemType "MISSING" -Status "MISSING" -SizeBytes 0 -Note "Source not found"
        return
    }

    try {
        $parent = Split-Path -Parent $dst
        New-Item -ItemType Directory -Force -Path $parent | Out-Null

        if ((Get-Item $src).PSIsContainer) {
            Copy-Item -Path $src -Destination $dst -Recurse -Force

            $files = Get-ChildItem -Path $src -Recurse -File -ErrorAction SilentlyContinue
            foreach ($f in $files) {
                $rel = $f.FullName.Substring($Root.Length).TrimStart("\")
                Add-ManifestRow -RelPath $rel -ItemType "FILE" -Status "COPIED" -SizeBytes $f.Length -Note "Copied from directory layer"
                $script:CopiedFileCount += 1
            }
        }
        else {
            Copy-Item -Path $src -Destination $dst -Force
            $f = Get-Item $src
            $rel = $f.FullName.Substring($Root.Length).TrimStart("\")
            Add-ManifestRow -RelPath $rel -ItemType "FILE" -Status "COPIED" -SizeBytes $f.Length -Note "Copied single file"
            $script:CopiedFileCount += 1
        }
    }
    catch {
        $script:CopyFailCount += 1
        Add-ManifestRow -RelPath $RelPath -ItemType "COPY_FAIL" -Status "COPY_FAIL" -SizeBytes 0 -Note $_.Exception.Message
    }
}

$CopyItems = @(
    "scripts\v18",
    "outputs\v18\read_center",
    "outputs\v18\technical_timing",
    "outputs\v18\technical_timing_backtest",
    "outputs\v18\technical_timing_forward",
    "outputs\v18\technical_timing_read_center",
    "state\v18"
)

Write-Host ""
Write-Host "=== COPY STABLE LAYERS ==="

foreach ($item in $CopyItems) {
    Write-Host "COPY: $item"
    Copy-RelPath -RelPath $item
}

$CriticalPs1 = @(
    "scripts\v18\run_v18_6E_final_read_center_with_technical.ps1",
    "scripts\v18\run_v18_6D_technical_timing_read_center.ps1",
    "scripts\v18\run_v18_6C_R1_technical_timing_forward_tracker_freshness_guard.ps1",
    "scripts\v18\run_v18_6B_R1_technical_timing_diagnostic_patch.ps1",
    "scripts\v18\run_v18_6B_technical_timing_backtest.ps1",
    "scripts\v18\run_v18_6A_technical_timing_shadow.ps1",
    "scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"
)

$CriticalPy = @(
    "scripts\v18\v18_6E_final_read_center_with_technical.py",
    "scripts\v18\v18_6D_technical_timing_read_center.py",
    "scripts\v18\v18_6C_R1_technical_timing_forward_tracker_freshness_guard.py",
    "scripts\v18\v18_6C_technical_timing_forward_tracker.py",
    "scripts\v18\v18_6B_R1_technical_timing_diagnostic_patch.py",
    "scripts\v18\v18_6B_technical_timing_backtest.py",
    "scripts\v18\v18_6A_technical_timing_shadow.py"
)

$ParseFailCount = 0
$PyCompileFailCount = 0
$MissingCriticalCount = 0

Write-Host ""
Write-Host "=== PARSE CHECK CRITICAL POWERSHELL ==="

foreach ($rel in $CriticalPs1) {
    $p = Join-Path $Root $rel

    if (!(Test-Path $p)) {
        $MissingCriticalCount += 1
        Write-Host "MISSING_CRITICAL: $p"
        continue
    }

    $errors = $null
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $p -Raw), [ref]$errors)

    if ($errors -and $errors.Count -gt 0) {
        $ParseFailCount += 1
        Write-Host "PARSE_FAIL: $p"
    }
    else {
        Write-Host "OK_PARSE: $p"
    }
}

Write-Host ""
Write-Host "=== PY COMPILE CHECK CRITICAL PYTHON ==="

foreach ($rel in $CriticalPy) {
    $p = Join-Path $Root $rel

    if (!(Test-Path $p)) {
        $MissingCriticalCount += 1
        Write-Host "MISSING_CRITICAL: $p"
        continue
    }

    python -m py_compile $p

    if ($LASTEXITCODE -ne 0) {
        $PyCompileFailCount += 1
        Write-Host "PY_COMPILE_FAIL: $p"
    }
    else {
        Write-Host "OK_PY_COMPILE: $p"
    }
}

$ManifestPath = Join-Path $SnapshotRoot "V18_6E_R2_STABLE_MANIFEST.csv"
$ReadmePath = Join-Path $SnapshotRoot "V18_6E_R2_STABLE_SNAPSHOT_README.txt"
$RestorePath = Join-Path $SnapshotRoot "restore_v18_6E_R2_stable_snapshot.ps1"

$Manifest | Export-Csv -Path $ManifestPath -NoTypeInformation -Encoding UTF8

$RestoreLines = @()
$RestoreLines += 'param([string]$Root = "D:\us-tech-quant")'
$RestoreLines += '$ErrorActionPreference = "Stop"'
$RestoreLines += '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path'
$RestoreLines += 'Write-Host ""'
$RestoreLines += 'Write-Host "=== RESTORE V18.6E-R2 STABLE SNAPSHOT START ==="'
$RestoreLines += 'Write-Host "SNAPSHOT: $SnapshotRoot"'
$RestoreLines += 'Write-Host "TARGET ROOT: $Root"'
$RestoreLines += '$CopyItems = @('

foreach ($item in $CopyItems) {
    $RestoreLines += "    `"$item`","
}

$RestoreLines += ')'
$RestoreLines += 'foreach ($item in $CopyItems) {'
$RestoreLines += '    $src = Join-Path $SnapshotRoot $item'
$RestoreLines += '    $dst = Join-Path $Root $item'
$RestoreLines += '    if (Test-Path $src) {'
$RestoreLines += '        $parent = Split-Path -Parent $dst'
$RestoreLines += '        New-Item -ItemType Directory -Force -Path $parent | Out-Null'
$RestoreLines += '        Copy-Item -Path $src -Destination $dst -Recurse -Force'
$RestoreLines += '        Write-Host "RESTORED: $item"'
$RestoreLines += '    } else {'
$RestoreLines += '        Write-Host "MISSING_IN_SNAPSHOT: $item"'
$RestoreLines += '    }'
$RestoreLines += '}'
$RestoreLines += 'Write-Host "=== RESTORE V18.6E-R2 STABLE SNAPSHOT DONE ==="'

$RestoreLines | Set-Content -Path $RestorePath -Encoding UTF8

$StableStatus = "OK_STABLE_SNAPSHOT_READY"

if ($MissingCount -gt 0 -or $CopyFailCount -gt 0 -or $ParseFailCount -gt 0 -or $PyCompileFailCount -gt 0 -or $MissingCriticalCount -gt 0) {
    $StableStatus = "WARN_STABLE_SNAPSHOT_CREATED_WITH_ISSUES"
}

$Readme = @()
$Readme += "V18.6E-R2 STABLE SNAPSHOT README"
$Readme += ""
$Readme += "STATUS:"
$Readme += $StableStatus
$Readme += ""
$Readme += "SNAPSHOT:"
$Readme += $SnapshotRoot
$Readme += ""
$Readme += "CREATED_AT:"
$Readme += (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
$Readme += ""
$Readme += "PURPOSE:"
$Readme += "Stable snapshot after V18.6E final read center with technical timing integration."
$Readme += ""
$Readme += "KEY CAPABILITIES PRESERVED:"
$Readme += "- V18.6A technical timing shadow: Bollinger Bands / RSI / KDJ / VIX"
$Readme += "- V18.6B technical timing backtest"
$Readme += "- V18.6B-R1 overheat decomposition and benchmark excess"
$Readme += "- V18.6C-R1 technical timing forward tracker freshness guard"
$Readme += "- V18.6D technical timing read center"
$Readme += "- V18.6E final read center with technical timing"
$Readme += ""
$Readme += "COUNTS:"
$Readme += "COPIED_FILE_COUNT: $CopiedFileCount"
$Readme += "MISSING_COUNT: $MissingCount"
$Readme += "COPY_FAIL_COUNT: $CopyFailCount"
$Readme += "MISSING_CRITICAL_COUNT: $MissingCriticalCount"
$Readme += "PARSE_FAIL_COUNT: $ParseFailCount"
$Readme += "PY_COMPILE_FAIL_COUNT: $PyCompileFailCount"
$Readme += ""
$Readme += "RESTORE:"
$Readme += $RestorePath
$Readme += ""
$Readme += "MANIFEST:"
$Readme += $ManifestPath
$Readme += ""
$Readme += "OFFICIAL_DECISION_IMPACT:"
$Readme += "NONE"

$Readme | Set-Content -Path $ReadmePath -Encoding UTF8

Write-Host ""
Write-Host "=== V18.6E-R2 STABLE SNAPSHOT READY ==="
Write-Host "STABLE_STATUS: $StableStatus"
Write-Host "SNAPSHOT: $SnapshotRoot"
Write-Host "README: $ReadmePath"
Write-Host "MANIFEST: $ManifestPath"
Write-Host "RESTORE_SCRIPT: $RestorePath"
Write-Host "COPIED_FILE_COUNT: $CopiedFileCount"
Write-Host "MISSING_COUNT: $MissingCount"
Write-Host "COPY_FAIL_COUNT: $CopyFailCount"
Write-Host "MISSING_CRITICAL_COUNT: $MissingCriticalCount"
Write-Host "PARSE_FAIL_COUNT: $ParseFailCount"
Write-Host "PY_COMPILE_FAIL_COUNT: $PyCompileFailCount"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host ""
Write-Host "=== V18.6E-R2 STABLE SNAPSHOT DONE ==="
