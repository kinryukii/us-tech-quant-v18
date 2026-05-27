param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$ScriptPath = Join-Path $Root "scripts\v18\v18_25A_R7_local_market_proxy_coverage_repair_audit.py"
$ReadFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R7_READ_FIRST.txt"

Write-Host "===== START V18.25A-R7 LOCAL MARKET PROXY / VIX COVERAGE REPAIR AUDIT ====="
Write-Host "ROOT: $Root"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $ScriptPath"

& $Python $ScriptPath
if ($LASTEXITCODE -ne 0) {
    throw "R7 audit script failed with exit code $LASTEXITCODE"
}

Write-Host "===== END V18.25A-R7 LOCAL MARKET PROXY / VIX COVERAGE REPAIR AUDIT ====="
Write-Host "===== READ FIRST ====="
Get-Content -Path $ReadFirstPath
