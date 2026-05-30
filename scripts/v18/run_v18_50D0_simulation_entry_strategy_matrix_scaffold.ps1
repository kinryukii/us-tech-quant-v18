param(
    [string]$ProjectRoot = "",
    [string]$Root = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    if ([string]::IsNullOrWhiteSpace($Root)) {
        $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
    } else {
        $ProjectRoot = $Root
    }
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\v18\v18_50D0_simulation_entry_strategy_matrix_scaffold.py"
$ReadFirst = Join-Path $ProjectRoot "outputs\v18\ops\V18_50D0_READ_FIRST.txt"

if (-not (Test-Path $Python)) { throw "Missing Python executable: $Python" }
if (-not (Test-Path $Script)) { throw "Missing V18.50D-0 script: $Script" }

Write-Host "PATCH_VERSION: V18.50D-0"
Write-Host "PATCH_NAME: SIMULATION_ENTRY_STRATEGY_MATRIX_SCAFFOLD"
Write-Host "RESEARCH_ONLY: TRUE"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"
Write-Host "WRITES_CURRENT_TOP20_ALIAS: FALSE"

& $Python $Script --project-root $ProjectRoot
$ExitCode = $LASTEXITCODE
Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
exit $ExitCode
