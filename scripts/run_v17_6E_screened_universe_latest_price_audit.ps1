$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$PyScript = Join-Path $Root "scripts\run_v17_6E_screened_universe_latest_price_audit.py"

Write-Host ""
Write-Host "=== V17.6E SCREENED UNIVERSE LATEST PRICE AUDIT WRAPPER START ==="
Write-Host "ROOT: $Root"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $PyScript"
Write-Host ""

& $Python $PyScript
$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=== V17.6E READ FIRST ==="
$ReadFirst = Join-Path $Root "outputs\v17\price\V17_6E_READ_FIRST.txt"
if (Test-Path $ReadFirst) {
    Get-Content $ReadFirst
}

$Report = Join-Path $Root "outputs\v17\price\V17_6E_SCREENED_UNIVERSE_LATEST_PRICE_AUDIT.md"
if (Test-Path $Report) {
    code $Report
}

Write-Host ""
Write-Host "=== V17.6E SCREENED UNIVERSE LATEST PRICE AUDIT WRAPPER DONE ==="
exit $ExitCode
