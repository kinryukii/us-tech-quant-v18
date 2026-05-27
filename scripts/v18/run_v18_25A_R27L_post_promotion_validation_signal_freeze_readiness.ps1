[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27L_post_promotion_validation_signal_freeze_readiness.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27L_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27L POST-PROMOTION VALIDATION + SIGNAL-FREEZE READINESS ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_POST_PROMOTION_VALIDATION_SIGNAL_FREEZE_READINESS"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "R27L post-promotion validation + signal-freeze readiness failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27L POST-PROMOTION VALIDATION + SIGNAL-FREEZE READINESS ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
