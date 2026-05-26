param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.20C LOW-RISK SAFE DELETE START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: $(if ($Apply) { 'APPLY' } else { 'DRYRUN' })"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_20C_apply_low_risk_safe_delete.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.20C Python script: $Script"
}

$argsList = @("--root", $Root)
if ($Apply) {
    $argsList += "--apply"
}

& $Python $Script @argsList
exit $LASTEXITCODE
