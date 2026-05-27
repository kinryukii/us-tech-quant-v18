param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_37D_stable_snapshot_research_stack_baseline.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_37D_READ_FIRST.txt"

Write-Host "=== START V18.37D STABLE SNAPSHOT RESEARCH STACK BASELINE ==="
Write-Host "DELEGATING_TO: V18.37D_STABLE_SNAPSHOT_RESEARCH_STACK_BASELINE"
Write-Host "ROOT: $Root"
Write-Host "MODE: SNAPSHOT_ONLY"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "OFFICIAL_SIGNAL_FREEZE_LEDGER_MODIFIED: FALSE"
Write-Host "PAPER_TRADING_LEDGER_MODIFIED: FALSE"
Write-Host "SHADOW_PORTFOLIO_LEDGER_MODIFIED: FALSE"
Write-Host "FORBIDDEN_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_37D_STABLE_SNAPSHOT_RESEARCH_STACK_BASELINE_FAILED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.37D READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_37D_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.37D STABLE SNAPSHOT RESEARCH STACK BASELINE ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
