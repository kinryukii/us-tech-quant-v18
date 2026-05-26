[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "v18_25A_R19_official_price_integration_batch3_full_history.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "=== START V18.25A-R19 OFFICIAL BATCH3 FULL-HISTORY PRICE CACHE INTEGRATION ==="
& $pythonExe $scriptPath --root $Root
Write-Host "=== END V18.25A-R19 OFFICIAL BATCH3 FULL-HISTORY PRICE CACHE INTEGRATION ==="
Write-Host ""
Get-Content (Join-Path $Root "outputs\v18\ops\V18_25A_R19_READ_FIRST.txt")
