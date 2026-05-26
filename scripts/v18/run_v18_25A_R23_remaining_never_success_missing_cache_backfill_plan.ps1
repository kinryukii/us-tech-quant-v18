[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 65,
    [bool]$PlanOnly = $true,
    [switch]$AllowExternalFetch
)

$ErrorActionPreference = "Stop"

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R23_READ_FIRST.txt"

Write-Host "=== START V18.25A-R23 REMAINING NEVER-SUCCESS MISSING-CACHE BACKFILL PLAN ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "PLAN_ONLY: $PlanOnly"
Write-Host "ALLOW_EXTERNAL_FETCH: $($AllowExternalFetch.IsPresent)"
Write-Host "MODE: PLAN_ONLY_MISSING_CACHE_BACKFILL"

if ($AllowExternalFetch.IsPresent) {
    Write-Host "R23 refuses external fetch. External fetch belongs to R23B controlled staged backfill execution."
    Write-Host "=== END V18.25A-R23 REMAINING NEVER-SUCCESS MISSING-CACHE BACKFILL PLAN ==="
    Write-Host "STATUS: REFUSED_EXTERNAL_FETCH_FOR_R23"
    Write-Host "READ_FIRST: $readFirstPath"
    exit 1
}

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R23_remaining_never_success_missing_cache_backfill_plan.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

& $pythonExe $scriptPath --root $Root --max-tickers $MaxTickers
if ($LASTEXITCODE -ne 0) {
    throw "R23 missing-cache backfill plan failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R23 REMAINING NEVER-SUCCESS MISSING-CACHE BACKFILL PLAN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
