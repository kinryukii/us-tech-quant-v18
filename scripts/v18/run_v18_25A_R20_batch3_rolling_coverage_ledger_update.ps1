[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "v18_25A_R20_batch3_rolling_coverage_ledger_update.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "=== START V18.25A-R20 BATCH3 ROLLING COVERAGE LEDGER UPDATE ==="
& $pythonExe $scriptPath --root $Root
Write-Host "=== END V18.25A-R20 BATCH3 ROLLING COVERAGE LEDGER UPDATE ==="
Write-Host ""
Get-Content (Join-Path $Root "outputs\v18\ops\V18_25A_R20_READ_FIRST.txt")
