param(
    [string]$ProjectRoot = "D:\us-tech-quant",
    [string]$Root = ""
)

if ($Root -and -not $ProjectRoot) {
    $ProjectRoot = $Root
}
if ($Root) {
    $ProjectRoot = $Root
}

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$Script = Join-Path $ProjectRoot "scripts\v18\v18_50C_daily_operator_readability_and_source_audit_lock.py"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing V18.50C script: $Script"
}

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.50C-R1"
Write-Host "PATCH_NAME: COMMAND_CENTER_ACTION_PACKET_SEQUENCE_FIX"
Write-Host "READABILITY_ONLY: TRUE"
Write-Host "WRITES_CURRENT_TOP20_ALIAS: FALSE"
Write-Host "TRADING_EXECUTION_ALLOWED: FALSE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"

& $Python $Script --project-root $ProjectRoot
$Code = $LASTEXITCODE
Write-Host "SCRIPT_EXIT_CODE: $Code"
Write-Host "READ_FIRST_PATH: $(Join-Path $ProjectRoot 'outputs\v18\ops\V18_50C_READ_FIRST.txt')"
if (Test-Path (Join-Path $ProjectRoot 'outputs\v18\ops\V18_50C_READ_FIRST.txt')) {
    Write-Host "--- V18.50C READ_FIRST ---"
    Get-Content (Join-Path $ProjectRoot 'outputs\v18\ops\V18_50C_READ_FIRST.txt')
}
exit $Code
