[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 93,
    [bool]$PlanOnly = $true,
    [switch]$AllowOfficialMerge
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25C_validate_staged_factor_technical_merge_plan.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25C_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25C VALIDATE STAGED FACTOR TECHNICAL MERGE PLAN ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "PLAN_ONLY: $PlanOnly"
Write-Host "MODE: READ_ONLY_STAGED_VALIDATION_MERGE_PLAN"

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)

if ($PlanOnly) {
    $argsList += "--plan-only"
}

if ($AllowOfficialMerge.IsPresent) {
    Write-Host "R25C refuses -AllowOfficialMerge. Official merge belongs to R25D only."
    $argsList += "--allow-official-merge"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25C staged validation merge plan failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25C VALIDATE STAGED FACTOR TECHNICAL MERGE PLAN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
