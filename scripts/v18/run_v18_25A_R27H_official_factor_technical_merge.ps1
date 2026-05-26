[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27H_official_factor_technical_merge.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27H_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27H OFFICIAL FACTOR + TECHNICAL MERGE ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_REQUESTED: $($Apply.IsPresent)"
Write-Host "MODE: $(if ($Apply.IsPresent) { 'APPLY_OFFICIAL_FACTOR_TECHNICAL_MERGE_WITH_BACKUP' } else { 'DRYRUN_OFFICIAL_FACTOR_TECHNICAL_MERGE_PLAN_ONLY' })"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($Apply.IsPresent) {
    $argsList += "--apply"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R27H official factor + technical merge failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27H OFFICIAL FACTOR + TECHNICAL MERGE ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
