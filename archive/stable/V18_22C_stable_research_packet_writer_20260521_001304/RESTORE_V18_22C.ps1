param([string]$Root = "D:\us-tech-quant")
$ErrorActionPreference = "Stop"
$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "=== RESTORE V18.22C STABLE SNAPSHOT START ==="
Write-Host "MODE: SNAPSHOT_RESTORE"
Write-Host "NOTE: This restores advisory packet-writer artifacts only."
$Source = Join-Path $SnapshotRoot "scripts\v18\v18_22C_research_packet_writer.py"
$Target = Join-Path $Root "scripts\v18\v18_22C_research_packet_writer.py"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\run_v18_22C_research_packet_writer.ps1"
$Target = Join-Path $Root "scripts\v18\run_v18_22C_research_packet_writer.ps1"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\v18_22B_daily_research_command_center_wrapper.py"
$Target = Join-Path $Root "scripts\v18\v18_22B_daily_research_command_center_wrapper.py"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "scripts\v18\run_v18_22B_daily_research_command_center_wrapper.ps1"
$Target = Join-Path $Root "scripts\v18\run_v18_22B_daily_research_command_center_wrapper.ps1"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_EXECUTIVE_RESEARCH_BRIEF.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_DETAILED_RESEARCH_PACKET.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_BLOCKED_GATE_EXPLANATION.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_NEXT_ACTION_CHECKLIST.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_DO_NOT_DO_YET_CHECKLIST.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_RESEARCH_PACKET_SOURCE_AUDIT.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_packets\V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv"
$Target = Join-Path $Root "outputs\v18\research_packets\V18_22C_CURRENT_RESEARCH_PACKET_VALIDATION.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_READ_FIRST.txt"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_CURRENT_RESEARCH_PACKET_WRITER_REPORT.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_STABLE_READ_FIRST.txt"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_READ_FIRST.txt"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22B_CURRENT_DAILY_RESEARCH_COMMAND_CENTER_WRAPPER_REPORT.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_PACKET.md"
$Target = Join-Path $Root "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_PACKET.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv"
$Target = Join-Path $Root "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_GATE_SUMMARY.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_ACTION_SUMMARY.csv"
$Target = Join-Path $Root "outputs\v18\research_command_center\V18_22B_CURRENT_DAILY_RESEARCH_ACTION_SUMMARY.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_command_center\V18_22B_CURRENT_WRAPPER_SAFETY_AUDIT.csv"
$Target = Join-Path $Root "outputs\v18\research_command_center\V18_22B_CURRENT_WRAPPER_SAFETY_AUDIT.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\research_command_center\V18_22B_CURRENT_WRAPPER_VALIDATION.csv"
$Target = Join-Path $Root "outputs\v18\research_command_center\V18_22B_CURRENT_WRAPPER_VALIDATION.csv"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_STABLE_READ_FIRST.txt"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_STABLE_READ_FIRST.txt"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
$Source = Join-Path $SnapshotRoot "outputs\v18\ops\V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md"
$Target = Join-Path $Root "outputs\v18\ops\V18_22C_CURRENT_STABLE_SNAPSHOT_REPORT.md"
if (Test-Path $Source) {
    $Dir = Split-Path -Parent $Target
    if (-not (Test-Path $Dir)) { New-Item -ItemType Directory -Path $Dir -Force | Out-Null }
    Copy-Item -LiteralPath $Source -Destination $Target -Force
}
Write-Host "RESTORE_COMPLETE: TRUE"
Write-Host "RESEARCH_PACKET_WRITER_READY: TRUE"
Write-Host "PRODUCTION_DAILY_COMMAND_CENTER_MODIFIED: FALSE"
Write-Host "DAILY_COMMAND_CENTER_INTEGRATION_APPLIED: FALSE"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "BACKTEST_EXECUTED: FALSE"
Write-Host "FORWARD_RETURN_FILLED_COUNT: 0"
