param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$Apply
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.18E TECHNICAL TIMING CURRENT ALIAS EXTERNALIZATION AUDIT START ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DRYRUN"
Write-Host "APPLY: $($Apply.IsPresent.ToString().ToUpper())"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_18E_technical_timing_current_alias_externalization_audit.py"

if (-not (Test-Path $Python)) {
    $Python = "python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.18E Python script: $Script"
}

$argsList = @("--root", $Root)
if ($Apply) {
    $argsList += "--apply"
}

& $Python $Script @argsList
exit $LASTEXITCODE
