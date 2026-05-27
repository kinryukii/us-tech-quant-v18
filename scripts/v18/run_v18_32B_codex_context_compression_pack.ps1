[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_32B_codex_context_compression_pack.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_32B_READ_FIRST.txt"
$projectContextPath = Join-Path $Root "outputs\v18\ops\V18_PROJECT_CONTEXT_COMPACT.md"
$safetyContractPath = Join-Path $Root "docs\v18\V18_CODEX_SAFETY_CONTRACT.md"
$taskTemplatePath = Join-Path $Root "docs\v18\V18_CODEX_TASK_TEMPLATE.md"

Write-Host "=== START V18.32B CODEX CONTEXT COMPRESSION PACK ==="
Write-Host "ROOT: $Root"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MODE: CODEX_CONTEXT_COMPRESSION_PACK"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "BROKER_API_CALLS: NOT_EXECUTED"
Write-Host "ORDER_PLACEMENT: NOT_EXECUTED"
Write-Host "EXTERNAL_DATA_FETCH: NOT_EXECUTED"
Write-Host "HEAVY_DAILY_PIPELINE_STEPS: NOT_EXECUTED"

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

Write-Host "=== DONE V18.32B CODEX CONTEXT COMPRESSION PACK ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
Write-Host "PROJECT_CONTEXT: $projectContextPath"
Write-Host "SAFETY_CONTRACT: $safetyContractPath"
Write-Host "TASK_TEMPLATE: $taskTemplatePath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
if ($statusLine -match '^STATUS:\s*FAIL') {
    exit 1
}
