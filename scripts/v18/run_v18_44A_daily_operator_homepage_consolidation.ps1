param(
    [switch]$WriteCurrent,
    [switch]$Strict,
    [switch]$IncludeFileChecklist,
    [switch]$IncludeWarningDetails,
    [switch]$RequireTopNCurrent,
    [string]$Root = "D:\us-tech-quant"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
if (-not (Test-Path $Root)) {
    $Root = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}

$Python = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Script = Join-Path $Root "scripts\v18\v18_44A_daily_operator_homepage_consolidation.py"
$ReadFirst = Join-Path $Root "outputs\v18\ops\V18_44A_READ_FIRST.txt"

Write-Host "DELEGATING_TO: $Script"
Write-Host "PATCH_VERSION: V18.44A"
Write-Host "WRITE_CURRENT: $WriteCurrent"
Write-Host "INCLUDE_FILE_CHECKLIST: $IncludeFileChecklist"
Write-Host "INCLUDE_WARNING_DETAILS: $IncludeWarningDetails"
Write-Host "REQUIRE_TOPN_CURRENT: $RequireTopNCurrent"
Write-Host "STRICT: $Strict"

if (-not (Test-Path $Script)) {
    throw "Missing script: $Script"
}

$Args44A = @(
    "--root", $Root
)
if ($WriteCurrent) { $Args44A += "--write-current" }
if ($Strict) { $Args44A += "--strict" }
if ($IncludeFileChecklist) { $Args44A += "--include-file-checklist" }
if ($IncludeWarningDetails) { $Args44A += "--include-warning-details" }
if ($RequireTopNCurrent) { $Args44A += "--require-topn-current" }

& $Python $Script @Args44A
$ExitCode = $LASTEXITCODE

Write-Host "SCRIPT_EXIT_CODE: $ExitCode"
Write-Host "READ_FIRST_PATH: $ReadFirst"
if (Test-Path $ReadFirst) {
    Write-Host "--- V18.44A READ_FIRST ---"
    Get-Content -Path $ReadFirst | ForEach-Object { Write-Host $_ }
}

if ($ExitCode -ne 0) {
    exit $ExitCode
}
exit 0
