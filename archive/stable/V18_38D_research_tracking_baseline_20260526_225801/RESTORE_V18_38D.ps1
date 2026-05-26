[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"
$Manifest = Join-Path $PSScriptRoot "MANIFEST.csv"

Write-Host "=== RESTORE V18.38D STABLE SNAPSHOT START ==="
Write-Host "ROOT: $Root"
Write-Host "SNAPSHOT_ROOT: $PSScriptRoot"
Write-Host "MANIFEST: $Manifest"

if (-not (Test-Path $Manifest)) {
    throw "Missing MANIFEST.csv: $Manifest"
}

$Rows = Import-Csv -Path $Manifest
foreach ($Row in $Rows) {
    if ($Row.exists -ne "TRUE" -or $Row.copied -ne "TRUE") {
        continue
    }

    $Source = Join-Path $PSScriptRoot $Row.snapshot_path
    $Target = Join-Path $Root $Row.source_path

    if (-not (Test-Path $Source)) {
        throw "Missing snapshot source: $Source"
    }

    $TargetParent = Split-Path -Parent $Target
    if ($TargetParent -and -not (Test-Path $TargetParent)) {
        New-Item -ItemType Directory -Path $TargetParent -Force | Out-Null
    }

    Copy-Item -LiteralPath $Source -Destination $Target -Force
}

Write-Host "RESTORE_EXECUTED: FALSE"
Write-Host "This restore script was generated only; it has not been executed."
Write-Host "=== RESTORE V18.38D STABLE SNAPSHOT END ==="
