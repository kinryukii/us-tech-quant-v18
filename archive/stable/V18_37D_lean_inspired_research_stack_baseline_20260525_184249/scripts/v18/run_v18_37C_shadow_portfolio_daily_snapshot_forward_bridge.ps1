param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplySnapshot
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_37C_shadow_portfolio_daily_snapshot_forward_bridge.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_37C_READ_FIRST.txt"

Write-Host "=== START V18.37C SHADOW PORTFOLIO DAILY SNAPSHOT FORWARD BRIDGE ==="
Write-Host "DELEGATING_TO: V18.37C_SHADOW_PORTFOLIO_DAILY_SNAPSHOT_FORWARD_BRIDGE"
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_SHADOW_PORTFOLIO_FORWARD_BRIDGE"
Write-Host "APPLY_SNAPSHOT: $ApplySnapshot"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "FORBIDDEN_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_37C_SHADOW_PORTFOLIO_FORWARD_BRIDGE_FAILED"
    throw "Missing script: $Script"
}

$Args37C = @("--root", $Root)
if ($ApplySnapshot) {
    $Args37C += "--apply-snapshot"
}

& $Python $Script @Args37C
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.37C READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_37C_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.37C SHADOW PORTFOLIO DAILY SNAPSHOT FORWARD BRIDGE ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
