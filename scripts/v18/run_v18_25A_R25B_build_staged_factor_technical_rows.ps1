[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 93,
    [switch]$DryRun,
    [switch]$AllowMergeToCurrentFactorPack,
    [switch]$AllowMergeToCurrentTechnicalTiming
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25B_build_staged_factor_technical_rows.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25B_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25B BUILD STAGED FACTOR TECHNICAL ROWS ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "DRY_RUN: $($DryRun.IsPresent)"
Write-Host "MODE: $(if ($DryRun.IsPresent) { 'DRYRUN_STAGED_BUILD_PLAN_ONLY' } else { 'STAGED_BUILD_ONLY' })"

if ($AllowMergeToCurrentFactorPack.IsPresent -or $AllowMergeToCurrentTechnicalTiming.IsPresent) {
    Write-Host "R25B refuses merge flags. Official merge belongs to R25C/R26 after validation."
}

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)
if ($DryRun.IsPresent) {
    $argsList += "--dry-run"
}
if ($AllowMergeToCurrentFactorPack.IsPresent) {
    $argsList += "--allow-merge-to-current-factor-pack"
}
if ($AllowMergeToCurrentTechnicalTiming.IsPresent) {
    $argsList += "--allow-merge-to-current-technical-timing"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25B staged factor technical build failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25B BUILD STAGED FACTOR TECHNICAL ROWS ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
