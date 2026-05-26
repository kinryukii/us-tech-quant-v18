$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$SnapshotName = "V18_4I_R2_stable_integrated_final_daily_promotion_merge_$Stamp"
$SnapshotRoot = Join-Path $Root "archive\stable\$SnapshotName"

$ManifestPath = Join-Path $SnapshotRoot "V18_4I_R2_STABLE_MANIFEST_$Stamp.csv"
$ReadmePath = Join-Path $SnapshotRoot "V18_4I_R2_STABLE_READ_FIRST.txt"
$RestorePath = Join-Path $SnapshotRoot "restore_v18_4I_R2_stable_snapshot.ps1"

Write-Host ""
Write-Host "=== V18.4I-R2 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT: $SnapshotRoot"

New-Item -ItemType Directory -Force -Path $SnapshotRoot | Out-Null

$CopyLayers = @()
$CopyLayers += @{ Source = Join-Path $Root "scripts"; TargetParent = $SnapshotRoot }
$CopyLayers += @{ Source = Join-Path $Root "outputs\v18"; TargetParent = Join-Path $SnapshotRoot "outputs" }
$CopyLayers += @{ Source = Join-Path $Root "outputs\v17"; TargetParent = Join-Path $SnapshotRoot "outputs" }
$CopyLayers += @{ Source = Join-Path $Root "state"; TargetParent = $SnapshotRoot }

$CopyFail = @()

foreach ($Layer in $CopyLayers) {
    $Source = $Layer.Source
    $TargetParent = $Layer.TargetParent

    if (!(Test-Path $Source)) {
        $CopyFail += "MISSING_SOURCE: $Source"
        continue
    }

    New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null

    Write-Host "COPY:" $Source
    try {
        Copy-Item -Path $Source -Destination $TargetParent -Recurse -Force
    }
    catch {
        $CopyFail += "COPY_FAIL: $Source :: $($_.Exception.Message)"
    }
}

$CriticalPS = @()
$CriticalPS += "scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"
$CriticalPS += "scripts\v18\run_v18_4I_backtest_forward_promotion_merge.ps1"
$CriticalPS += "scripts\v18\run_v18_4G_R1_final_daily_factor_audit_wrapper.ps1"
$CriticalPS += "scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1"
$CriticalPS += "scripts\v18\run_v18_4B_R1_final_daily_wrapper.ps1"
$CriticalPS += "scripts\v18\run_v18_4H_R1A_factor_robustness_interpretation_patch.ps1"
$CriticalPS += "scripts\v18\run_v18_4H_R1_factor_robustness_audit.ps1"
$CriticalPS += "scripts\v18\run_v18_4H_factor_rolling_backtest.ps1"

$CriticalPY = @()
$CriticalPY += "scripts\v18\v18_4I_backtest_forward_promotion_merge.py"
$CriticalPY += "scripts\v18\v18_4H_R1A_factor_robustness_interpretation_patch.py"
$CriticalPY += "scripts\v18\v18_4H_R1_factor_robustness_audit.py"
$CriticalPY += "scripts\v18\v18_4H_factor_rolling_backtest.py"
$CriticalPY += "scripts\v18\v18_4B_factor_outcome_summary_promotion_rules.py"
$CriticalPY += "scripts\v18\v18_4A_factor_forward_outcome_tracker.py"

$MissingCritical = @()
$ParseFail = @()

Write-Host ""
Write-Host "=== CHECK CRITICAL POWERSHELL ==="

foreach ($Rel in $CriticalPS) {
    $Path = Join-Path $SnapshotRoot $Rel

    if (!(Test-Path $Path)) {
        $MissingCritical += $Rel
        Write-Host "MISSING:" $Rel
        continue
    }

    try {
        [scriptblock]::Create((Get-Content $Path -Raw)) | Out-Null
        Write-Host "OK_PARSE:" $Path
    }
    catch {
        $ParseFail += "$Rel :: $($_.Exception.Message)"
        Write-Host "PARSE_FAIL:" $Path
    }
}

Write-Host ""
Write-Host "=== CHECK CRITICAL PYTHON ==="

foreach ($Rel in $CriticalPY) {
    $Path = Join-Path $SnapshotRoot $Rel

    if (!(Test-Path $Path)) {
        $MissingCritical += $Rel
        Write-Host "MISSING:" $Rel
        continue
    }

    python -m py_compile $Path

    if ($LASTEXITCODE -ne 0) {
        $ParseFail += "$Rel :: python compile failed"
        Write-Host "PY_COMPILE_FAIL:" $Path
    }
    else {
        Write-Host "OK_PY_COMPILE:" $Path
    }
}

$RestoreLines = @()
$RestoreLines += 'param([string]$Root = "D:\us-tech-quant")'
$RestoreLines += '$ErrorActionPreference = "Stop"'
$RestoreLines += '$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path'
$RestoreLines += 'Write-Host ""'
$RestoreLines += 'Write-Host "=== RESTORE V18.4I-R2 STABLE SNAPSHOT START ==="'
$RestoreLines += 'Write-Host "SNAPSHOT: $SnapshotRoot"'
$RestoreLines += 'Write-Host "ROOT: $Root"'
$RestoreLines += '$Pairs = @()'
$RestoreLines += '$Pairs += @{ Source = "scripts"; Destination = "scripts" }'
$RestoreLines += '$Pairs += @{ Source = "outputs"; Destination = "outputs" }'
$RestoreLines += '$Pairs += @{ Source = "state"; Destination = "state" }'
$RestoreLines += 'foreach ($Pair in $Pairs) {'
$RestoreLines += '    $Src = Join-Path $SnapshotRoot $Pair.Source'
$RestoreLines += '    $Dst = Join-Path $Root $Pair.Destination'
$RestoreLines += '    if (Test-Path $Src) {'
$RestoreLines += '        New-Item -ItemType Directory -Force -Path $Dst | Out-Null'
$RestoreLines += '        Copy-Item -Path (Join-Path $Src "*") -Destination $Dst -Recurse -Force'
$RestoreLines += '        Write-Host "RESTORED:" $Pair.Destination'
$RestoreLines += '    }'
$RestoreLines += '}'
$RestoreLines += 'Write-Host ""'
$RestoreLines += 'Write-Host "=== RESTORE V18.4I-R2 STABLE SNAPSHOT DONE ==="'
$RestoreLines += 'Write-Host "FINAL DAILY COMMAND:"'
$RestoreLines += 'Write-Host ''powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'''

Set-Content -Path $RestorePath -Value $RestoreLines -Encoding UTF8

try {
    [scriptblock]::Create((Get-Content $RestorePath -Raw)) | Out-Null
    Write-Host "OK_RESTORE_PARSE:" $RestorePath
}
catch {
    $ParseFail += "RESTORE_SCRIPT :: $($_.Exception.Message)"
    Write-Host "RESTORE_PARSE_FAIL:" $RestorePath
}

$Files = Get-ChildItem -Path $SnapshotRoot -Recurse -File
$ManifestRows = @()

foreach ($File in $Files) {
    $Rel = $File.FullName.Substring($SnapshotRoot.Length).TrimStart("\")
    $ManifestRows += [pscustomobject]@{
        relative_path = $Rel
        size_bytes = $File.Length
        last_write_time = $File.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")
    }
}

$ManifestRows | Export-Csv -Path $ManifestPath -NoTypeInformation -Encoding UTF8

$ReadmeLines = @()
$ReadmeLines += "V18_4I_R2_STABLE_SNAPSHOT_CREATED"
$ReadmeLines += "GENERATED_AT: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
$ReadmeLines += "SNAPSHOT: $SnapshotRoot"
$ReadmeLines += ""
$ReadmeLines += "SCOPE:"
$ReadmeLines += "V18.4I-R1 integrated final daily promotion merge wrapper"
$ReadmeLines += "V18.4I backtest-forward promotion merge"
$ReadmeLines += "V18.4H / H-R1 / H-R1A historical robustness layer"
$ReadmeLines += "V18.4G-R1 final daily factor audit wrapper"
$ReadmeLines += "V18.4C/D/E/F factor audit chain"
$ReadmeLines += "V18.4B promotion rules and V18.4A forward tracker"
$ReadmeLines += "V18 current outputs and state files"
$ReadmeLines += ""
$ReadmeLines += "FINAL_DAILY_COMMAND:"
$ReadmeLines += 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4I_R1_final_daily_promotion_merge_wrapper.ps1"'
$ReadmeLines += ""
$ReadmeLines += "CURRENT_DECISION_GUARD:"
$ReadmeLines += "OFFICIAL_DECISION_IMPACT: NONE"
$ReadmeLines += "PROMOTION_ACTION: NONE"
$ReadmeLines += "DIRECT_PROMOTION: NO"
$ReadmeLines += ""
$ReadmeLines += "MANIFEST: $ManifestPath"
$ReadmeLines += "RESTORE_SCRIPT: $RestorePath"
$ReadmeLines += ""
$ReadmeLines += "COPY_FAIL_COUNT: $($CopyFail.Count)"
$ReadmeLines += "MISSING_CRITICAL_COUNT: $($MissingCritical.Count)"
$ReadmeLines += "PARSE_FAIL_COUNT: $($ParseFail.Count)"
$ReadmeLines += "TOTAL_FILE_COUNT: $($ManifestRows.Count)"

if ($CopyFail.Count -gt 0) {
    $ReadmeLines += ""
    $ReadmeLines += "COPY_FAIL:"
    $ReadmeLines += $CopyFail
}

if ($MissingCritical.Count -gt 0) {
    $ReadmeLines += ""
    $ReadmeLines += "MISSING_CRITICAL:"
    $ReadmeLines += $MissingCritical
}

if ($ParseFail.Count -gt 0) {
    $ReadmeLines += ""
    $ReadmeLines += "PARSE_FAIL:"
    $ReadmeLines += $ParseFail
}

Set-Content -Path $ReadmePath -Value $ReadmeLines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4I-R2 STABLE SNAPSHOT READY ==="
Write-Host "SNAPSHOT:" $SnapshotRoot
Write-Host "README:" $ReadmePath
Write-Host "MANIFEST:" $ManifestPath
Write-Host "RESTORE_SCRIPT:" $RestorePath
Write-Host "TOTAL_FILE_COUNT:" $ManifestRows.Count
Write-Host "COPY_FAIL_COUNT:" $CopyFail.Count
Write-Host "MISSING_CRITICAL_COUNT:" $MissingCritical.Count
Write-Host "PARSE_FAIL_COUNT:" $ParseFail.Count

if ($CopyFail.Count -gt 0 -or $MissingCritical.Count -gt 0 -or $ParseFail.Count -gt 0) {
    throw "V18.4I-R2 stable snapshot completed with errors. Check README."
}

Write-Host ""
Write-Host "=== V18.4I-R2 STABLE SNAPSHOT DONE ==="