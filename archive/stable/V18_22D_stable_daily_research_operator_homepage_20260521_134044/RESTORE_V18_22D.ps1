param([string]$Root = "D:\us-tech-quant")
$ErrorActionPreference = "Stop"
$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "=== RESTORE V18.22D STABLE SNAPSHOT START ==="
Write-Host "MODE: SNAPSHOT_RESTORE"
Write-Host "NOTE: Restores V18.22D read-only operator homepage scripts and outputs only."
$Source = Join-Path $SnapshotRoot "scripts\v18\v18_22D_daily_research_operator_homepage.py"
$Target = Join-Path $Root "scripts\v18\v18_22D_daily_research_operator_homepage.py"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\run_v18_22D_daily_research_operator_homepage.ps1"
$Target = Join-Path $Root "scripts\v18\run_v18_22D_daily_research_operator_homepage.ps1"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\operator_homepage\V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md"
$Target = Join-Path $Root "outputs\v18\operator_homepage\V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_GATE_SUMMARY.csv"
$Target = Join-Path $Root "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_GATE_SUMMARY.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_SOURCE_AUDIT.csv"
$Target = Join-Path $Root "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_SOURCE_AUDIT.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_VALIDATION.csv"
$Target = Join-Path $Root "outputs\v18\operator_homepage\V18_22D_CURRENT_OPERATOR_VALIDATION.csv"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22D_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22D_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22D_CURRENT_DAILY_RESEARCH_OPERATOR_HOMEPAGE_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22A_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22A_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22A_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22A_STABLE_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22A_CURRENT_RESEARCH_COMMAND_CENTER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22A_CURRENT_RESEARCH_COMMAND_CENTER_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22A_CURRENT_STABLE_SNAPSHOT_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22A_CURRENT_STABLE_SNAPSHOT_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_STABLE_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_CURRENT_STABLE_SNAPSHOT_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_CURRENT_STABLE_SNAPSHOT_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_STABLE_READ_FIRST.txt"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md"
if (Test-Path -LiteralPath $Source) {
    $TargetDir = Split-Path -Parent $Target
    if (-not (Test-Path -LiteralPath $TargetDir)) { New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
Write-Host "RESTORE_COMPLETE: TRUE"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "BACKTEST_EXECUTED: FALSE"
