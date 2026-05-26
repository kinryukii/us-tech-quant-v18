$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
Set-Location $Root

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (!(Test-Path $Python)) {
    $Python = "python"
}

$PyScript = Join-Path $Root "scripts\run_v17_6A_full_universe_latest_price_audit.py"

Write-Host ""
Write-Host "=== V17.6A FULL UNIVERSE LATEST PRICE AUDIT WRAPPER START ==="
Write-Host "ROOT: $Root"
Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $PyScript"
Write-Host ""

& $Python $PyScript
$ExitCode = $LASTEXITCODE

Write-Host ""
Write-Host "=== V17.6A READ FIRST ==="
$ReadFirst = Join-Path $Root "outputs\v17\price\V17_6A_READ_FIRST.txt"
if (Test-Path $ReadFirst) {
    Get-Content $ReadFirst
}

$Report = Join-Path $Root "outputs\v17\price\V17_6A_FULL_UNIVERSE_LATEST_PRICE_AUDIT.md"
if (Test-Path $Report) {
    code $Report
}

Write-Host ""
Write-Host "=== V17.6A FULL UNIVERSE LATEST PRICE AUDIT WRAPPER DONE ==="
exit $ExitCode
