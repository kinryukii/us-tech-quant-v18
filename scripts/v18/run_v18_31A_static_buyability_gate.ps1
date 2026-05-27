[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 252,
    [switch]$DryRun,
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_31A_static_buyability_gate.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_31A_READ_FIRST.txt"

Write-Host "=== START V18.31A STATIC BUYABILITY GATE ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "STRICT: $($Strict.IsPresent)"
Write-Host "MODE: STATIC_MANUAL_BUYABILITY_GATE"
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
if ($Strict.IsPresent) {
    $argsList += "--strict"
}

& $pythonExe @argsList
$pythonExit = $LASTEXITCODE

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.31A STATIC BUYABILITY GATE ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"

if ($pythonExit -ne 0) {
    exit $pythonExit
}
