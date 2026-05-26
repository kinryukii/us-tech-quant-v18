param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_37A_lean_inspired_strategy_motif_lab.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_37A_READ_FIRST.txt"

Write-Host "=== START V18.37A LEAN-INSPIRED STRATEGY MOTIF LAB ==="
Write-Host "DELEGATING_TO: V18.37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB"
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_RESEARCH_MOTIF_LAB"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "FORBIDDEN_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_37A_LEAN_INSPIRED_STRATEGY_MOTIF_LAB_FAILED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.37A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_37A_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.37A LEAN-INSPIRED STRATEGY MOTIF LAB ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

$FailLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
if ($FailLine) {
    exit 1
}

exit 0
