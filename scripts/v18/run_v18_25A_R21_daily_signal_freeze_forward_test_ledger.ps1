[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 100,
    [switch]$DryRun,
    [switch]$AllowSameDayAppend,
    [switch]$AppendIntradayRun
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R21_daily_signal_freeze_forward_test_ledger.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R21_READ_FIRST.txt"

Write-Host "=== START V18.25A-R21 DAILY SIGNAL FREEZE / FORWARD TEST LEDGER ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "ALLOW_SAME_DAY_APPEND: $($AllowSameDayAppend.IsPresent -or $AppendIntradayRun.IsPresent)"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($AllowSameDayAppend.IsPresent -or $AppendIntradayRun.IsPresent) {
    $argsList += "--allow-same-day-append"
}

& $pythonExe @argsList

Write-Host "=== END V18.25A-R21 DAILY SIGNAL FREEZE / FORWARD TEST LEDGER ==="
Write-Host ""

if (Test-Path $readFirstPath) {
    $statusLine = Select-String -Path $readFirstPath -Pattern "^STATUS:" | Select-Object -First 1
    if ($statusLine) {
        Write-Host "FINAL $($statusLine.Line)"
    }
    Write-Host "READ_FIRST: $readFirstPath"
    Get-Content $readFirstPath
} else {
    Write-Host "FINAL STATUS: FAIL_V18_25A_R21_READ_FIRST_NOT_FOUND"
    Write-Host "READ_FIRST: $readFirstPath"
    exit 1
}
