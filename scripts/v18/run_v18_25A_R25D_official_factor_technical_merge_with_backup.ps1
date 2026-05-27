[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$DryRun,
    [int]$MaxTickers = 93,
    [bool]$RequireValidatedMergePlan = $true
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25D_official_factor_technical_merge_with_backup.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25D_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25D OFFICIAL FACTOR TECHNICAL MERGE WITH BACKUP ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "REQUIRE_VALIDATED_MERGE_PLAN: $RequireValidatedMergePlan"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_OFFICIAL_FACTOR_TECHNICAL_MERGE_PLAN' } else { 'APPLY_OFFICIAL_FACTOR_TECHNICAL_MERGE_WITH_BACKUP' })"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)

if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($RequireValidatedMergePlan) {
    $argsList += "--require-validated-merge-plan"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25D official factor technical merge failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25D OFFICIAL FACTOR TECHNICAL MERGE WITH BACKUP ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
