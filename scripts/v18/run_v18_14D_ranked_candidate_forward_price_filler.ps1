param(
    [switch]$UseYFinance,
    [bool]$AllowLocalPriceOnly = $true,
    [int]$MaxRows = 0
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_14D_ranked_candidate_forward_price_filler.py"
$SummaryPath = Join-Path $Root "outputs\v18\ops\V18_14D_CURRENT_RANKED_CANDIDATE_FORWARD_PRICE_FILLER_SUMMARY.csv"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing Python script: $Script"
}

Write-Host "=== V18.14D RANKED CANDIDATE FORWARD PRICE FILLER START ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_ROWS: $MaxRows"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "ALLOW_LOCAL_PRICE_ONLY: $AllowLocalPriceOnly"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "FORWARD_PRICE_FILLER_ONLY: TRUE"

$Args = @($Script, "--root", $Root, "--max-rows", "$MaxRows")
if ($UseYFinance) {
    $Args += "--use-yfinance"
}
if ($AllowLocalPriceOnly) {
    $Args += "--allow-local-price-only"
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
Write-Host "=== V18.14D COMPACT SUMMARY ==="
foreach ($Key in @(
    "STATUS",
    "TRACKER_ROWS",
    "UPDATED_FORWARD_ROWS",
    "FORWARD_COMPLETE_ROWS",
    "PENDING_FORWARD_ROWS",
    "PRICE_SOURCE_COUNT",
    "PRICE_SOURCE_STATUS",
    "VALIDATION_FAIL_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "READ_FIRST"
)) {
    Write-Host "$($Key): $($Summary[$Key.ToLower()])"
}
