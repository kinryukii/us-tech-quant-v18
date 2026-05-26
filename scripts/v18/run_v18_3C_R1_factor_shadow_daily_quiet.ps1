param([switch]$Force)
$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$Python = if (Test-Path "$Root\.venv\Scripts\python.exe") { "$Root\.venv\Scripts\python.exe" } else { "python" }
$OutDir = "$Root\outputs\v18\factor_shadow"
$OpsDir = "$Root\outputs\v18\ops"
$ReadFirst = "$OutDir\V18_3C_R1_READ_FIRST.txt"
$Marker = "$OutDir\V18_3C_R1_LAST_RUN.json"
$Today = Get-Date -Format "yyyy-MM-dd"
$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$UpstreamLog = "$OpsDir\V18_3C_R1_upstream_$Stamp.log"
New-Item -ItemType Directory -Force $OutDir | Out-Null
New-Item -ItemType Directory -Force $OpsDir | Out-Null

function Get-CurrentSummary {
    $CompareCsv = "$OutDir\V18_3B_R2_SHADOW_OFFICIAL_COMPARE_CURRENT.csv"
    $ShadowCsv = "$OutDir\V18_3A_FACTOR_SHADOW_DAILY_CURRENT.csv"
    $Result = [ordered]@{
        selected_factors = "UNKNOWN"
        shadow_name_count = 0
        top1 = "UNKNOWN"
        overlap_count = 0
        overlap_names = "NONE"
        shadow_top30_only_count = 0
        official_not_shadow_top30_count = 0
    }
    if (Test-Path $ShadowCsv) {
        $Shadow = @(Import-Csv $ShadowCsv)
        $Result.shadow_name_count = $Shadow.Count
        if ($Shadow.Count -gt 0) {
            $Top = $Shadow | Sort-Object {[int]$_.shadow_rank} | Select-Object -First 1
            $Result.top1 = $Top.ticker
            $Result.selected_factors = $Top.shadow_factor_ids
        }
    }
    if (Test-Path $CompareCsv) {
        $Cmp = @(Import-Csv $CompareCsv)
        $Overlap = @($Cmp | Where-Object {$_.compare_bucket -eq "SHADOW_TOP30_AND_OFFICIAL_REVIEW"})
        $TopOnly = @($Cmp | Where-Object {$_.compare_bucket -eq "SHADOW_TOP30_ONLY"})
        $OffNotTop = @($Cmp | Where-Object {$_.compare_bucket -eq "OFFICIAL_REVIEW_NOT_SHADOW_TOP30"})
        $Result.overlap_count = $Overlap.Count
        $Result.overlap_names = if ($Overlap.Count -gt 0) { ($Overlap.ticker -join ",") } else { "NONE" }
        $Result.shadow_top30_only_count = $TopOnly.Count
        $Result.official_not_shadow_top30_count = $OffNotTop.Count
    }
    return [pscustomobject]$Result
}

function Write-QuietReadFirst {
    param([string]$Status, [string]$LogPath, [string]$Mode)
    $S = Get-CurrentSummary
    $Lines = @(
        "=== V18.3C-R1 FACTOR SHADOW DAILY QUIET READ FIRST ===",
        "",
        "STATUS:",
        $Status,
        "",
        "MODE:",
        $Mode,
        "",
        "OFFICIAL_DECISION_IMPACT:",
        "NONE",
        "",
        "PROMOTION_ACTION:",
        "NONE",
        "",
        "SUMMARY:",
        "SELECTED_FACTORS: $($S.selected_factors)",
        "SHADOW_NAME_COUNT: $($S.shadow_name_count)",
        "TOP1: $($S.top1)",
        "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: $($S.overlap_count)",
        "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: $($S.overlap_names)",
        "SHADOW_TOP30_ONLY_COUNT: $($S.shadow_top30_only_count)",
        "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: $($S.official_not_shadow_top30_count)",
        "",
        "OUTPUTS:",
        "$OutDir\V18_3A_READ_FIRST.txt",
        "$OutDir\V18_3B_R2_READ_FIRST.txt",
        "$OutDir\V18_3B_R2_SHADOW_OFFICIAL_COMPARE_REPORT.md",
        "$Root\state\v18\factor_shadow_outcome_tracker.csv",
        $LogPath,
        "",
        "NEXT_STEP:",
        "Run V18.4A only after enough forward trading days are available.",
        "",
        "IMPORTANT:",
        "This wrapper is shadow-only. It does not promote factors and does not change official BUY / NO_BUY."
    )
    Set-Content -Path $ReadFirst -Value $Lines -Encoding UTF8
}

function Show-Summary {
    $S = Get-CurrentSummary
    Write-Host "V18_3C_R1_STATUS: OK_FACTOR_SHADOW_DAILY_QUIET_READY"
    Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
    Write-Host "PROMOTION_ACTION: NONE"
    Write-Host "SELECTED_FACTORS: $($S.selected_factors)"
    Write-Host "TOP1: $($S.top1)"
    Write-Host "SHADOW_TOP30_AND_OFFICIAL_REVIEW_COUNT: $($S.overlap_count)"
    Write-Host "SHADOW_TOP30_AND_OFFICIAL_REVIEW_NAMES: $($S.overlap_names)"
    Write-Host "SHADOW_TOP30_ONLY_COUNT: $($S.shadow_top30_only_count)"
    Write-Host "OFFICIAL_REVIEW_NOT_SHADOW_TOP30_COUNT: $($S.official_not_shadow_top30_count)"
    Write-Host ""
    Write-Host "READ_FIRST:"
    Write-Host $ReadFirst
}

Write-Host ""
Write-Host "=== V18.3C-R1 FACTOR SHADOW DAILY QUIET WRAPPER START ==="
Write-Host ""

if ((Test-Path $Marker) -and (-not $Force)) {
    try {
        $M = Get-Content -Raw $Marker | ConvertFrom-Json
        if ($M.run_date -eq $Today -and $M.status -eq "OK") {
            Write-QuietReadFirst -Status "V18_3C_R1_STATUS: OK_ALREADY_RAN_TODAY_SKIPPED_UPSTREAM" -LogPath $M.upstream_log -Mode "SKIP_ALREADY_RAN_TODAY"
            Write-Host "SKIP_REASON: ALREADY_RAN_TODAY"
            Write-Host "USE_FORCE_TO_REFRESH: powershell -NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`" -Force"
            Write-Host ""
            Show-Summary
            Write-Host ""
            Write-Host "=== V18.3C-R1 FACTOR SHADOW DAILY QUIET WRAPPER DONE ==="
            exit 0
        }
    } catch {
        Write-Host "WARN: MARKER_READ_FAILED_CONTINUE_RUN"
    }
}

$Step1 = "$Root\scripts\v18\run_v18_1B_factor_value_compute.ps1"
$Py3A = "$Root\src\v18\factor_lab\run_v18_3A_factor_shadow_daily.py"
$Py3B = "$Root\src\v18\factor_lab\run_v18_3B_R2_strict_fallback_compare.py"
foreach ($P in @($Step1, $Py3A, $Py3B)) {
    if (!(Test-Path $P)) { throw "MISSING_REQUIRED_STEP: $P" }
}

Write-Host "RUN_MODE: QUIET"
Write-Host "UPSTREAM_LOG:"
Write-Host $UpstreamLog
Write-Host ""

& powershell -NoProfile -ExecutionPolicy Bypass -File $Step1 *> $UpstreamLog
if ($LASTEXITCODE -ne 0) { throw "V18_1B_FAILED_SEE_LOG: $UpstreamLog" }

foreach ($Py in @($Py3A, $Py3B)) {
    & $Python -m py_compile $Py *>> $UpstreamLog
    if ($LASTEXITCODE -ne 0) { throw "PY_PARSE_FAILED_SEE_LOG: $Py $UpstreamLog" }
    & $Python $Py *>> $UpstreamLog
    if ($LASTEXITCODE -ne 0) { throw "PY_RUN_FAILED_SEE_LOG: $Py $UpstreamLog" }
}

$MarkerObj = [ordered]@{
    run_date = $Today
    status = "OK"
    generated_at = (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
    upstream_log = $UpstreamLog
    read_first = $ReadFirst
}
$MarkerObj | ConvertTo-Json -Depth 5 | Set-Content -Path $Marker -Encoding UTF8

Write-QuietReadFirst -Status "V18_3C_R1_STATUS: OK_FACTOR_SHADOW_DAILY_QUIET_READY" -LogPath $UpstreamLog -Mode "RUN_UPSTREAM_QUIET"
Show-Summary
Write-Host ""
Write-Host "UPSTREAM_LOG:"
Write-Host $UpstreamLog
Write-Host ""
Write-Host "=== V18.3C-R1 FACTOR SHADOW DAILY QUIET WRAPPER DONE ==="
