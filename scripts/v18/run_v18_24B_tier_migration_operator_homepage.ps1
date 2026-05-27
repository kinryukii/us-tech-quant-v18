param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.24B TIER MIGRATION OPERATOR HOMEPAGE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_TIER_MIGRATION_OPERATOR_HOMEPAGE"
Write-Host "READ_ONLY: TRUE"
Write-Host "PRICE_CACHE_MODIFIED: FALSE"
Write-Host "LEDGER_MODIFIED: FALSE"
Write-Host "RANKING_MODIFIED: FALSE"
Write-Host "FACTOR_PACK_MODIFIED: FALSE"
Write-Host "TECHNICAL_TIMING_MODIFIED: FALSE"
Write-Host "SIGNAL_SNAPSHOT_MODIFIED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_24B_tier_migration_operator_homepage.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_24B_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.24B operator homepage Python script: $Script"
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

Write-Host "=== V18.24B READ_FIRST CONTENT ==="
$ReadFirstContent = Get-Content -LiteralPath $ReadFirst
$ReadFirstContent | ForEach-Object { Write-Host $_ }

$StatusLine = $ReadFirstContent | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
$HomepageLine = $ReadFirstContent | Where-Object { $_ -like "OPERATOR_HOMEPAGE_PATH:*" } | Select-Object -First 1
Write-Host $HomepageLine

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
Write-Host "=== V18.24B TIER MIGRATION OPERATOR HOMEPAGE END ==="
exit 0
