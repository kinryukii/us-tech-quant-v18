[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$scriptPath = Join-Path $PSScriptRoot "v18_25A_R18_batch3_staged_quality_audit_integration_gate.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "=== START V18.25A-R18 BATCH3 STAGED QUALITY AUDIT / INTEGRATION GATE ==="
& $pythonExe $scriptPath --root $Root
Write-Host "=== END V18.25A-R18 BATCH3 STAGED QUALITY AUDIT / INTEGRATION GATE ==="
Write-Host ""
Get-Content (Join-Path $Root "outputs\v18\ops\V18_25A_R18_READ_FIRST.txt")
