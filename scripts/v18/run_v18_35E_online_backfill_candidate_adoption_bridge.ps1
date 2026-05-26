param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UseYFinanceForCandidateBridgeBackfill,
    [switch]$ApplyOnlineBackfilledRecomputedCandidates
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35E_online_backfill_candidate_adoption_bridge.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35E_READ_FIRST.txt"

Write-Host "=== START V18.35E ONLINE BACKFILL CANDIDATE ADOPTION BRIDGE ==="
Write-Host "ROOT: $Root"
Write-Host "USE_YFINANCE_FOR_CANDIDATE_BRIDGE_BACKFILL: $UseYFinanceForCandidateBridgeBackfill"
Write-Host "APPLY_ONLINE_BACKFILLED_RECOMPUTED_CANDIDATES: $ApplyOnlineBackfilledRecomputedCandidates"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35E_ONLINE_BACKFILL_CANDIDATE_BRIDGE_FAILED"
    throw "Missing script: $Script"
}

$Args35E = @("--root", $Root)
if ($UseYFinanceForCandidateBridgeBackfill) { $Args35E += "--use-yfinance-for-candidate-bridge-backfill" }
if ($ApplyOnlineBackfilledRecomputedCandidates) { $Args35E += "--apply-online-backfilled-recomputed-candidates" }

& $Python $Script @Args35E
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35E READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35E ONLINE BACKFILL CANDIDATE ADOPTION BRIDGE ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
