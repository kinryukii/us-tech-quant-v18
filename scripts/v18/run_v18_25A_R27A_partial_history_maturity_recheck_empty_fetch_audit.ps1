[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [string]$RunDate = ""
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27A_partial_history_maturity_recheck_empty_fetch_audit.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27A_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27A PARTIAL-HISTORY MATURITY RECHECK + EMPTY-FETCH AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_PARTIAL_HISTORY_MATURITY_RECHECK_EMPTY_FETCH_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @(
    $scriptPath,
    "--root", $Root
)
if ($RunDate.Trim()) {
    $argsList += @("--run-date", $RunDate)
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R27A partial-history maturity recheck + empty-fetch audit failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27A PARTIAL-HISTORY MATURITY RECHECK + EMPTY-FETCH AUDIT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
