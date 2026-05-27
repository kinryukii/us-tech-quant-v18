param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$rootPath = (Resolve-Path $Root).Path
$python = Join-Path $rootPath ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$scriptPath = Join-Path $rootPath "scripts\v18\v18_25A_R4_integrated_tickers_factor_technical_refresh_readiness_audit.py"
$readFirstPath = Join-Path $rootPath "outputs\v18\ops\V18_25A_R4_READ_FIRST.txt"

Write-Host "=== V18.25A-R4 INTEGRATED TICKERS FACTOR / TECHNICAL REFRESH READINESS AUDIT START ==="
Write-Host "ROOT: $rootPath"
Write-Host "MODE: READ_ONLY_INTEGRATED_TICKERS_FACTOR_TECHNICAL_REFRESH_READINESS_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "BACKTEST_EXECUTED: FALSE"
Write-Host "PYTHON: $python"
Write-Host "PYTHON_SCRIPT: $scriptPath"

& $python -m py_compile $scriptPath
if ($LASTEXITCODE -ne 0) {
    throw "Python compile check failed for $scriptPath"
}

& $python $scriptPath --root $rootPath
$exitCode = $LASTEXITCODE

if (-not (Test-Path -LiteralPath $readFirstPath)) {
    throw "Missing READ_FIRST output: $readFirstPath"
}

Write-Host "=== V18.25A-R4 READ_FIRST CONTENT ==="
Get-Content -LiteralPath $readFirstPath | ForEach-Object { Write-Host $_ }

Write-Host "=== V18.25A-R4 INTEGRATED TICKERS FACTOR / TECHNICAL REFRESH READINESS AUDIT END ==="
exit $exitCode
