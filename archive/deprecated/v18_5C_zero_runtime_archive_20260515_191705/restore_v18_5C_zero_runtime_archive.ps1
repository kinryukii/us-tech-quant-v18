$ErrorActionPreference = "Stop"
$Root = "D:\us-tech-quant"
$ArchiveRoot = "D:\us-tech-quant\archive\deprecated\v18_5C_zero_runtime_archive_20260515_191705"

$src = Join-Path $ArchiveRoot "scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1"
$dst = Join-Path $Root "scripts\run_v17_7C_manual_daily_with_raw_universe_audit.ps1"
if (Test-Path $src) {
    New-Item -ItemType Directory -Force -Path (Split-Path $dst -Parent) | Out-Null
    Move-Item -LiteralPath $src -Destination $dst -Force
    Write-Host "RESTORED: " $dst
}

