param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.25A R2 TIER MIGRATION SOURCE ALIAS REPAIR START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_TIER_MIGRATION_SOURCE_ALIAS_REPAIR"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_25A_R2_tier_migration_source_alias_repair.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R2_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.25A R2 tier migration source alias repair Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (Test-Path -LiteralPath $ReadFirst) {
    Write-Host "=== V18.25A R2 READ_FIRST CONTENT ==="
    Get-Content -LiteralPath $ReadFirst | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "READ_FIRST_MISSING: $ReadFirst"
}

Write-Host "=== V18.25A R2 TIER MIGRATION SOURCE ALIAS REPAIR END ==="
exit $PythonExitCode
