param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_38D_stable_snapshot_research_tracking_baseline.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_38D_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\read_center\V18_38D_STABLE_SNAPSHOT_REPORT.md"

Write-Host "=== START V18.38D STABLE SNAPSHOT RESEARCH TRACKING BASELINE ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: STABLE_SNAPSHOT_ONLY_RESEARCH_TRACKING_BASELINE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE"
Write-Host "ACCOUNT_STATE_MODIFIED: FALSE"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "ORDER_EXECUTION_USED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_38D_STABLE_SNAPSHOT_RESEARCH_TRACKING_BASELINE_BLOCKED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.38D READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_38D_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.38D STABLE SNAPSHOT RESEARCH TRACKING BASELINE ==="
Write-Host "READ_FIRST: $ReadFirst"
Write-Host "REPORT: $Report"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
