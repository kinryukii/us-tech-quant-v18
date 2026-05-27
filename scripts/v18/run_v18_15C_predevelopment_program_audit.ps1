param(
    [switch]$SkipRuntimeValidation
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_15C_predevelopment_program_audit.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.15C audit script: $Script"
}

Write-Host "=== V18.15C PRE-DEVELOPMENT PROGRAM AUDIT START ==="
Write-Host "MODE: READ_ONLY_AUDIT"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"

$Args15C = @("--root", $Root)
if ($SkipRuntimeValidation) {
    $Args15C += "--skip-runtime-validation"
}

& $Python $Script @Args15C
exit $LASTEXITCODE
