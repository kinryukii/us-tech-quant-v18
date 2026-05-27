[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Manifest = Join-Path $PSScriptRoot "MANIFEST.csv"

Write-Host "=== RESTORE V18.35H STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT_ROOT: $PSScriptRoot"
Write-Host "MANIFEST: $Manifest"

if (-not (Test-Path $Manifest)) {
    throw "Missing MANIFEST.csv: $Manifest"
}

$rows = Import-Csv -Path $Manifest
foreach ($row in $rows) {
    $source = Join-Path $PSScriptRoot $row.snapshot_path
    $target = Join-Path $Root $row.source_path
    if (-not (Test-Path $source)) {
        throw "Missing snapshot file: $source"
    }
    $dir = Split-Path $target -Parent
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Copy-Item -LiteralPath $source -Destination $target -Force
}

Write-Host "=== RESTORE V18.35H STABLE SNAPSHOT DONE ==="
Write-Host "FILES_RESTORED: $($rows.Count)"
