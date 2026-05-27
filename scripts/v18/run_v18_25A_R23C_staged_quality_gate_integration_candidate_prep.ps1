[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MinRowsFullHistory = 500,
    [switch]$AllowPartialHistoryIntegration
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R23C_staged_quality_gate_integration_candidate_prep.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R23C_READ_FIRST.txt"

Write-Host "=== START V18.25A-R23C STAGED QUALITY GATE INTEGRATION CANDIDATE PREP ==="
Write-Host "ROOT: $Root"
Write-Host "MIN_ROWS_FULL_HISTORY: $MinRowsFullHistory"
Write-Host "ALLOW_PARTIAL_HISTORY_INTEGRATION: $($AllowPartialHistoryIntegration.IsPresent)"
Write-Host "MODE: READ_ONLY_STAGED_QUALITY_GATE"
if ($AllowPartialHistoryIntegration.IsPresent) {
    Write-Host "R23C refuses partial-history integration. Partial-history policy must be handled separately."
}

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--min-rows-full-history", $MinRowsFullHistory
)
if ($AllowPartialHistoryIntegration.IsPresent) {
    $argsList += "--allow-partial-history-integration"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R23C staged quality gate failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R23C STAGED QUALITY GATE INTEGRATION CANDIDATE PREP ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
