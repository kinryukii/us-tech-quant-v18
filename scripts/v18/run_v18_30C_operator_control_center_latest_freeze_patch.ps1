[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_30C_operator_control_center_latest_freeze_patch.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_30C_READ_FIRST.txt"

Write-Host "=== START V18.30C OPERATOR CONTROL CENTER LATEST FREEZE PATCH ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: OPERATOR_CONTROL_CENTER_LATEST_FREEZE_SOURCE_PATCH"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.30C operator control center latest freeze patch failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.30C OPERATOR CONTROL CENTER LATEST FREEZE PATCH ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
