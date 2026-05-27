[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_28A_R2_remaining_unknown_theme_patch.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_28A_R2_READ_FIRST.txt"

Write-Host "=== START V18.28A-R2 REMAINING UNKNOWN THEME PATCH ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: REMAINING_UNKNOWN_THEME_PATCH"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18.28A-R2 remaining UNKNOWN theme patch failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.28A-R2 REMAINING UNKNOWN THEME PATCH ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
