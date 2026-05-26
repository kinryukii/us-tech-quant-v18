param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35A_universe_to_candidate_diff_audit.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35A_READ_FIRST.txt"

Write-Host "=== START V18.35A UNIVERSE TO CANDIDATE DIFF AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "REPORT_ONLY: TRUE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35A_UNIVERSE_TO_CANDIDATE_AUDIT_FAILED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35A UNIVERSE TO CANDIDATE DIFF AUDIT ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) {
        exit 1
    }
}

exit 0
