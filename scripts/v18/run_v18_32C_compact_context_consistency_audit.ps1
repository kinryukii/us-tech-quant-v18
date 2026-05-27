[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [switch]$Patch32B
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_32C_compact_context_consistency_audit.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_32C_READ_FIRST.txt"
$reportPath = Join-Path $Root "outputs\v18\read_center\V18_32C_CONTEXT_CONSISTENCY_REPORT.md"
$contextPath = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_CONTEXT_CONSISTENCY.md"
$projectContextPath = Join-Path $Root "outputs\v18\ops\V18_PROJECT_CONTEXT_COMPACT.md"

Write-Host "=== START V18.32C CONTEXT CONSISTENCY AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "PATCH32B: $($Patch32B.IsPresent)"
Write-Host "MODE: V18_32C_CONTEXT_CONSISTENCY_AUDIT"
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
if ($Patch32B.IsPresent) {
    $argsList += "--patch32b"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== DONE V18.32C CONTEXT CONSISTENCY AUDIT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "REPORT: $reportPath"
Write-Host "CONTEXT: $contextPath"
Write-Host "PROJECT_CONTEXT: $projectContextPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
