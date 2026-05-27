param(
    [string]$Ticker,
    [int]$TopN = 20,
    [int]$NeighborWindow = 3,
    [switch]$Strict,
    [switch]$WriteCurrent,
    [switch]$AllowCurrentMissingOverwrite,
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
if ([string]::IsNullOrWhiteSpace($Ticker)) {
    throw "Ticker is required. Use -Ticker <string>."
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_42A_single_ticker_ranking_explainer.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_42A_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.42A"
Write-Host "TICKER: $Ticker"
Write-Host "TOP_N: $TopN"
Write-Host "NEIGHBOR_WINDOW: $NeighborWindow"
Write-Host "STRICT: $Strict"
Write-Host "WRITE_CURRENT: $WriteCurrent"
Write-Host "ALLOW_CURRENT_MISSING_OVERWRITE: $AllowCurrentMissingOverwrite"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args42A = @(
    "--root", $Root,
    "--ticker", $Ticker,
    "--top-n", [string]$TopN,
    "--neighbor-window", [string]$NeighborWindow
)
if ($Strict) { $Args42A += "--strict" }
if ($WriteCurrent) { $Args42A += "--write-current" }
if ($AllowCurrentMissingOverwrite) { $Args42A += "--allow-current-missing-overwrite" }

& $Python $Script @Args42A
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.42A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
