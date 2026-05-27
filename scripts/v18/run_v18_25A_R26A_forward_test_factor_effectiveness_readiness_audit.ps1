[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 250,
    [int]$SignalLookbackDays = 30
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R26A_forward_test_factor_effectiveness_readiness_audit.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R26A_READ_FIRST.txt"

Write-Host "=== START V18.25A-R26A FORWARD-TEST FACTOR EFFECTIVENESS READINESS AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "SIGNAL_LOOKBACK_DAYS: $SignalLookbackDays"
Write-Host "MODE: READ_ONLY_FORWARD_TEST_FACTOR_EFFECTIVENESS_READINESS_AUDIT"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--top-n", $TopN,
    "--signal-lookback-days", $SignalLookbackDays
)

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R26A readiness audit failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R26A FORWARD-TEST FACTOR EFFECTIVENESS READINESS AUDIT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
