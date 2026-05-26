param(
    [string]$Root = "D:\us-tech-quant",
    [switch]$UseYFinance,
    [switch]$SkipOfficialDaily,
    [switch]$SkipRankedCandidates,
    [switch]$SkipUnifiedLink
)

$ErrorActionPreference = "Stop"

Write-Host "=== V18.13D DAILY COMMAND CENTER START ==="
Write-Host "ROOT: $Root"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "SKIP_OFFICIAL_DAILY: $SkipOfficialDaily"
Write-Host "SKIP_RANKED_CANDIDATES: $SkipRankedCandidates"
Write-Host "SKIP_UNIFIED_LINK: $SkipUnifiedLink"
Write-Host "OFFICIAL_DECISION_IMPACT: NONE"
Write-Host "AUTO_TRADE: DISABLED"
Write-Host "AUTO_SELL: DISABLED"
Write-Host "READ_ONLY: TRUE"
Write-Host "COMMAND_CENTER_ONLY: TRUE"

$Python = Join-Path $Root ".venv\Scripts\python.exe"
$SummaryScript = Join-Path $Root "scripts\v18\v18_13D_daily_command_center.py"
$RunLog = Join-Path $Root "outputs\v18\ops\V18_13D_CURRENT_DAILY_COMMAND_CENTER_RUN_LOG.csv"
$ReadFirst = Join-Path $Root "outputs\v18\read_center\V18_13D_READ_FIRST.txt"
$SummaryPath = Join-Path $Root "outputs\v18\read_center\V18_13D_CURRENT_DAILY_COMMAND_CENTER_SUMMARY.csv"

if (-not (Test-Path $Python)) {
    throw "Missing Python executable: $Python"
}
if (-not (Test-Path $SummaryScript)) {
    throw "Missing Python script: $SummaryScript"
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $RunLog) | Out-Null
$RunRows = New-Object System.Collections.Generic.List[object]

function Add-RunRow {
    param(
        [string]$Step,
        [string]$Status,
        [int]$ExitCode,
        [string]$Script,
        [string]$Note
    )
    $RunRows.Add([pscustomobject]@{
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
        step = $Step
        status = $Status
        exit_code = $ExitCode
        script = $Script
        note = $Note
    }) | Out-Null
}

function Invoke-CommandCenterStep {
    param(
        [string]$Step,
        [string]$Script,
        [string[]]$Arguments,
        [switch]$ContinueOnFailure
    )
    Write-Host ""
    Write-Host "RUN_STEP: $Step"
    Write-Host "SCRIPT: $Script"
    if (-not (Test-Path $Script)) {
        Add-RunRow -Step $Step -Status "FAIL" -ExitCode 1 -Script $Script -Note "MISSING_SCRIPT"
        if (-not $ContinueOnFailure) {
            throw "MISSING_SCRIPT: $Script"
        }
        return $false
    }

    & powershell -NoProfile -ExecutionPolicy Bypass -File $Script @Arguments
    $Code = $LASTEXITCODE
    if ($Code -eq 0) {
        Add-RunRow -Step $Step -Status "PASS" -ExitCode 0 -Script $Script -Note "OK"
        return $true
    }

    Add-RunRow -Step $Step -Status "FAIL" -ExitCode $Code -Script $Script -Note "NONZERO_EXIT"
    if (-not $ContinueOnFailure) {
        throw "STEP_FAILED: $Step"
    }
    return $false
}

if ($SkipOfficialDaily) {
    Add-RunRow -Step "OFFICIAL_DAILY" -Status "SKIPPED" -ExitCode 0 -Script "scripts\v18\run_v18_current_official_daily.ps1" -Note "SKIP_OFFICIAL_DAILY"
}
else {
    $OfficialScript = Join-Path $Root "scripts\v18\run_v18_current_official_daily.ps1"
    $OfficialArgs = @()
    if ($UseYFinance) {
        $OfficialArgs += "-UseYFinance"
    }
    Invoke-CommandCenterStep -Step "OFFICIAL_DAILY" -Script $OfficialScript -Arguments $OfficialArgs | Out-Null
}

$AOk = Invoke-CommandCenterStep -Step "V18_13A" -Script (Join-Path $Root "scripts\v18\run_v18_13A_unified_daily_read_center_link.ps1") -Arguments @("-Root", $Root)
if (-not $AOk) {
    $RunRows | Export-Csv -Path $RunLog -NoTypeInformation -Encoding UTF8
    & $Python $SummaryScript --root $Root | Out-Host
    exit 1
}

if ($SkipRankedCandidates) {
    Add-RunRow -Step "V18_13B" -Status "SKIPPED" -ExitCode 0 -Script "scripts\v18\run_v18_13B_ranked_candidate_read_center.ps1" -Note "SKIP_RANKED_CANDIDATES"
}
else {
    Invoke-CommandCenterStep -Step "V18_13B" -Script (Join-Path $Root "scripts\v18\run_v18_13B_ranked_candidate_read_center.ps1") -Arguments @("-Root", $Root) -ContinueOnFailure | Out-Null
}

if ($SkipUnifiedLink) {
    Add-RunRow -Step "V18_13C" -Status "SKIPPED" -ExitCode 0 -Script "scripts\v18\run_v18_13C_ranked_candidate_unified_link.ps1" -Note "SKIP_UNIFIED_LINK"
}
else {
    Invoke-CommandCenterStep -Step "V18_13C" -Script (Join-Path $Root "scripts\v18\run_v18_13C_ranked_candidate_unified_link.ps1") -Arguments @("-Root", $Root) -ContinueOnFailure | Out-Null
}

$RunRows | Export-Csv -Path $RunLog -NoTypeInformation -Encoding UTF8

& $Python -m py_compile $SummaryScript
if ($LASTEXITCODE -ne 0) {
    throw "PY_COMPILE_FAILED: $SummaryScript"
}

& $Python $SummaryScript --root $Root
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if (-not (Test-Path $SummaryPath)) {
    throw "Missing summary output: $SummaryPath"
}

$Summary = @{}
Import-Csv -Path $SummaryPath | ForEach-Object {
    $Summary[$_.metric] = $_.value
}

Write-Host "STATUS: $($Summary['STATUS'])"
Write-Host "RUN_MODE: $($Summary['RUN_MODE'])"
Write-Host "OFFICIAL_DAILY_STATUS: $($Summary['OFFICIAL_DAILY_STATUS'])"
Write-Host "V18_13A_STATUS: $($Summary['V18_13A_STATUS'])"
Write-Host "V18_13B_STATUS: $($Summary['V18_13B_STATUS'])"
Write-Host "V18_13C_STATUS: $($Summary['V18_13C_STATUS'])"
Write-Host "RANK_SOURCE_STATUS: $($Summary['RANK_SOURCE_STATUS'])"
Write-Host "SECOND_STAGE_COUNT: $($Summary['SECOND_STAGE_COUNT'])"
Write-Host "SCORED_TICKER_COUNT: $($Summary['SCORED_TICKER_COUNT'])"
Write-Host "UNSCORED_TICKER_COUNT: $($Summary['UNSCORED_TICKER_COUNT'])"
Write-Host "TOP_5_TICKERS: $($Summary['TOP_5_TICKERS'])"
Write-Host "OFFICIAL_DECISION_IMPACT: $($Summary['OFFICIAL_DECISION_IMPACT'])"
Write-Host "AUTO_TRADE: $($Summary['AUTO_TRADE'])"
Write-Host "AUTO_SELL: $($Summary['AUTO_SELL'])"
Write-Host "READ_ONLY: $($Summary['READ_ONLY'])"
Write-Host "COMMAND_CENTER_ONLY: $($Summary['COMMAND_CENTER_ONLY'])"
Write-Host "READ_FIRST: $($Summary['READ_FIRST'])"
Write-Host "MAIN_READ: $($Summary['MAIN_READ'])"
