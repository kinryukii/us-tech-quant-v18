[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27F_build_staged_factor_technical_rows_tln_rddt.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27F_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27F STAGED FACTOR + TECHNICAL BUILD ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: STAGED_BUILD_ONLY"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "R27F staged factor + technical build failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27F STAGED FACTOR + TECHNICAL BUILD ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
