param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.23A-R1 UNIVERSE COUNT DRIFT RECONCILIATION START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_UNIVERSE_COUNT_DRIFT_RECONCILIATION"
Write-Host "ROLLING_SCAN_EXECUTED: FALSE"
Write-Host "ROLLING_SCAN_DATA_FETCHED: FALSE"
Write-Host "ROLLING_SCAN_PLAN_MODIFIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_23A_R1_universe_count_drift_reconciliation.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_23A_R1_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.23A-R1 reconciliation Python script: $Script"
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

Write-Host "=== V18.23A-R1 READ_FIRST CONTENT ==="
$ReadFirstContent = Get-Content -LiteralPath $ReadFirst
$ReadFirstContent | ForEach-Object { Write-Host $_ }

$StatusLine = $ReadFirstContent | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
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
Write-Host "=== V18.23A-R1 UNIVERSE COUNT DRIFT RECONCILIATION END ==="
exit 0
