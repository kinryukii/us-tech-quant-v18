param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.13C RANKED CANDIDATE UNIFIED LINK START ==="
Write-Host "ROOT: $Root"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "LINK_ONLY: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_13C_ranked_candidate_unified_link.py"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing Python script: $Script"
}

& $Python $Script --root $Root
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$SummaryPath = Join-Path $Root "outputs\v18\read_center\V18_13C_CURRENT_UNIFIED_DAILY_WITH_RANKED_CANDIDATES_SUMMARY.csv"
if (-not (Test-Path $SummaryPath)) {
    throw "Missing summary output: $SummaryPath"
}

$Summary = @{}
Import-Csv -Path $SummaryPath | ForEach-Object {
    $Summary[$_.metric] = $_.value
}

Write-Host "STATUS: $($Summary['STATUS'])"
Write-Host "V18_13A_STATUS: $($Summary['V18_13A_STATUS'])"
Write-Host "V18_13B_STATUS: $($Summary['V18_13B_STATUS'])"
Write-Host "RANK_SOURCE_STATUS: $($Summary['RANK_SOURCE_STATUS'])"
Write-Host "SECOND_STAGE_COUNT: $($Summary['SECOND_STAGE_COUNT'])"
Write-Host "SCORED_TICKER_COUNT: $($Summary['SCORED_TICKER_COUNT'])"
Write-Host "UNSCORED_TICKER_COUNT: $($Summary['UNSCORED_TICKER_COUNT'])"
Write-Host "TOP_5_TICKERS: $($Summary['TOP_5_TICKERS'])"
Write-Host "OFFICIAL_DECISION_IMPACT: $($Summary['OFFICIAL_DECISION_IMPACT'])"
Write-Host "AUTO_TRADE: $($Summary['AUTO_TRADE'])"
Write-Host "AUTO_SELL: $($Summary['AUTO_SELL'])"
Write-Host "READ_ONLY: $($Summary['READ_ONLY'])"
Write-Host "LINK_ONLY: $($Summary['LINK_ONLY'])"
Write-Host "READ_FIRST: $($Summary['READ_FIRST'])"
Write-Host "READ_CENTER: $($Summary['READ_CENTER'])"
