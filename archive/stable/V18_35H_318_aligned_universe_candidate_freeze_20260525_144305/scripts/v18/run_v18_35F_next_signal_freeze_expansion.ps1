param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyNextSignalFreezeExpansion
)

$ErrorActionPreference = "Stop"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_35F_next_signal_freeze_expansion.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_35F_READ_FIRST.txt"

Write-Host "=== START V18.35F NEXT SIGNAL FREEZE EXPANSION ==="
Write-Host "ROOT: $Root"
Write-Host "APPLY_NEXT_SIGNAL_FREEZE_EXPANSION: $ApplyNextSignalFreezeExpansion"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

if (-not (Test-Path $Script)) {
    Write-Host "STATUS: FAIL_V18_35F_NEXT_SIGNAL_FREEZE_EXPANSION_FAILED"
    throw "Missing script: $Script"
}

$Args35F = @("--root", $Root)
if ($ApplyNextSignalFreezeExpansion) { $Args35F += "--apply-next-signal-freeze-expansion" }

& $Python $Script @Args35F
$ExitCode = $LASTEXITCODE

if (Test-Path $ReadFirst) {
    Write-Host "--- V18.35F READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

Write-Host "=== DONE V18.35F NEXT SIGNAL FREEZE EXPANSION ==="
Write-Host "READ_FIRST: $ReadFirst"

if ($ExitCode -ne 0) {
    exit $ExitCode
}

if (Test-Path $ReadFirst) {
    $StatusLine = Select-String -Path $ReadFirst -Pattern '^STATUS:\s*FAIL_' -SimpleMatch:$false
    if ($StatusLine) { exit 1 }
}

exit 0
