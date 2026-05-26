[CmdletBinding()]
param(
    [string]$Root = "D:\us-tech-quant",
    [int]$MaxTickers = 100,
    [bool]$PlanOnly = $true,
    [bool]$IncludeTechnicalPlan = $true,
    [switch]$AllowModifyFactorPack,
    [switch]$AllowModifyTechnicalTiming
)

$ErrorActionPreference = "Stop"

$scriptPath = Join-Path $PSScriptRoot "v18_25A_R25_factor_technical_refresh_build_plan.py"
$pythonExe = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

$readFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R25_READ_FIRST.txt"

Write-Host "=== START V18.25A-R25 FACTOR TECHNICAL REFRESH BUILD PLAN ==="
Write-Host "ROOT: $Root"
Write-Host "MAX_TICKERS: $MaxTickers"
Write-Host "PLAN_ONLY: $PlanOnly"
Write-Host "INCLUDE_TECHNICAL_PLAN: $IncludeTechnicalPlan"
Write-Host "MODE: READ_ONLY_FACTOR_TECHNICAL_REFRESH_PLAN"

if ($AllowModifyFactorPack.IsPresent -or $AllowModifyTechnicalTiming.IsPresent) {
    Write-Host "R25 refuses modification flags. Factor/technical modification belongs to a later R25B/R26 step."
    throw "R25 is plan-only; remove AllowModifyFactorPack/AllowModifyTechnicalTiming."
}

$argsList = @(
    $scriptPath,
    "--root", $Root,
    "--max-tickers", $MaxTickers
)
if ($IncludeTechnicalPlan) {
    $argsList += "--include-technical-plan"
} else {
    $argsList += "--no-include-technical-plan"
}

& $pythonExe @argsList
if ($LASTEXITCODE -ne 0) {
    throw "R25 factor technical refresh build plan failed with exit code $LASTEXITCODE"
}

$statusLine = ""
if (Test-Path $readFirstPath) {
    $statusLine = (Select-String -Path $readFirstPath -Pattern '^STATUS:' | Select-Object -First 1).Line
}

Write-Host "=== END V18.25A-R25 FACTOR TECHNICAL REFRESH BUILD PLAN ==="
Write-Host $statusLine
Write-Host "READ_FIRST: $readFirstPath"
