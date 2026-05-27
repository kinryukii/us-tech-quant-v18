[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$RefreshChineseHomepage
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_33B_daily_operator_runbook.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$runbookPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_DAILY_OPERATOR_RUNBOOK_CN.md"
$homepagePath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_33B_READ_FIRST.txt"
$refreshWrapper = Join-Path $Root "scripts\v18\run_v18_33A_chinese_daily_operator_homepage.ps1"

Write-Host "=== START V18.33B DAILY OPERATOR RUNBOOK ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "REFRESH_CHINESE_HOMEPAGE: $($RefreshChineseHomepage.IsPresent)"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

if ($RefreshChineseHomepage.IsPresent -and -not $DryRun.IsPresent) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File $refreshWrapper
    $refreshExit = $LASTEXITCODE
    if ($refreshExit -ne 0) {
        Write-Host "V18_33A_REFRESH_STATUS: NONZERO_EXIT_$refreshExit"
        Write-Host "=== DONE V18.33B DAILY OPERATOR RUNBOOK ==="
        Write-Host "RUNBOOK: $runbookPath"
        Write-Host "HOME: $homepagePath"
        Write-Host "READ_FIRST: $readFirstPath"
        exit $refreshExit
    }
}

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($RefreshChineseHomepage.IsPresent) {
    $argsList += "--refresh-chinese-homepage"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.33B DAILY OPERATOR RUNBOOK ==="
Write-Host $statusLine
Write-Host "RUNBOOK: $runbookPath"
Write-Host "HOME: $homepagePath"
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
