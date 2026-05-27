[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$BatchSize = 65,
    [int]$LookbackDays = 5,
    [switch]$AllowSameDayContinuation,
    [switch]$ApplyPlan,
    [bool]$ExcludeTodaySuccess = $true
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R22_rolling_multi_run_continuation_scheduler.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R22_READ_FIRST.txt"

Write-Host "=== START V18.25A-R22 ROLLING MULTI-RUN CONTINUATION SCHEDULER ==="
Write-Host "ROOT: $Root"
Write-Host "BATCH_SIZE: $BatchSize"
Write-Host "LOOKBACK_DAYS: $LookbackDays"
Write-Host "ALLOW_SAME_DAY_CONTINUATION: $($AllowSameDayContinuation.IsPresent)"
Write-Host "APPLY_PLAN: $($ApplyPlan.IsPresent)"
Write-Host "EXCLUDE_TODAY_SUCCESS: $ExcludeTodaySuccess"
Write-Host "MODE: $(if ($ApplyPlan.IsPresent) { 'APPLY_PLAN_METADATA_ONLY' } else { 'DRYRUN_PLAN_ONLY' })"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--batch-size", $BatchSize,
    "--lookback-days", $LookbackDays
)

if ($AllowSameDayContinuation.IsPresent) {
    $argsList += "--allow-same-day-continuation"
}
if ($ApplyPlan.IsPresent) {
    $argsList += "--apply-plan"
}
if ($ExcludeTodaySuccess) {
    $argsList += "--exclude-today-success"
} else {
    $argsList += "--no-exclude-today-success"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R22 scheduler failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R22 ROLLING MULTI-RUN CONTINUATION SCHEDULER ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
