[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [bool]$IncludeBatch3History = $true,
    [int]$MaxTickers = 200
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R24_factor_technical_tier_refresh_readiness_audit.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R24_READ_FIRST.txt"

Write-Host "=== START V18.25A-R24 FACTOR TECHNICAL TIER REFRESH READINESS AUDIT ==="
Write-Host "ROOT: $Root"
Write-Host "INCLUDE_BATCH3_HISTORY: $IncludeBatch3History"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "MODE: READ_ONLY_REFRESH_READINESS_AUDIT"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)
if ($IncludeBatch3History) {
    $argsList += "--include-batch3-history"
} else {
    $argsList += "--no-include-batch3-history"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R24 readiness audit failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R24 FACTOR TECHNICAL TIER REFRESH READINESS AUDIT ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
