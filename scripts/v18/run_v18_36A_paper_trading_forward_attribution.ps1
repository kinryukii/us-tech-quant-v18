param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UpdatePaperTradingLedger,
    [switch]$UseYFinanceForPaperTradingPrices
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_36A_paper_trading_forward_attribution.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_36A_READ_FIRST.txt"

Write-Host "=== START V18.36A PAPER TRADING FORWARD ATTRIBUTION ==="
Write-Host "ROOT: $Root"
Write-Host "UPDATE_PAPER_TRADING_LEDGER: $UpdatePaperTradingLedger"
Write-Host "USE_YFINANCE_FOR_PAPER_TRADING_PRICES: $UseYFinanceForPaperTradingPrices"
Write-Host "PAPER_TRADING_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_36A_PAPER_TRADING_FORWARD_ATTRIBUTION_FAILED"
    throw "Missing script: $Script"
}

$Args36A = @("--root", $Root)
if ($UpdatePaperTradingLedger) { $Args36A += "--update-paper-trading-ledger" }
if ($UseYFinanceForPaperTradingPrices) { $Args36A += "--use-yfinance-for-paper-trading-prices" }

& $Python $Script @Args36A
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.36A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.36A PAPER TRADING FORWARD ATTRIBUTION ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
