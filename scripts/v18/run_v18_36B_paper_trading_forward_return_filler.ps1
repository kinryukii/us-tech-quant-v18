param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UpdatePaperTradingForwardReturns,
    [switch]$UseYFinanceForPaperForwardPrices
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_36B_paper_trading_forward_return_filler.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_36B_READ_FIRST.txt"

Write-Host "=== START V18.36B PAPER FORWARD RETURN FILLER ==="
Write-Host "ROOT: $Root"
Write-Host "UPDATE_PAPER_TRADING_FORWARD_RETURNS: $UpdatePaperTradingForwardReturns"
Write-Host "USE_YFINANCE_FOR_PAPER_FORWARD_PRICES: $UseYFinanceForPaperForwardPrices"
Write-Host "PAPER_TRADING_ONLY: TRUE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_36B_PAPER_FORWARD_RETURN_FILLER_FAILED"
    throw "Missing script: $Script"
}

$Args36B = @("--root", $Root)
if ($UpdatePaperTradingForwardReturns) { $Args36B += "--update-paper-trading-forward-returns" }
if ($UseYFinanceForPaperForwardPrices) { $Args36B += "--use-yfinance-for-paper-forward-prices" }

& $Python $Script @Args36B
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.36B READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.36B PAPER FORWARD RETURN FILLER ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
