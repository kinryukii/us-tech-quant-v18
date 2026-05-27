[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [switch]$DryRun,
    [switch]$ForceSnapshot,
    [switch]$SkipR21,
    [switch]$SkipR29C,
    [switch]$StopOnWarn
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_30E_safe_daily_operator_sequence.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_30E_READ_FIRST.txt"

Write-Host "=== START V18.30E SAFE DAILY OPERATOR SEQUENCE ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "FORCE_SNAPSHOT: $($ForceSnapshot.IsPresent)"
Write-Host "SKIP_R21: $($SkipR21.IsPresent)"
Write-Host "SKIP_R29C: $($SkipR29C.IsPresent)"
Write-Host "STOP_ON_WARN: $($StopOnWarn.IsPresent)"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($ForceSnapshot.IsPresent) {
    $argsList += "--force-snapshot"
}
if ($SkipR21.IsPresent) {
    $argsList += "--skip-r21"
}
if ($SkipR29C.IsPresent) {
    $argsList += "--skip-r29c"
}
if ($StopOnWarn.IsPresent) {
    $argsList += "--stop-on-warn"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.30E SAFE DAILY OPERATOR SEQUENCE ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
