param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== V18.14E-R1 STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "FORWARD_TRACKER_INTEGRATED: TRUE"
Write-Host "SNAPSHOT_ONLY: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_14E_R1_stable_snapshot.py"

if (-not (Test-Path $Python)) {
    throw "Missing Python interpreter: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Script"

& $Python $Script --root $Root
if ($LASTEXITCODE -ne 0) {
    throw "V18_14E_R1_STABLE_SNAPSHOT_FAILED"
}

$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_14E_R1_READ_FIRST.txt"
if (-not (Test-Path $ReadFirst)) {
    throw "Missing read-first output: $ReadFirst"
}

Write-Host ""
Write-Host "=== V18.14E-R1 STABLE SNAPSHOT DONE ==="
Write-Host ""
Write-Host "=== V18.14E-R1 READ FIRST ==="
Get-Content -Path $ReadFirst -Encoding UTF8
