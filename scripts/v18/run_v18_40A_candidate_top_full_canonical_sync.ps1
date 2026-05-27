param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyCandidateTopFullCanonicalSync
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_40A_candidate_top_full_canonical_sync.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_40A_READ_FIRST.txt"
$Report = Join-Path $Root "outputs\v18\read_center\V18_CURRENT_CANDIDATE_TOP_FULL_CANONICAL_SYNC.md"

Write-Host "=== START V18.40A CANDIDATE TOP/FULL CANONICAL SYNC ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_CANDIDATE_TOP_FULL_CANONICAL_SYNC: $ApplyCandidateTopFullCanonicalSync"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "BROKER_API_USED: FALSE"
Write-Host "ORDER_EXECUTION_USED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args40A = @("--root", $Root)
if ($ApplyCandidateTopFullCanonicalSync) {
    $Args40A += "--apply-candidate-top-full-canonical-sync"
}

& $Python $Script @Args40A
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.40A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}
else {
    Write-Host "STATUS: FAIL_V18_40A_READ_FIRST_MISSING"
    exit 1
}

Write-Host "=== DONE V18.40A CANDIDATE TOP/FULL CANONICAL SYNC ==="
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
