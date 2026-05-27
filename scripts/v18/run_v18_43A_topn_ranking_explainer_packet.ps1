param(
    [int]$TopN = 20,
    [int]$NeighborWindow = 2,
    [switch]$WriteCurrent,
    [switch]$IncludeSingleTickerHints,
    [switch]$Strict,
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_43A_topn_ranking_explainer_packet.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_43A_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.43A"
Write-Host "TOP_N: $TopN"
Write-Host "NEIGHBOR_WINDOW: $NeighborWindow"
Write-Host "WRITE_CURRENT: $WriteCurrent"
Write-Host "INCLUDE_SINGLE_TICKER_HINTS: $IncludeSingleTickerHints"
Write-Host "STRICT: $Strict"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args43A = @(
    "--root", $Root,
    "--top-n", [string]$TopN,
    "--neighbor-window", [string]$NeighborWindow
)
if ($WriteCurrent) { $Args43A += "--write-current" }
if ($IncludeSingleTickerHints) { $Args43A += "--include-single-ticker-hints" }
if ($Strict) { $Args43A += "--strict" }

& $Python $Script @Args43A
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.43A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
