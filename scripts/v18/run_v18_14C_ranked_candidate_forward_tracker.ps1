param(
    [switch]$UseYFinance,
    [int]$MaxRank = 20
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_14C_ranked_candidate_forward_tracker.py"
$SummaryPath = Join-Path $Root "outputs\v18\ops\V18_14C_CURRENT_RANKED_CANDIDATE_FORWARD_TRACKER_SUMMARY.csv"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing Python script: $Script"
}

Write-Host "=== V18.14C RANKED CANDIDATE FORWARD TRACKER START ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_RANK: $MaxRank"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "FORWARD_VALIDATION_ONLY: TRUE"

$Args = @($Script, "--root", $Root, "--max-rank", "$MaxRank")
if ($UseYFinance) {
    $Args += "--use-yfinance"
}

& $Python @Args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$Summary = @{}
if (Test-Path $SummaryPath) {
    Import-Csv -Path $SummaryPath | Select-Object -First 1 | ForEach-Object {
        $_.PSObject.Properties | ForEach-Object {
            $Summary[$_.Name] = $_.Value
        }
    }
}

Write-Host ""
Write-Host "=== V18.14C COMPACT SUMMARY ==="
foreach ($Key in @(
    "STATUS",
    "TRACKER_ROWS",
    "NEW_SIGNAL_ROWS_ADDED",
    "UPDATED_FORWARD_ROWS",
    "PENDING_FORWARD_ROWS",
    "SIGNAL_DATE",
    "TOP_5_TICKERS",
    "VALIDATION_FAIL_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "READ_FIRST"
)) {
    Write-Host "$($Key): $($Summary[$Key.ToLower()])"
}
