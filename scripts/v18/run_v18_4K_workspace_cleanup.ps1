param(
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"

$ArchiveRoot = Join-Path $Root "archive\deprecated\v18_4K_workspace_cleanup_$Stamp"
$OutDir = Join-Path $Root "outputs\v18\ops"
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$ReportCsv = Join-Path $OutDir "V18_4K_WORKSPACE_CLEANUP_CANDIDATES_$Stamp.csv"
$ReportMd = Join-Path $OutDir "V18_4K_WORKSPACE_CLEANUP_REPORT_$Stamp.md"
$CurrentReport = Join-Path $OutDir "V18_4K_CURRENT_WORKSPACE_CLEANUP_REPORT.md"

$FinalDailyCommand = 'powershell -NoProfile -ExecutionPolicy Bypass -File "D:\us-tech-quant\scripts\v18\run_v18_4J_R1_final_daily_read_center_wrapper.ps1"'

Write-Host ""
Write-Host "=== V18.4K WORKSPACE CLEANUP START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE:" $(if ($Apply) { "APPLY_MOVE_TO_ARCHIVE" } else { "DRYRUN_ONLY" })

$MustKeep = @()
$MustKeep += "scripts"
$MustKeep += "src"
$MustKeep += "state"
$MustKeep += "configs"
$MustKeep += "archive\stable"
$MustKeep += "outputs\v18\read_center"
$MustKeep += "outputs\v18\daily_integrated"
$MustKeep += "outputs\v18\promotion_merge"
$MustKeep += "outputs\v18\outcome_summary"
$MustKeep += "outputs\v18\forward_outcome"
$MustKeep += "outputs\v18\factor_audit"
$MustKeep += "outputs\v18\factor_backtest"
$MustKeep += "outputs\v18\factor_pack"
$MustKeep += "outputs\v18\ops"

$CandidateDirs = @()

# PROTECTED_RUNTIME_DEPENDENCY: outputs\v16
# PROTECTED_RUNTIME_DEPENDENCY: outputs\v17
$CandidateDirs += "logs\v16"

$CandidateDirs += "outputs\v18\factor_lab"
$CandidateDirs += "outputs\v18\factor_shadow"
$CandidateDirs += "outputs\v18\factor_validation"
$CandidateDirs += "outputs\v18\manifests"
$CandidateDirs += "outputs\v18\cockpit"
$CandidateDirs += "outputs\v18\daily"

# PROTECTED_RUNTIME_DEPENDENCY: data\prices
# PROTECTED_RUNTIME_DEPENDENCY: data\events

$Rows = @()
$MoveFail = @()

foreach ($Rel in $CandidateDirs) {
    $Full = Join-Path $Root $Rel

    if (!(Test-Path $Full)) {
        continue
    }

    $Item = Get-Item $Full
    $Files = Get-ChildItem -Path $Full -Recurse -File -ErrorAction SilentlyContinue
    $FileCount = @($Files).Count
    $TotalBytes = 0

    foreach ($F in $Files) {
        $TotalBytes += $F.Length
    }

    $Rows += [pscustomobject]@{
        relative_path = $Rel
        full_path = $Full
        item_type = "directory"
        file_count = $FileCount
        size_mb = [math]::Round($TotalBytes / 1MB, 3)
        action = $(if ($Apply) { "MOVE_TO_ARCHIVE" } else { "DRYRUN_KEEP_IN_PLACE" })
    }
}

$Rows | Export-Csv -Path $ReportCsv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "=== CLEANUP CANDIDATES ==="

foreach ($Row in $Rows) {
    Write-Host ("{0} | files={1} | size_mb={2} | {3}" -f $Row.relative_path, $Row.file_count, $Row.size_mb, $Row.action)
}

if ($Apply) {
    New-Item -ItemType Directory -Force -Path $ArchiveRoot | Out-Null

    foreach ($Row in $Rows) {
        $Source = $Row.full_path
        $Rel = $Row.relative_path
        $Target = Join-Path $ArchiveRoot $Rel
        $TargetParent = Split-Path -Parent $Target

        try {
            New-Item -ItemType Directory -Force -Path $TargetParent | Out-Null
            Move-Item -Path $Source -Destination $Target -Force
            Write-Host "MOVED:" $Rel
        }
        catch {
            $MoveFail += "MOVE_FAIL: $Rel :: $($_.Exception.Message)"
            Write-Host "MOVE_FAIL:" $Rel
        }
    }
}
else {
    $ArchiveRoot = "DRYRUN_NOT_CREATED"
}

$Lines = @()
$Lines += "# V18.4K Workspace Cleanup Report"
$Lines += ""
$Lines += "Generated at: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")"
$Lines += ""
$Lines += "## 1. Mode"
$Lines += ""
$Lines += "- APPLY: $Apply"
$Lines += "- ARCHIVE_TARGET: $ArchiveRoot"
$Lines += "- FINAL_DAILY_COMMAND: $FinalDailyCommand"
$Lines += ""
$Lines += "## 2. Protected"
$Lines += ""

foreach ($K in $MustKeep) {
    $Lines += "- KEEP: $K"
}

$Lines += ""
$Lines += "## 3. Candidates"
$Lines += ""
$Lines += "| path | files | size_mb | action |"
$Lines += "|---|---:|---:|---|"

foreach ($Row in $Rows) {
    $Lines += "| $($Row.relative_path) | $($Row.file_count) | $($Row.size_mb) | $($Row.action) |"
}

$Lines += ""
$Lines += "## 4. Result"
$Lines += ""
$Lines += "- CANDIDATE_COUNT: $($Rows.Count)"
$Lines += "- MOVE_FAIL_COUNT: $($MoveFail.Count)"
$Lines += "- REPORT_CSV: $ReportCsv"

if ($MoveFail.Count -gt 0) {
    $Lines += ""
    $Lines += "## 5. Move Failures"
    foreach ($Fail in $MoveFail) {
        $Lines += "- $Fail"
    }
}

Set-Content -Path $ReportMd -Value $Lines -Encoding UTF8
Set-Content -Path $CurrentReport -Value $Lines -Encoding UTF8

Write-Host ""
Write-Host "=== V18.4K WORKSPACE CLEANUP READY ==="
Write-Host "APPLY:" $Apply
Write-Host "CANDIDATE_COUNT:" $Rows.Count
Write-Host "MOVE_FAIL_COUNT:" $MoveFail.Count
Write-Host "REPORT:" $ReportMd
Write-Host "CURRENT_REPORT:" $CurrentReport
Write-Host "CSV:" $ReportCsv
Write-Host "ARCHIVE_TARGET:" $ArchiveRoot

if ($MoveFail.Count -gt 0) {
    throw "Workspace cleanup completed with move failures. Check report."
}

Write-Host ""
Write-Host "=== V18.4K WORKSPACE CLEANUP DONE ==="
