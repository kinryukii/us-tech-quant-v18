param(
    [switch]$UseYFinance,
    [switch]$FullDaily,
    [switch]$ReadCenterRefreshOnly,
    [switch]$ValidateOnly,
    [switch]$RunForwardTracker,
    [int]$MaxRank = 20
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Current = Join-Path $Root "scripts\v18\run_v18_current_daily_command_center.ps1"
$Run14C = Join-Path $Root "scripts\v18\run_v18_14C_ranked_candidate_forward_tracker.ps1"
$Run14D = Join-Path $Root "scripts\v18\run_v18_14D_ranked_candidate_forward_price_filler.ps1"
$Script14E = Join-Path $Root "scripts\v18\v18_14E_current_daily_with_forward_tracker.py"

foreach ($Required in @($Python, $Current, $Run14C, $Run14D, $Script14E)) {
    if (-not (Test-Path $Required)) {
        throw "Missing required file: $Required"
    }
}

$Mode = "READ_CENTER_REFRESH_ONLY"
if ($ValidateOnly) {
    $Mode = "VALIDATE_ONLY"
}
elseif ($FullDaily) {
    $Mode = "FULL_DAILY"
}
elseif ($ReadCenterRefreshOnly) {
    $Mode = "READ_CENTER_REFRESH_ONLY"
}

Write-Host "=== V18.14E CURRENT DAILY WITH FORWARD TRACKER START ==="
Write-Host "MODE: $Mode"
Write-Host "RUN_FORWARD_TRACKER: $RunForwardTracker"
Write-Host "MAX_RANK: $MaxRank"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "FORWARD_TRACKER_INTEGRATED: TRUE"

$CurrentArgs = @()
if ($FullDaily) { $CurrentArgs += "-FullDaily" }
if ($ReadCenterRefreshOnly) { $CurrentArgs += "-ReadCenterRefreshOnly" }
if ($ValidateOnly) { $CurrentArgs += "-ValidateOnly" }
if ($UseYFinance -and $FullDaily) { $CurrentArgs += "-UseYFinance" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $Current @CurrentArgs
if ($LASTEXITCODE -ne 0) {
    throw "V18_CURRENT_DAILY_COMMAND_CENTER_FAILED"
}

$ForwardRun = "SKIPPED"
if ($RunForwardTracker) {
    $ForwardRun = "RAN"
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run14C -MaxRank $MaxRank
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_14C_FORWARD_TRACKER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }

    $DArgs = @()
    if ($UseYFinance -and $FullDaily) {
        $DArgs += "-UseYFinance"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File $Run14D @DArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "V18_14D_FORWARD_PRICE_FILLER_STATUS: NONZERO_EXIT_$LASTEXITCODE"
    }
}

& $Python $Script14E --root $Root --mode $Mode --forward-tracker-run $ForwardRun
exit $LASTEXITCODE
