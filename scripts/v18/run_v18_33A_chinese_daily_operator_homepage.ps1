[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_33A_chinese_daily_operator_homepage.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$homePath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_CHINESE_DAILY_HOMEPAGE.md"
$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_33A_READ_FIRST.txt"

Write-Host "=== START V18.33A CHINESE DAILY OPERATOR HOMEPAGE ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MODE: CHINESE_DAILY_OPERATOR_HOMEPAGE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.33A CHINESE DAILY OPERATOR HOMEPAGE ==="
Write-Host $statusLine
Write-Host "HOMEPAGE: $homePath"
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
