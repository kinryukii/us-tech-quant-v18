param(
    [switch]$CreateTemplatesOnly,
    [switch]$AllowEmptyManualFiles
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Script = Join-Path $Root "scripts\v18\v18_15A_manual_position_trade_feedback.py"
$SummaryPath = Join-Path $Root "outputs\v18\ops\V18_15A_CURRENT_MANUAL_POSITION_TRADE_FEEDBACK_SUMMARY.csv"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $Script)) {
    throw "Missing Python script: $Script"
}

Write-Host "=== V18.15A MANUAL POSITION TRADE FEEDBACK START ==="
Write-Host "ROOT: $Root"
Write-Host "CREATE_TEMPLATES_ONLY: $CreateTemplatesOnly"
Write-Host "ALLOW_EMPTY_MANUAL_FILES: $AllowEmptyManualFiles"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "MANUAL_INPUT_ONLY: TRUE"
Write-Host "POSITION_FEEDBACK_ONLY: TRUE"

$Args = @($Script, "--root", $Root)
if ($CreateTemplatesOnly) {
    $Args += "--create-templates-only"
}
if ($AllowEmptyManualFiles) {
    $Args += "--allow-empty-manual-files"
}

& $Python @Args
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

$Summary = @{}
if (Test-Path $SummaryPath) {
    Import-Csv -Path $SummaryPath | Select-Object -First 1 | ForEach-Object {
        $_.PSObject.Properties | ForEach-Object {
            $Summary[$_.Name] = $_.Value
        }
    }
}

Write-Host ""
Write-Host "=== V18.15A COMPACT SUMMARY ==="
foreach ($Key in @(
    "STATUS",
    "POSITION_COUNT",
    "TRADE_LOG_ROWS",
    "LINKED_SIGNAL_ROWS",
    "UNLINKED_POSITION_ROWS",
    "VALIDATION_FAIL_COUNT",
    "OFFICIAL_DECISION_IMPACT",
    "AUTO_TRADE",
    "AUTO_SELL",
    "READ_FIRST"
)) {
    Write-Host "$($Key): $($Summary[$Key.ToLower()])"
}
