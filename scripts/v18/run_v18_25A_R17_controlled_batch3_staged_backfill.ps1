param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "===== START V18.25A-R17 CONTROLLED BATCH3 STAGED BACKFILL ====="
Write-Host "ROOT: $Root"
Write-Host "MODE: CONTROLLED_BATCH3_STAGED_BACKFILL_SELECTED_CANDIDATES_ONLY"
Write-Host "FETCH_SCOPE: R16 selected Batch3 candidates only"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_25A_R17_controlled_batch3_staged_backfill.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R17_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.25A R17 controlled Batch3 staged backfill Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $Script"

& $Python $Script --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (Test-Path -LiteralPath $ReadFirst) {
    Write-Host "===== V18.25A-R17 READ_FIRST ====="
    Get-Content -LiteralPath $ReadFirst | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "READ_FIRST_MISSING: $ReadFirst"
}

Write-Host "===== END V18.25A-R17 CONTROLLED BATCH3 STAGED BACKFILL ====="
exit $PythonExitCode
