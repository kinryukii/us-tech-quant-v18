param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$WriteCurrent
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
if (-not (Test-Path $Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_47C_R1_event_source_coverage_repair.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_47C_R1_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.47C-R1"
Write-Host "PATCH_NAME: Event Source Coverage Repair"
Write-Host "READ_ONLY: TRUE"
Write-Host "OFFICIAL_RANKING_CHANGED: FALSE"
Write-Host "FACTOR_WEIGHTS_CHANGED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args47CR1 = @("--root", $Root)
if ($WriteCurrent) {
    $Args47CR1 += "--write-current"
}

& $Python $Script @Args47CR1
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.47C-R1 READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
