param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.23C-R5 BATCH 2 STAGED BACKFILL QUALITY AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_BATCH2_STAGED_BACKFILL_QUALITY_AUDIT_DRY_RUN"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "STAGED_PRICE_HISTORY_MODIFIED: FALSE"
Write-Host "OFFICIAL_PRICE_CACHE_MODIFIED: FALSE"
Write-Host "OFFICIAL_PRICE_HISTORY_MODIFIED: FALSE"
Write-Host "LEDGER_MODIFIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_23C_R5_batch2_staged_backfill_quality_audit.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_23C_R5_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.23C-R5 Batch 2 quality audit Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (-not (Test-Path -LiteralPath $ReadFirst)) {
    Write-Host "READ_FIRST_MISSING: $ReadFirst"
    exit 1
}

Write-Host "=== V18.23C-R5 READ_FIRST CONTENT ==="
$ReadFirstContent = Get-Content -LiteralPath $ReadFirst
$ReadFirstContent | ForEach-Object { Write-Host $_ }

$StatusLine = $ReadFirstContent | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
$AllowedLine = $ReadFirstContent | Where-Object { $_ -like "OFFICIAL_INTEGRATION_ALLOWED_NEXT_STEP:*" } | Select-Object -First 1
$ApprovalLine = $ReadFirstContent | Where-Object { $_ -like "OFFICIAL_INTEGRATION_REQUIRES_EXPLICIT_APPROVAL:*" } | Select-Object -First 1
Write-Host $AllowedLine
Write-Host $ApprovalLine

if ($StatusLine -like "STATUS: FAIL*") {
    Write-Host "READ_FIRST_STATUS_FAIL: TRUE"
    exit 1
}
if ($StatusLine -like "STATUS: OK*") {
    Write-Host "READ_FIRST_STATUS_OK: TRUE"
} else {
    Write-Host "READ_FIRST_STATUS_OK: FALSE"
}
if ($PythonExitCode -ne 0) {
    exit $PythonExitCode
}

Write-Host "READ_FIRST: $ReadFirst"
Write-Host "=== V18.23C-R5 BATCH 2 STAGED BACKFILL QUALITY AUDIT END ==="
exit 0
