param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$rootPath = (Resolve-Path $Root).Path
$python = Join-Path $rootPath ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    $python = "python"
}

$scriptPath = Join-Path $rootPath "scripts\v18\v18_25A_R3_post_integration_promotion_blocker_audit.py"
$readFirstPath = Join-Path $rootPath "outputs\v18\ops\V18_25A_R3_READ_FIRST.txt"

Write-Host "=== V18.25A-R3 POST-INTEGRATION PROMOTION BLOCKER AUDIT START ==="
Write-Host "ROOT: $rootPath"
Write-Host "MODE: READ_ONLY_POST_INTEGRATION_PROMOTION_BLOCKER_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "BACKTEST_EXECUTED: FALSE"
Write-Host "PYTHON: $python"
Write-Host "PYTHON_SCRIPT: $scriptPath"

& $python $scriptPath
$exitCode = $LASTEXITCODE

if (Test-Path $readFirstPath) {
    Write-Host "=== V18.25A-R3 READ_FIRST CONTENT ==="
    Get-Content $readFirstPath
} else {
    Write-Host "READ_FIRST_MISSING: $readFirstPath"
}

Write-Host "=== V18.25A-R3 POST-INTEGRATION PROMOTION BLOCKER AUDIT END ==="
exit $exitCode
