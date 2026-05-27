[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyCleanup
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_30D_same_day_signal_freeze_replace_policy.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_30D_READ_FIRST.txt"

Write-Host "=== START V18.30D SAME-DAY SIGNAL FREEZE REPLACE POLICY ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: SAME_DAY_SIGNAL_FREEZE_REPLACE_POLICY"
Write-Host "APPLY_CLEANUP: $($ApplyCleanup.IsPresent)"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @($scriptPath, "--root", $Root)
if ($ApplyCleanup.IsPresent) {
    $argsList += "--apply-cleanup"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "V18.30D same-day signal freeze replace policy failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.30D SAME-DAY SIGNAL FREEZE REPLACE POLICY ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
