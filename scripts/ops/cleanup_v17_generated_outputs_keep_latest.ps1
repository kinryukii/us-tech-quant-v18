param(
    [switch]$Apply,
    [int]$KeepLatest = 2
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

Write-Host ""
Write-Host "=== CLEANUP V17 GENERATED OUTPUTS START ==="
Write-Host "MODE: $(if ($Apply) { 'APPLY_DELETE' } else { 'DRY_RUN_ONLY' })"
Write-Host "KEEP_LATEST_PER_PATTERN: $KeepLatest"

$Targets = @(
    @{
        Dir = "$Root\outputs\v17\manual_daily"
        Patterns = @(
            "V17_6F_E_MANUAL_DAILY_STABLE_*.txt",
            "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_*.txt",
            "V17_7G_R1_DYNAMIC_RAW105_MANUAL_DAILY_*.md",
            "v17_6F_E_full_universe_chain_*.log",
            "v17_6F_E_price_audit_*.log",
            "v17_6F_E_official_daily_*.log",
            "v17_7G_R1_steps_*.csv"
        )
    },
    @{
        Dir = "$Root\outputs\v17\raw105_decision"
        Patterns = @(
            "V17_8B_RAW105_FULL_DECISION_READABLE_PANEL_*.txt"
        )
    }
)

$DeleteList = New-Object System.Collections.Generic.List[object]

foreach ($target in $Targets) {
    $dir = $target.Dir

    if (-not (Test-Path $dir)) {
        continue
    }

    foreach ($pattern in $target.Patterns) {
        $files = Get-ChildItem -Path $dir -Filter $pattern -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending

        $keep = @($files | Select-Object -First $KeepLatest)
        $remove = @($files | Select-Object -Skip $KeepLatest)

        foreach ($f in $remove) {
            $DeleteList.Add([pscustomobject]@{
                Pattern = $pattern
                LastWriteTime = $f.LastWriteTime
                LengthMB = [math]::Round($f.Length / 1MB, 3)
                FullName = $f.FullName
            })
        }
    }
}

$TotalCount = $DeleteList.Count
$TotalMB = [math]::Round((($DeleteList | Measure-Object LengthMB -Sum).Sum), 3)

Write-Host ""
Write-Host "=== CLEANUP CANDIDATES ==="
Write-Host "DELETE_CANDIDATE_COUNT: $TotalCount"
Write-Host "APPROX_DELETE_MB: $TotalMB"

if ($TotalCount -gt 0) {
    $DeleteList |
        Sort-Object FullName |
        Format-Table Pattern, LastWriteTime, LengthMB, FullName -AutoSize
}

$ReportDir = "$Root\outputs\v17\ops"
New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$ReportCsv = "$ReportDir\v17_cleanup_generated_outputs_$Stamp.csv"
$DeleteList | Export-Csv -Path $ReportCsv -NoTypeInformation -Encoding UTF8

Write-Host ""
Write-Host "REPORT:"
Write-Host $ReportCsv

if (-not $Apply) {
    Write-Host ""
    Write-Host "DRY RUN ONLY. No files deleted."
    Write-Host "To actually delete, run:"
    Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Apply"
    Write-Host ""
    Write-Host "=== CLEANUP V17 GENERATED OUTPUTS DRY RUN DONE ==="
    exit 0
}

foreach ($item in $DeleteList) {
    try {
        Remove-Item -Path $item.FullName -Force
        Write-Host "DELETED: $($item.FullName)"
    } catch {
        Write-Host "DELETE_FAILED: $($item.FullName)"
    }
}

Write-Host ""
Write-Host "=== CLEANUP V17 GENERATED OUTPUTS APPLY DONE ==="
Write-Host "DELETED_COUNT: $TotalCount"
Write-Host "APPROX_DELETED_MB: $TotalMB"
