[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27C_controlled_partial_mature_integration_dryrun.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27C_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27C CONTROLLED PARTIAL-MATURE INTEGRATION DRY RUN ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN_CONTROLLED_PARTIAL_MATURE_INTEGRATION_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "R27C controlled partial mature integration dry run failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27C CONTROLLED PARTIAL-MATURE INTEGRATION DRY RUN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
