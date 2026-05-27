[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 93,
    [switch]$RunDownstreamReview,
    [switch]$NoRerun
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25E_post_merge_validation_rerun.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25E_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25E POST-MERGE VALIDATION RERUN ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "RUN_DOWNSTREAM_REVIEW: $($RunDownstreamReview.IsPresent)"
Write-Host "NO_RERUN: $($NoRerun.IsPresent)"
Write-Host "MODE: READ_ONLY_POST_MERGE_VALIDATION"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)

if ($RunDownstreamReview.IsPresent) {
    $argsList += "--run-downstream-review"
}
if ($NoRerun.IsPresent) {
    $argsList += "--no-rerun"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25E post-merge validation rerun failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25E POST-MERGE VALIDATION RERUN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
