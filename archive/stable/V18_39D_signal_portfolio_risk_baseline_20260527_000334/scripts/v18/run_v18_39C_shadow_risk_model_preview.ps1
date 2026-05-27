param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_39C_shadow_risk_model_preview.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_39C_READ_FIRST.txt"
$Summary = Join-Path $Root "outputs\v18\risk_preview\V18_39C_SHADOW_RISK_PREVIEW_SUMMARY.csv"
$Detail = Join-Path $Root "outputs\v18\risk_preview\V18_39C_SHADOW_RISK_PREVIEW_DETAIL.csv"
$Report = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_SHADOW_RISK_MODEL_PREVIEW.md"

Write-Host "=== START V18.39C SHADOW RISK MODEL PREVIEW ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_SHADOW_RISK_MODEL_PREVIEW"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "ORDER_EXECUTION_USED: FALSE"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "REAL_ACCOUNT_USED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE"
Write-Host "ACCOUNT_STATE_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_39C_SHADOW_RISK_MODEL_PREVIEW_BLOCKED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.39C READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_39C_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.39C SHADOW RISK MODEL PREVIEW ==="
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "SUMMARY_CSV: $Summary"
Write-Host "DETAIL_CSV: $Detail"
Write-Host "REPORT: $Report"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
