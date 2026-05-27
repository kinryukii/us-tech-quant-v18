param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyResidualActionWarningResolver
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_40D_residual_action_warning_resolver.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_40D_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_RESIDUAL_ACTION_WARNING_RESOLVER.md"

Write-Host "=== START V18.40D RESIDUAL ACTION WARNING RESOLVER ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_RESIDUAL_ACTION_WARNING_RESOLVER: $ApplyResidualActionWarningResolver"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE"
Write-Host "ACCOUNT_STATE_MODIFIED: FALSE"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "ORDER_EXECUTION_USED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args40D = @("--root", $Root)
if ($ApplyResidualActionWarningResolver) {
    $Args40D += "--apply-residual-action-warning-resolver"
}

& $Python $Script @Args40D
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.40D READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_40D_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.40D RESIDUAL ACTION WARNING RESOLVER ==="
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
