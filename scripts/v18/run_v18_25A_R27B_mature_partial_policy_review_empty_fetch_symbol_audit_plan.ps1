[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R27B_mature_partial_policy_review_empty_fetch_symbol_audit_plan.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R27B_READ_FIRST.txt"

Write-Host "=== START V18.25A-R27B MATURE PARTIAL POLICY REVIEW + EMPTY-FETCH SYMBOL AUDIT PLAN ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_PLAN_ONLY_MATURE_PARTIAL_POLICY_REVIEW_EMPTY_FETCH_SYMBOL_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $pythonExe $scriptPath --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "R27B mature partial policy review + empty-fetch symbol audit plan failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R27B MATURE PARTIAL POLICY REVIEW + EMPTY-FETCH SYMBOL AUDIT PLAN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
