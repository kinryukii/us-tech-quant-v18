param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.25A R1 DEGRADED DAILY OUTPUT REVIEW START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: READ_ONLY_DEGRADED_DAILY_OUTPUT_REVIEW"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_25A_R1_degraded_daily_output_review.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R1_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}
if (-not (Test-Path -LiteralPath $Script)) {
    throw "Missing V18.25A R1 degraded daily output review Python script: $Script"
}

Write-Host "PYTHON: $Python"
Write-Host "PYTHON_SCRIPT: $Script"

& $Python $Script --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (Test-Path -LiteralPath $ReadFirst) {
    Write-Host "=== V18.25A R1 READ_FIRST CONTENT ==="
    Get-Content -LiteralPath $ReadFirst | ForEach-Object { Write-Host $_ }
} else {
    Write-Host "READ_FIRST_MISSING: $ReadFirst"
}

Write-Host "=== V18.25A R1 DEGRADED DAILY OUTPUT REVIEW END ==="
exit $PythonExitCode
