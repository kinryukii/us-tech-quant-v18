param(
    [switch]$SkipAudit,
    [switch]$SkipCloudEvents
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$V18 = Join-Path $Root "scripts\v18"

$Audit = Join-Path $V18 "run_v18_4C_runtime_dependency_audit.ps1"
$CloudEvents = Join-Path $V18 "run_v18_4C_cloud_earnings_event_update.ps1"
$OldFinal = Join-Path $V18 "run_v18_4B_R1_final_daily_wrapper.ps1"

Write-Host ""
Write-Host "=== V18.4C-R1 FINAL DAILY WRAPPER START ==="

if (-not $SkipAudit) {
    Write-Host ""
    Write-Host "STEP 1: runtime dependency audit"
    powershell -NoProfile -ExecutionPolicy Bypass -File $Audit -Root $Root -Entry $OldFinal
}

if (-not $SkipCloudEvents) {
    Write-Host ""
    Write-Host "STEP 2: cloud earnings event update"
    powershell -NoProfile -ExecutionPolicy Bypass -File $CloudEvents -Root $Root
}

Write-Host ""
Write-Host "STEP 3: upstream V18.4B-R1 final daily chain"
powershell -NoProfile -ExecutionPolicy Bypass -File $OldFinal

Write-Host ""
Write-Host "=== V18.4C-R1 FINAL DAILY WRAPPER DONE ==="
Write-Host "NEXT DAILY COMMAND:"
Write-Host "powershell -NoProfile -ExecutionPolicy Bypass -File `"D:\us-tech-quant\scripts\v18\run_v18_4C_R1_final_daily_wrapper.ps1`""
