[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$ApplyRestore,
    [switch]$RefreshDerived
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_30B_daily_command_compatibility_guard.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_30B_READ_FIRST.txt"

Write-Host "=== START V18.30B DAILY COMMAND COMPATIBILITY GUARD ==="
Write-Host "ROOT: $Root"
Write-Host "MODE: DAILY_COMMAND_COMPATIBILITY_GUARD"
Write-Host "APPLY_RESTORE: $($ApplyRestore.IsPresent)"
Write-Host "REFRESH_DERIVED: $($RefreshDerived.IsPresent)"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

$argsList = @($scriptPath, "--root", $Root)
if ($ApplyRestore.IsPresent) {
    $argsList += "--apply-restore"
}
if ($RefreshDerived.IsPresent) {
    $argsList += "--refresh-derived"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "V18.30B daily command compatibility guard failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.30B DAILY COMMAND COMPATIBILITY GUARD ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
