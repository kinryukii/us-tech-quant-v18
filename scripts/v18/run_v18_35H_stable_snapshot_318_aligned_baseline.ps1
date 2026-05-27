param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35H_stable_snapshot_318_aligned_baseline.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35H_READ_FIRST.txt"

Write-Host "=== START V18.35H STABLE SNAPSHOT 318 ALIGNED BASELINE ==="
Write-Host "ROOT: $Root"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35H_STABLE_SNAPSHOT_318_ALIGNED_FAILED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35H READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35H STABLE SNAPSHOT 318 ALIGNED BASELINE ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
