param([string]$Root = "D:\us-tech-quant")
$ErrorActionPreference = "Stop"
$SnapshotRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Manifest = Join-Path $SnapshotRoot "MANIFEST.csv"
if (-not (Test-Path -LiteralPath $Manifest)) { throw "Missing manifest: $Manifest" }
Write-Host "=== RESTORE V18.24B SNAPSHOT START ==="
Import-Csv -LiteralPath $Manifest | Where-Object { $_.status -eq "COPIED" } | ForEach-Object {
    $src = Join-Path $SnapshotRoot $_.relative_snapshot_path
    $dest = Join-Path $Root $_.relative_source_path
    $parent = Split-Path -Parent $dest
    if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent | Out-Null }
    Copy-Item -LiteralPath $src -Destination $dest -Force
}
Write-Host "=== RESTORE V18.24B SNAPSHOT END ==="
exit 0
