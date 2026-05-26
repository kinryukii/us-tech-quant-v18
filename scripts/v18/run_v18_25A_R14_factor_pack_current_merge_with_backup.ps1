param(
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

Write-Host "===== START V18.25A-R14 FACTOR PACK CURRENT MERGE WITH BACKUP ====="
Write-Host "ROOT: $Root"
Write-Host "MODE: FACTOR_PACK_CURRENT_MERGE_WITH_BACKUP"
Write-Host "CURRENT_FACTOR_PACK_PATH: outputs\v18\factor_pack\V18_CURRENT_RAW105_FACTOR_PACK_RANKING.csv"
Write-Host "EXTERNAL_DATA_FETCHED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    $Python = "python"
}

$ScriptPath = Join-Path $Root "scripts\v18\v18_25A_R14_factor_pack_current_merge_with_backup.py"
$ReadFirstPath = Join-Path $Root "outputs\v18\ops\V18_25A_R14_READ_FIRST.txt"

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Missing V18.25A-R14 Python script: $ScriptPath"
}

Write-Host "PYTHON: $Python"
Write-Host "SCRIPT: $ScriptPath"

& $Python $ScriptPath --root $Root
$PythonExitCode = $LASTEXITCODE
if ($PythonExitCode -ne 0) {
    Write-Host "PYTHON_EXIT_CODE: $PythonExitCode"
}

if (-not (Test-Path -LiteralPath $ReadFirstPath)) {
    Write-Host "READ_FIRST_MISSING: $ReadFirstPath"
    exit 1
}

Write-Host "===== V18.25A-R14 READ_FIRST ====="
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
Write-Host "===== END V18.25A-R14 FACTOR PACK CURRENT MERGE WITH BACKUP ====="
exit 0
