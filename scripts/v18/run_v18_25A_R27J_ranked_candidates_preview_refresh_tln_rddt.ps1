[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27J_ranked_candidates_preview_refresh_tln_rddt.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27J_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27J RANKED CANDIDATES PREVIEW REFRESH ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: PREVIEW_ONLY_RANKED_CANDIDATES_REFRESH"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "R27J ranked candidates preview refresh failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27J RANKED CANDIDATES PREVIEW REFRESH ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
