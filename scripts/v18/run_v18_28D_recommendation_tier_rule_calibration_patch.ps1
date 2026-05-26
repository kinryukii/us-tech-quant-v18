[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_28D_recommendation_tier_rule_calibration_patch.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_28D_READ_FIRST.txt"

Write-Host "=== START V18.28D RECOMMENDATION TIER RULE CALIBRATION PATCH ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: RECOMMENDATION_TIER_RULE_CALIBRATION_PATCH"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.28D recommendation tier rule calibration patch failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.28D RECOMMENDATION TIER RULE CALIBRATION PATCH ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
