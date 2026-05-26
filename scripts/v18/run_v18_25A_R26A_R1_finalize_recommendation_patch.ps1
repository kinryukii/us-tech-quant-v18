[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$TopN = 250,
    [int]$SignalLookbackDays = 30
)

$ErrorActionPreference = "Stop"

$wrapper = Join-Path $PSScriptRoot "run_v18_25A_R26A_forward_test_factor_effectiveness_readiness_audit.ps1"
$r26aReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R26A_READ_FIRST.txt"
$r26aReport = Join-Path $Root "outputs\v18\ops\V18_25A_R26A_CURRENT_FORWARD_TEST_FACTOR_EFFECTIVENESS_READINESS_REPORT.md"
$r26aSummary = Join-Path $Root "outputs\v18\factor_validation\V18_25A_R26A_CURRENT_FACTOR_EFFECTIVENESS_READINESS_SUMMARY.csv"
$r26aBlockers = Join-Path $Root "outputs\v18\factor_validation\V18_25A_R26A_CURRENT_BLOCKERS_AND_NEXT_ACTIONS.csv"
$r1ReadFirst = Join-Path $Root "outputs\v18\ops\V18_25A_R26A_R1_READ_FIRST.txt"
$r1Report = Join-Path $Root "outputs\v18\ops\V18_25A_R26A_R1_CURRENT_FINALIZE_FORWARD_TEST_READINESS_REPORT.md"
$r1Audit = Join-Path $Root "outputs\v18\factor_validation\V18_25A_R26A_R1_CURRENT_RECOMMENDATION_PATCH_AUDIT.csv"

Write-Host "=== START V18.25A-R26A-R1 FINALIZE RECOMMENDATION PATCH ==="
Write-Host "ROOT: $Root"
Write-Host "TOP_N: $TopN"
Write-Host "SIGNAL_LOOKBACK_DAYS: $SignalLookbackDays"
Write-Host "MODE: RECOMMENDATION_TEXT_ONLY_PATCH_RERUN"

& powershell -NoProfile -ExecutionPolicy Bypass -File $wrapper -Root $Root -TopN $TopN -SignalLookbackDays $SignalLookbackDays
if ($LASTEXITCODE -ne 0) {
    throw "R26A-R1 recommendation patch rerun failed with exit code $LASTEXITCODE"
}

if (Test-Path $r26aReadFirst) { Copy-Item -LiteralPath $r26aReadFirst -Destination $r1ReadFirst -Force }
if (Test-Path $r26aReport) { Copy-Item -LiteralPath $r26aReport -Destination $r1Report -Force }
if (Test-Path $r26aSummary) { Copy-Item -LiteralPath $r26aSummary -Destination $r1Audit -Force }
if (Test-Path $r26aBlockers) { Copy-Item -LiteralPath $r26aBlockers -Destination (Join-Path $Root "outputs\v18\factor_validation\V18_25A_R26A_R1_CURRENT_BLOCKERS_AND_NEXT_ACTIONS.csv") -Force }

$statusLine = ""
if (Test-Path $r1ReadFirst) {
    $statusLine = (Select-String -Path $r1ReadFirst -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R26A-R1 FINALIZE RECOMMENDATION PATCH ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $r1ReadFirst"
