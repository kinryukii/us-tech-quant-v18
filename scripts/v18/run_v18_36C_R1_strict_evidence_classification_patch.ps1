param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_36C_R1_strict_evidence_classification_patch.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_36C_R1_READ_FIRST.txt"

Write-Host "=== START V18.36C-R1 STRICT FACTOR IMPLEMENTATION AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_STRICT_EVIDENCE_AUDIT"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "FACTOR_WEIGHTS_MODIFIED: FALSE"
Write-Host "AUTO_WEIGHT_CHANGE: DISABLED"
Write-Host "FORBIDDEN_MODIFIED: FALSE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_36C_R1_STRICT_FACTOR_IMPLEMENTATION_AUDIT_FAILED"
    throw "Missing script: $Script"
}

& $Python $Script --root $Root
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.36C-R1 READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.36C-R1 STRICT FACTOR IMPLEMENTATION AUDIT ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
