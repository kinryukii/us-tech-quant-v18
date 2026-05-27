param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "===== START V18.25A-R16 BATCH3 CANDIDATE SELECTION / STAGED BACKFILL PLAN ====="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_BATCH3_CANDIDATE_SELECTION_STAGED_BACKFILL_PLAN"
Write-Host "EXTERNAL_FETCH_EXECUTED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_25A_R16_batch3_candidate_selection_staged_backfill_plan.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R16_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.25A R16 Batch3 candidate selection Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Script"

& $Python $Script --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (Test-Path -LiteralPath $ReadFirst) {
    Write-Host "===== V18.25A-R16 READ_FIRST ====="
    Get-Content -LiteralPath $ReadFirst | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "READ_FIRST_MISSING: $ReadFirst"
}

Write-Host "===== END V18.25A-R16 BATCH3 CANDIDATE SELECTION / STAGED BACKFILL PLAN ====="
exit $PythonExitCode
