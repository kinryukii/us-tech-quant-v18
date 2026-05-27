param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_40A_kdj_macd_shadow_layer.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_40A_READ_FIRST.txt"
$Signals = Join-Path $Root "outputs\v18\technical_timing\V18_40A_KDJ_MACD_SHADOW_SIGNALS.csv"
$Summary = Join-Path $Root "outputs\v18\ops\V18_40A_KDJ_MACD_SHADOW_SUMMARY.csv"
$Report = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_KDJ_MACD_SHADOW_REPORT.md"

Write-Host "=== START V18.40A KDJ + MACD SHADOW LAYER ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SHADOW_ONLY_RESEARCH_ONLY_KDJ_MACD_OSCILLATOR_LAYER"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "ORDER_EXECUTION_USED: FALSE"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "RANKING_FORMULA_MODIFIED: FALSE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_40A_KDJ_MACD_SHADOW_LAYER_BLOCKED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.40A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_40A_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.40A KDJ + MACD SHADOW LAYER ==="
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "SIGNALS_CSV: $Signals"
Write-Host "SUMMARY_CSV: $Summary"
Write-Host "REPORT: $Report"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
