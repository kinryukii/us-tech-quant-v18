param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyUniverseInvalidTickerPrune
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35G_universe_invalid_ticker_prune.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35G_READ_FIRST.txt"

Write-Host "=== START V18.35G UNIVERSE INVALID TICKER PRUNE ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_UNIVERSE_INVALID_TICKER_PRUNE: $ApplyUniverseInvalidTickerPrune"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35G_UNIVERSE_INVALID_TICKER_PRUNE_FAILED"
    throw "Missing script: $Script"
}

$Args35G = @("--root", $Root)
if ($ApplyUniverseInvalidTickerPrune) { $Args35G += "--apply-universe-invalid-ticker-prune" }

& $Python $Script @Args35G
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35G READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35G UNIVERSE INVALID TICKER PRUNE ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
