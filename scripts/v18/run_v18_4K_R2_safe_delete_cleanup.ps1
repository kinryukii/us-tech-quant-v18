param(
    [switch]$Apply,
    [int]$KeepStableCount = 2
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$OutDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$Report = Join-Path $OutDir "V18_4K_R2_SAFE_DELETE_REPORT_$Stamp.md"
$CurrentReport = Join-Path $OutDir "V18_4K_R2_CURRENT_SAFE_DELETE_REPORT.md"
$Csv = Join-Path $OutDir "V18_4K_R2_SAFE_DELETE_CANDIDATES_$Stamp.csv"

Write-Host ""
Write-Host "=== V18.4K-R2 SAFE DELETE CLEANUP START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE:" $(if ($Apply) { "APPLY_DELETE" } else { "DRYRUN_ONLY" })
Write-Host "KEEP_STABLE_COUNT:" $KeepStableCount

$RuntimeMustExist = @(
    "outputs\v17",
    "outputs\v18\factor_lab",
    "outputs\v18\factor_shadow",
    "outputs\v18\factor_validation",
    "outputs\v18\factor_pack",
    "outputs\v18\daily_integrated",
    "outputs\v18\read_center",
    "outputs\v18\promotion_merge",
    "outputs\v18\outcome_summary",
    "outputs\v18\forward_outcome",
    "outputs\v18\factor_audit",
    "outputs\v18\factor_backtest",
    "state",
    "scripts",
    "src"
)

$MissingRuntime = @()

foreach ($Rel in $RuntimeMustExist) {
    $Path = Join-Path $Root $Rel
    if (!(Test-Path $Path)) {
        $MissingRuntime += $Rel
    }
}

if ($MissingRuntime.Count -gt 0) {
    Write-Host ""
    Write-Host "MISSING_RUNTIME_DEPENDENCY:"
    $MissingRuntime | ForEach-Object { Write-Host $_ }
    throw "Runtime dependency missing. Restore first; cleanup aborted."
}

$Candidates = @()

function Add-Candidate {
    param(
        [string]$Path,
        [string]$Reason
    )

    if (!(Test-Path $Path)) {
        return
    }

    $Item = Get-Item $Path -Force
    $SizeBytes = 0
    $FileCount = 0

    if ($Item.PSIsContainer) {
        $Files = Get-ChildItem -Path $Path -Recurse -File -Force -ErrorAction SilentlyContinue
        $FileCount = @($Files).Count
        foreach ($F in $Files) {
            $SizeBytes += $F.Length
        }
        $Type = "directory"
    }
    else {
        $FileCount = 1
        $SizeBytes = $Item.Length
        $Type = "file"
    }

    $Rel = $Path.Replace($Root, "").TrimStart("\")
    $Candidates += [pscustomobject]@{
        relative_path = $Rel
        full_path = $Path
        item_type = $Type
        file_count = $FileCount
        size_mb = [math]::Round($SizeBytes / 1MB, 3)
        reason = $Reason
        action = $(if ($Apply) { "DELETE" } else { "DRYRUN" })
    }
}

# 1. archive\deprecated 全部可删
$DeprecatedRoot = Join-Path $Root "archive\deprecated"
if (Test-Path $DeprecatedRoot) {
    Get-ChildItem -Path $DeprecatedRoot -Directory -Force | ForEach-Object {
        Add-Candidate -Path $_.FullName -Reason "deprecated_archive"
    }
}

# 2. stable 只保留最新 N 个
$StableRoot = Join-Path $Root "archive\stable"
if (Test-Path $StableRoot) {
    $StableDirs = Get-ChildItem -Path $StableRoot -Directory -Force |
        Sort-Object LastWriteTime -Descending

    $OldStable = $StableDirs | Select-Object -Skip $KeepStableCount

    foreach ($Dir in $OldStable) {
        Add-Candidate -Path $Dir.FullName -Reason "old_stable_snapshot_keep_latest_$KeepStableCount"
    }
}

# 3. Python / test caches
Get-ChildItem -Path $Root -Directory -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -in @("__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache")
    } |
    ForEach-Object {
        Add-Candidate -Path $_.FullName -Reason "cache_directory"
    }

# 4. pyc 文件
Get-ChildItem -Path $Root -File -Recurse -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Extension -in @(".pyc", ".pyo")
    } |
    ForEach-Object {
        Add-Candidate -Path $_.FullName -Reason "compiled_python_cache"
    }

# 5. 旧 V18.4K 清理报告，只保留 current
Get-ChildItem -Path $OutDir -File -Force -ErrorAction SilentlyContinue |
    Where-Object {
        $_.Name -like "V18_4K_WORKSPACE_CLEANUP_*" -or
        $_.Name -like "V18_4K_R2_SAFE_DELETE_CANDIDATES_*" -or
        $_.Name -like "V18_4K_R2_SAFE_DELETE_REPORT_*"
    } |
    ForEach-Object {
        Add-Candidate -Path $_.FullName -Reason "old_cleanup_report"
    }

$Candidates | Export-Csv -Path $Csv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== DELETE CANDIDATES ==="
foreach ($C in $Candidates) {
    Write-Host ("{0} | files={1} | size_mb={2} | reason={3} | {4}" -f $C.relative_path, $C.file_count, $C.size_mb, $C.reason, $C.action)
}

$DeleteFail = @()

if ($Apply) {
    foreach ($C in $Candidates) {
        try {
            Remove-Item -Path $C.full_path -Recurse -Force -ErrorAction Stop
            Write-Host "DELETED:" $C.relative_path
        }
        catch {
            $DeleteFail += "DELETE_FAIL: $($C.relative_path) :: $($_.Exception.Message)"
            Write-Host "DELETE_FAIL:" $C.relative_path
        }
    }

    # 删除空目录，但不碰根目录本身
    Get-ChildItem -Path $Root -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending |
        ForEach-Object {
            try {
                $Children = Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue
                if (@($Children).Count -eq 0) {
                    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                }
            }
            catch {}
        }
}

$Lines = @()
$Lines += "# V18.4K-R2 Safe Delete Cleanup Report"
$Lines += ""
$Lines += "Generated at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
$Lines += ""
$Lines += "## Status"
$Lines += ""
$Lines += "- APPLY: $Apply"
$Lines += "- KEEP_STABLE_COUNT: $KeepStableCount"
$Lines += "- CANDIDATE_COUNT: $($Candidates.Count)"
$Lines += "- DELETE_FAIL_COUNT: $($DeleteFail.Count)"
$Lines += "- CSV: $Csv"
$Lines += ""
$Lines += "## Protected Runtime Dependencies"
foreach ($Rel in $RuntimeMustExist) {
    $Lines += "- KEEP: $Rel"
}
$Lines += ""
$Lines += "## Candidates"
$Lines += ""
$Lines += "| path | type | files | size_mb | reason | action |"
$Lines += "|---|---|---:|---:|---|---|"

foreach ($C in $Candidates) {
    $Lines += "| $($C.relative_path) | $($C.item_type) | $($C.file_count) | $($C.size_mb) | $($C.reason) | $($C.action) |"
}

if ($DeleteFail.Count -gt 0) {
    $Lines += ""
    $Lines += "## Delete Failures"
    foreach ($Fail in $DeleteFail) {
        $Lines += "- $Fail"
    }
}

Set-Content -Path $Report -Value $Lines -Encoding UTF8
Set-Content -Path $CurrentReport -Value $Lines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4K-R2 SAFE DELETE CLEANUP READY ==="
Write-Host "APPLY:" $Apply
Write-Host "CANDIDATE_COUNT:" $Candidates.Count
Write-Host "DELETE_FAIL_COUNT:" $DeleteFail.Count
Write-Host "REPORT:" $Report
Write-Host "CURRENT_REPORT:" $CurrentReport
Write-Host "CSV:" $Csv

if ($DeleteFail.Count -gt 0) {
    throw "Safe delete cleanup completed with failures. Check report."
}

Write-Host ""
Write-Host "=== V18.4K-R2 SAFE DELETE CLEANUP DONE ==="