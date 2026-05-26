[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [string]$SnapshotPath = "D:/us-tech-quant/archive/stable/V18_39D_signal_portfolio_risk_baseline_20260527_000334"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SnapshotPath)) {
    throw "Snapshot path not found: $SnapshotPath"
}

$items = Get-ChildItem -Path $SnapshotPath -File -Recurse
foreach ($item in $items) {
    $relative = $item.FullName.Substring($SnapshotPath.Length).TrimStart("\", "/")
    if ([string]::IsNullOrWhiteSpace($relative)) {
        continue
    }
    $destination = Join-Path $Root $relative
    $destinationDir = Split-Path -Parent $destination
    if (-not (Test-Path $destinationDir)) {
        New-Item -ItemType Directory -Path $destinationDir -Force | Out-Null
    }
    Copy-Item -Path $item.FullName -Destination $destination -Force
}

Write-Host "RESTORE_SCRIPT_EXECUTED: FALSE"
Write-Host "SNAPSHOT_PATH: $SnapshotPath"
Write-Host "RESTORED_TO_ROOT: $Root"
