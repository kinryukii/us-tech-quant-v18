param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$FetchStagedVix
)

$ErrorActionPreference = "Stop"

Write-Host "===== START V18.25A-R8 CONTROLLED STAGED VIX BACKFILL ====="
Write-Host "ROOT: $Root"
Write-Host "MODE: CONTROLLED_STAGED_VIX_BACKFILL_STAGED_ONLY"
if ($FetchStagedVix) {
    Write-Host "RUN_MODE: FETCH_STAGED_VIX"
    Write-Host "FETCH_SCOPE: ^VIX first, VIX fallback only"
} else {
    Write-Host "RUN_MODE: PLAN_ONLY"
    Write-Host "EXTERNAL_FETCH_REFUSED_WITHOUT_SWITCH: TRUE"
}
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$ScriptPath = Join-Path $Root "scripts\v18\v18_25A_R8_controlled_staged_vix_backfill.py"
$ReadFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R8_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Missing V18.25A-R8 Python script: $ScriptPath"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $ScriptPath"

$ArgsList = @($ScriptPath, "--root", $Root)
if ($FetchStagedVix) {
    $ArgsList += "--fetch-staged-vix"
}

& $Python @ArgsList
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (-not (Test-Path -LiteralPath $ReadFirstPath)) {
    Write-Host "READ_FIRST_MISSING: $ReadFirstPath"
    exit 1
}

Write-Host "===== V18.25A-R8 READ_FIRST ====="
$ReadFirstContent = Get-Content -LiteralPath $ReadFirstPath
$ReadFirstContent | ForEach-Object { Write-Host $_ }

$StatusLine = $ReadFirstContent | Where-Object { $_ -like "STATUS:*" } | Select-Object -First 1
if ($StatusLine -like "STATUS: FAIL*") {
    Write-Host "READ_FIRST_STATUS_FAIL: TRUE"
    exit 1
}
if ($PythonExitCode -ne 0) {
    exit $PythonExitCode
}

Write-Host "READ_FIRST: $ReadFirstPath"
Write-Host "===== END V18.25A-R8 CONTROLLED STAGED VIX BACKFILL ====="
exit 0
