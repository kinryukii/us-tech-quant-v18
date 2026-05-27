param([string]$Root = "D:\us-tech-quant")
$ErrorActionPreference = "Stop"
$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "=== RESTORE V18.23A STABLE SNAPSHOT START ==="
Write-Host "MODE: SNAPSHOT_RESTORE"
Write-Host "NOTE: Restores V18.23A read-only planning and reconciliation artifacts only."
$Source = Join-Path $SnapshotRoot "scripts\v18\v18_23A_rolling_research_coverage_controller.py"
$Target = Join-Path $Root "scripts\v18\v18_23A_rolling_research_coverage_controller.py"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\run_v18_23A_rolling_research_coverage_controller.ps1"
$Target = Join-Path $Root "scripts\v18\run_v18_23A_rolling_research_coverage_controller.ps1"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER.md"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_ROLLING_COVERAGE_PLAN.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_TODAY_PLANNED_SCAN_LIST.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_BUCKET_SUMMARY.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_BUCKET_SUMMARY.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_SOURCE_AUDIT.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_SOURCE_AUDIT.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_VALIDATION.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_CURRENT_COVERAGE_VALIDATION.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_23A_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_23A_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_23A_CURRENT_ROLLING_COVERAGE_CONTROLLER_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\v18_23A_R1_universe_count_drift_reconciliation.py"
$Target = Join-Path $Root "scripts\v18\v18_23A_R1_universe_count_drift_reconciliation.py"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\run_v18_23A_R1_universe_count_drift_reconciliation.ps1"
$Target = Join-Path $Root "scripts\v18\run_v18_23A_R1_universe_count_drift_reconciliation.ps1"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION.md"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_SOURCE_TICKER_COUNT_AUDIT.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_SOURCE_TICKER_COUNT_AUDIT.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_UNIVERSE_SOURCE_COMPARISON.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_UNIVERSE_SOURCE_COMPARISON.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_TICKER_SET_DIFF.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_TICKER_SET_DIFF.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_DROPPED_OR_MISSING_TICKERS.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_DROPPED_OR_MISSING_TICKERS.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_SUSPICIOUS_TICKERS.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_SUSPICIOUS_TICKERS.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_RECONCILIATION_VALIDATION.csv"
$Target = Join-Path $Root "outputs\v18\rolling_coverage\V18_23A_R1_CURRENT_RECONCILIATION_VALIDATION.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_23A_R1_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_23A_R1_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_23A_R1_CURRENT_UNIVERSE_COUNT_DRIFT_RECONCILIATION_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22D_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22D_STABLE_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22D_CURRENT_STABLE_SNAPSHOT_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22D_CURRENT_STABLE_SNAPSHOT_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
Write-Host "RESTORE_COMPLETE: TRUE"
Write-Host "ROLLING_SCAN_EXECUTED: FALSE"
Write-Host "ROLLING_SCAN_DATA_FETCHED: FALSE"
Write-Host "ROLLING_SCAN_PLAN_MODIFIED: FALSE"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "BACKTEST_EXECUTED: FALSE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
