param(
    [double]$InitialCashUSD = 2000.0,
    [int]$MaxNewPositions = 3,
    [int]$MaxReportRows = 40,
    [switch]$SkipOfficialDaily,
    [switch]$UseYFinance,
    [switch]$AllowLocalApprox,
    [switch]$OverwriteForward
)

$ErrorActionPreference = "Stop"

$Root = "D:\us-tech-quant"

$OfficialWithSim = Join-Path $Root "scripts\v18\run_v18_8C_official_daily_fast_with_simulation.ps1"
$CandidateTracker = Join-Path $Root "scripts\v18\run_v18_9A_simulation_candidate_tracker.ps1"
$ForwardFiller = Join-Path $Root "scripts\v18\run_v18_9B_forward_return_filler.ps1"

$ReadCenterDir = Join-Path $Root "outputs\v18\read_center"
$SimDir = Join-Path $Root "outputs\v18\simulation"
$OpsDir = Join-Path $Root "outputs\v18\ops"

New-Item -ItemType Directory -Force -Path $ReadCenterDir | Out-Null
New-Item -ItemType Directory -Force -Path $OpsDir | Out-Null

$CombinedReadFirst = Join-Path $ReadCenterDir "V18_9C_READ_FIRST.txt"
$CombinedReport = Join-Path $ReadCenterDir "V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION.md"
$Profile = Join-Path $OpsDir "V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_PROFILE.csv"
$StepCsv = Join-Path $OpsDir "V18_9C_CURRENT_OFFICIAL_DAILY_WITH_SIM_VALIDATION_STEPS.csv"

$V88CReadFirst = Join-Path $ReadCenterDir "V18_8C_READ_FIRST.txt"
$V88CReport = Join-Path $ReadCenterDir "V18_8C_CURRENT_OFFICIAL_DAILY_FAST_WITH_SIMULATION.md"

$V89AReadFirst = Join-Path $SimDir "V18_9A_READ_FIRST.txt"
$V89AReport = Join-Path $SimDir "V18_9A_CURRENT_SIM_CANDIDATE_TRACKER.md"

$V89BReadFirst = Join-Path $SimDir "V18_9B_READ_FIRST.txt"
$V89BReport = Join-Path $SimDir "V18_9B_CURRENT_FORWARD_RETURN_FILLER.md"

function Read-TextSafe {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        return ""
    }

    try {
        return Get-Content $Path -Raw -Encoding UTF8
    } catch {
        return Get-Content $Path -Raw
    }
}

function Extract-Field {
    param(
        [string]$Text,
        [string]$Field,
        [string]$Default = "UNKNOWN"
    )

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return $Default
    }

    $prefixes = @(
        "${Field}:",
        "- ${Field}:",
        "* ${Field}:",
        "${Field}：",
        "- ${Field}：",
        "* ${Field}："
    )

    foreach ($line in ($Text -split "`n")) {
        $t = $line.Trim().Trim("`r")
        foreach ($p in $prefixes) {
            if ($t.StartsWith($p, [System.StringComparison]::OrdinalIgnoreCase)) {
                $v = $t.Substring($p.Length).Trim()
                $v = $v.Trim([char]0x60).Trim()
                if (-not [string]::IsNullOrWhiteSpace($v)) {
                    return $v
                }
            }
        }
    }

    return $Default
}

$Start = Get-Date
$Steps = @()

function Add-Step {
    param(
        [string]$Step,
        [string]$Status,
        [datetime]$StartTime,
        [datetime]$EndTime,
        [string]$Detail
    )

    $script:Steps += [pscustomobject]@{
        Step = $Step
        Status = $Status
        StartTime = $StartTime.ToString('yyyy-MM-dd HH:mm:ss')
        EndTime = $EndTime.ToString('yyyy-MM-dd HH:mm:ss')
        Seconds = [math]::Round(($EndTime - $StartTime).TotalSeconds, 3)
        Detail = $Detail
    }
}

Write-Host ""
Write-Host "=== V18.9C OFFICIAL DAILY WITH SIM VALIDATION START ==="
Write-Host "ROOT: $Root"
Write-Host "SKIP_OFFICIAL_DAILY: $SkipOfficialDaily"
Write-Host "USE_YFINANCE: $UseYFinance"
Write-Host "ALLOW_LOCAL_APPROX: $AllowLocalApprox"
Write-Host "OVERWRITE_FORWARD: $OverwriteForward"
Write-Host ""

if (-not (Test-Path $OfficialWithSim)) {
    throw "MISSING_WRAPPER: $OfficialWithSim"
}

if (-not (Test-Path $CandidateTracker)) {
    throw "MISSING_WRAPPER: $CandidateTracker"
}

if (-not (Test-Path $ForwardFiller)) {
    throw "MISSING_WRAPPER: $ForwardFiller"
}

$s = Get-Date
Write-Host "STEP 1: run V18.8C official daily fast with simulation"

$args88C = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $OfficialWithSim,
    "-InitialCashUSD", $InitialCashUSD,
    "-MaxNewPositions", $MaxNewPositions
)

if ($SkipOfficialDaily) {
    $args88C += "-SkipOfficialDaily"
}

& powershell @args88C

if ($LASTEXITCODE -ne 0) {
    $e = Get-Date
    Add-Step -Step "V18_8C_OFFICIAL_DAILY_WITH_SIM" -Status "FAIL" -StartTime $s -EndTime $e -Detail $OfficialWithSim
    throw "FAIL: V18.8C official daily with simulation"
}

$e = Get-Date
Add-Step -Step "V18_8C_OFFICIAL_DAILY_WITH_SIM" -Status "OK" -StartTime $s -EndTime $e -Detail $OfficialWithSim

$s = Get-Date
Write-Host ""
Write-Host "STEP 2: run V18.9A simulation candidate tracker"

& powershell -NoProfile -ExecutionPolicy Bypass -File $CandidateTracker -MaxReportRows $MaxReportRows

if ($LASTEXITCODE -ne 0) {
    $e = Get-Date
    Add-Step -Step "V18_9A_SIM_CANDIDATE_TRACKER" -Status "FAIL" -StartTime $s -EndTime $e -Detail $CandidateTracker
    throw "FAIL: V18.9A simulation candidate tracker"
}

$e = Get-Date
Add-Step -Step "V18_9A_SIM_CANDIDATE_TRACKER" -Status "OK" -StartTime $s -EndTime $e -Detail $CandidateTracker

$s = Get-Date
Write-Host ""
Write-Host "STEP 3: run V18.9B forward return filler"

$args89B = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", $ForwardFiller,
    "-MaxReportRows", $MaxReportRows
)

if ($UseYFinance) {
    $args89B += "-UseYFinance"
}

if ($AllowLocalApprox) {
    $args89B += "-AllowLocalApprox"
}

if ($OverwriteForward) {
    $args89B += "-Overwrite"
}

& powershell @args89B

if ($LASTEXITCODE -ne 0) {
    $e = Get-Date
    Add-Step -Step "V18_9B_FORWARD_RETURN_FILLER" -Status "FAIL" -StartTime $s -EndTime $e -Detail $ForwardFiller
    throw "FAIL: V18.9B forward return filler"
}

$e = Get-Date
Add-Step -Step "V18_9B_FORWARD_RETURN_FILLER" -Status "OK" -StartTime $s -EndTime $e -Detail $ForwardFiller

$Text88C = Read-TextSafe $V88CReadFirst
$Text89A = Read-TextSafe $V89AReadFirst
$Text89B = Read-TextSafe $V89BReadFirst

$AllText = $Text88C + "`n" + $Text89A + "`n" + $Text89B

$FinalAction = Extract-Field -Text $AllText -Field "FINAL_ACTION"
$BuyPermission = Extract-Field -Text $AllText -Field "BUY_PERMISSION"
$VixRegime = Extract-Field -Text $AllText -Field "VIX_REGIME"
$OfficialImpact = Extract-Field -Text $AllText -Field "OFFICIAL_DECISION_IMPACT"

$SimStatus = Extract-Field -Text $AllText -Field "SIM_STATUS"
$SimMode = Extract-Field -Text $AllText -Field "SIM_MODE"
$OfficialPermission = Extract-Field -Text $AllText -Field "OFFICIAL_PERMISSION"
$CashUSD = Extract-Field -Text $AllText -Field "CASH_USD"
$MarketValueUSD = Extract-Field -Text $AllText -Field "MARKET_VALUE_USD"
$EquityUSD = Extract-Field -Text $AllText -Field "EQUITY_USD"
$PositionCount = Extract-Field -Text $AllText -Field "POSITION_COUNT"

$CandidateTrackerStatus = Extract-Field -Text $Text89A -Field "STATUS"
$TodayCandidateCount = Extract-Field -Text $Text89A -Field "TODAY_CANDIDATE_COUNT"
$EligibleSimBuyCount = Extract-Field -Text $Text89A -Field "ELIGIBLE_SIM_BUY_COUNT"
$ObserveOrBlockedCount = Extract-Field -Text $Text89A -Field "OBSERVE_OR_BLOCKED_COUNT"
$TrackerTotalRows = Extract-Field -Text $Text89A -Field "TRACKER_TOTAL_ROWS"

$ForwardStatus = Extract-Field -Text $Text89B -Field "STATUS"
$YFinanceStatus = Extract-Field -Text $Text89B -Field "YFINANCE_STATUS"
$TrackerRows = Extract-Field -Text $Text89B -Field "TRACKER_ROWS"
$FilledCellsThisRun = Extract-Field -Text $Text89B -Field "FILLED_CELLS_THIS_RUN"
$PendingCellsThisRun = Extract-Field -Text $Text89B -Field "PENDING_CELLS_THIS_RUN"
$ForwardCompleteRows = Extract-Field -Text $Text89B -Field "FORWARD_COMPLETE_ROWS"
$ForwardPartialRows = Extract-Field -Text $Text89B -Field "FORWARD_PARTIAL_ROWS"
$PendingForwardRows = Extract-Field -Text $Text89B -Field "PENDING_FORWARD_ROWS"

$End = Get-Date
$TotalSeconds = [math]::Round(($End - $Start).TotalSeconds, 3)

$Steps | Export-Csv -NoTypeInformation -Encoding UTF8 $StepCsv

$ProfileRows = @(
    [pscustomobject]@{
        RunName = "V18.9C_OFFICIAL_DAILY_WITH_SIM_VALIDATION"
        StartedAt = $Start.ToString('yyyy-MM-dd HH:mm:ss')
        EndedAt = $End.ToString('yyyy-MM-dd HH:mm:ss')
        TotalSeconds = $TotalSeconds
        FinalAction = $FinalAction
        BuyPermission = $BuyPermission
        VixRegime = $VixRegime
        OfficialPermission = $OfficialPermission
        SimStatus = $SimStatus
        CandidateTrackerStatus = $CandidateTrackerStatus
        ForwardStatus = $ForwardStatus
        YFinanceStatus = $YFinanceStatus
        TodayCandidateCount = $TodayCandidateCount
        PendingForwardRows = $PendingForwardRows
        OfficialDecisionImpact = $OfficialImpact
    }
)

$ProfileRows | Export-Csv -NoTypeInformation -Encoding UTF8 $Profile

$Report = @()
$Report += '# V18.9C Official Daily With Simulation Validation'
$Report += ''
$Report += ('- STATUS: `{0}`' -f 'OK_OFFICIAL_DAILY_WITH_SIM_VALIDATION_READY')
$Report += ('- MODE: `{0}`' -f 'OFFICIAL_DAILY_PLUS_SHADOW_SIM_VALIDATION')
$Report += ('- TOTAL_SECONDS: `{0}`' -f $TotalSeconds)
$Report += ('- USE_YFINANCE: `{0}`' -f $UseYFinance)
$Report += ('- ALLOW_LOCAL_APPROX: `{0}`' -f $AllowLocalApprox)
$Report += ''
$Report += '## Official Decision'
$Report += ''
$Report += ('- FINAL_ACTION: `{0}`' -f $FinalAction)
$Report += ('- BUY_PERMISSION: `{0}`' -f $BuyPermission)
$Report += ('- VIX_REGIME: `{0}`' -f $VixRegime)
$Report += ('- OFFICIAL_DECISION_IMPACT: `{0}`' -f $OfficialImpact)
$Report += ''
$Report += '## Simulation Cabin'
$Report += ''
$Report += ('- SIM_STATUS: `{0}`' -f $SimStatus)
$Report += ('- SIM_MODE: `{0}`' -f $SimMode)
$Report += ('- OFFICIAL_PERMISSION: `{0}`' -f $OfficialPermission)
$Report += ('- CASH_USD: `{0}`' -f $CashUSD)
$Report += ('- MARKET_VALUE_USD: `{0}`' -f $MarketValueUSD)
$Report += ('- EQUITY_USD: `{0}`' -f $EquityUSD)
$Report += ('- POSITION_COUNT: `{0}`' -f $PositionCount)
$Report += ''
$Report += '## Candidate Tracker'
$Report += ''
$Report += ('- CANDIDATE_TRACKER_STATUS: `{0}`' -f $CandidateTrackerStatus)
$Report += ('- TODAY_CANDIDATE_COUNT: `{0}`' -f $TodayCandidateCount)
$Report += ('- ELIGIBLE_SIM_BUY_COUNT: `{0}`' -f $EligibleSimBuyCount)
$Report += ('- OBSERVE_OR_BLOCKED_COUNT: `{0}`' -f $ObserveOrBlockedCount)
$Report += ('- TRACKER_TOTAL_ROWS: `{0}`' -f $TrackerTotalRows)
$Report += ''
$Report += '## Forward Return Filler'
$Report += ''
$Report += ('- FORWARD_STATUS: `{0}`' -f $ForwardStatus)
$Report += ('- YFINANCE_STATUS: `{0}`' -f $YFinanceStatus)
$Report += ('- TRACKER_ROWS: `{0}`' -f $TrackerRows)
$Report += ('- FILLED_CELLS_THIS_RUN: `{0}`' -f $FilledCellsThisRun)
$Report += ('- PENDING_CELLS_THIS_RUN: `{0}`' -f $PendingCellsThisRun)
$Report += ('- FORWARD_COMPLETE_ROWS: `{0}`' -f $ForwardCompleteRows)
$Report += ('- FORWARD_PARTIAL_ROWS: `{0}`' -f $ForwardPartialRows)
$Report += ('- PENDING_FORWARD_ROWS: `{0}`' -f $PendingForwardRows)
$Report += ''
$Report += '## Steps'
$Report += ''
$Report += '| Step | Status | Seconds | Detail |'
$Report += '|---|---|---:|---|'
foreach ($x in $Steps) {
    $Report += ('| {0} | {1} | {2} | `{3}` |' -f $x.Step, $x.Status, $x.Seconds, $x.Detail)
}
$Report += ''
$Report += '## Files'
$Report += ''
$Report += ('- V18_8C_READ_FIRST: `{0}`' -f $V88CReadFirst)
$Report += ('- V18_8C_REPORT: `{0}`' -f $V88CReport)
$Report += ('- V18_9A_READ_FIRST: `{0}`' -f $V89AReadFirst)
$Report += ('- V18_9A_REPORT: `{0}`' -f $V89AReport)
$Report += ('- V18_9B_READ_FIRST: `{0}`' -f $V89BReadFirst)
$Report += ('- V18_9B_REPORT: `{0}`' -f $V89BReport)
$Report += ('- COMBINED_READ_FIRST: `{0}`' -f $CombinedReadFirst)
$Report += ('- COMBINED_REPORT: `{0}`' -f $CombinedReport)
$Report += ('- PROFILE: `{0}`' -f $Profile)
$Report += ('- STEP_CSV: `{0}`' -f $StepCsv)
$Report += ''
$Report += '## Interpretation'
$Report += ''
$Report += '- The official daily decision remains the source of truth.'
$Report += '- Simulation cabin, candidate tracker, and forward return filler are all shadow-only.'
$Report += '- Candidate tracking records what the system observed, not what it officially traded.'
$Report += '- Forward returns are filled only when horizons mature.'

$Report -join "`n" | Set-Content -Encoding UTF8 $CombinedReport

$RF = @()
$RF += 'V18.9C OFFICIAL DAILY WITH SIM VALIDATION'
$RF += ''
$RF += 'STATUS: OK_OFFICIAL_DAILY_WITH_SIM_VALIDATION_READY'
$RF += 'MODE: OFFICIAL_DAILY_PLUS_SHADOW_SIM_VALIDATION'
$RF += ('TOTAL_SECONDS: {0}' -f $TotalSeconds)
$RF += ('USE_YFINANCE: {0}' -f $UseYFinance)
$RF += ('ALLOW_LOCAL_APPROX: {0}' -f $AllowLocalApprox)
$RF += ''
$RF += ('FINAL_ACTION: {0}' -f $FinalAction)
$RF += ('BUY_PERMISSION: {0}' -f $BuyPermission)
$RF += ('VIX_REGIME: {0}' -f $VixRegime)
$RF += ('OFFICIAL_DECISION_IMPACT: {0}' -f $OfficialImpact)
$RF += ''
$RF += ('SIM_STATUS: {0}' -f $SimStatus)
$RF += ('SIM_MODE: {0}' -f $SimMode)
$RF += ('OFFICIAL_PERMISSION: {0}' -f $OfficialPermission)
$RF += ('CASH_USD: {0}' -f $CashUSD)
$RF += ('MARKET_VALUE_USD: {0}' -f $MarketValueUSD)
$RF += ('EQUITY_USD: {0}' -f $EquityUSD)
$RF += ('POSITION_COUNT: {0}' -f $PositionCount)
$RF += ''
$RF += ('CANDIDATE_TRACKER_STATUS: {0}' -f $CandidateTrackerStatus)
$RF += ('TODAY_CANDIDATE_COUNT: {0}' -f $TodayCandidateCount)
$RF += ('ELIGIBLE_SIM_BUY_COUNT: {0}' -f $EligibleSimBuyCount)
$RF += ('OBSERVE_OR_BLOCKED_COUNT: {0}' -f $ObserveOrBlockedCount)
$RF += ('TRACKER_TOTAL_ROWS: {0}' -f $TrackerTotalRows)
$RF += ''
$RF += ('FORWARD_STATUS: {0}' -f $ForwardStatus)
$RF += ('YFINANCE_STATUS: {0}' -f $YFinanceStatus)
$RF += ('TRACKER_ROWS: {0}' -f $TrackerRows)
$RF += ('FILLED_CELLS_THIS_RUN: {0}' -f $FilledCellsThisRun)
$RF += ('PENDING_CELLS_THIS_RUN: {0}' -f $PendingCellsThisRun)
$RF += ('FORWARD_COMPLETE_ROWS: {0}' -f $ForwardCompleteRows)
$RF += ('FORWARD_PARTIAL_ROWS: {0}' -f $ForwardPartialRows)
$RF += ('PENDING_FORWARD_ROWS: {0}' -f $PendingForwardRows)
$RF += ''
$RF += 'COMBINED_REPORT:'
$RF += $CombinedReport
$RF += ''
$RF += 'PROFILE:'
$RF += $Profile
$RF += ''
$RF += 'STEP_CSV:'
$RF += $StepCsv

$RF -join "`n" | Set-Content -Encoding UTF8 $CombinedReadFirst

Write-Host ""
Write-Host "=== V18.9C OFFICIAL DAILY WITH SIM VALIDATION READY ==="
Write-Host "STATUS: OK_OFFICIAL_DAILY_WITH_SIM_VALIDATION_READY"
Write-Host "TOTAL_SECONDS: $TotalSeconds"
Write-Host "FINAL_ACTION: $FinalAction"
Write-Host "BUY_PERMISSION: $BuyPermission"
Write-Host "VIX_REGIME: $VixRegime"
Write-Host "OFFICIAL_PERMISSION: $OfficialPermission"
Write-Host "SIM_STATUS: $SimStatus"
Write-Host "CANDIDATE_TRACKER_STATUS: $CandidateTrackerStatus"
Write-Host "TODAY_CANDIDATE_COUNT: $TodayCandidateCount"
Write-Host "FORWARD_STATUS: $ForwardStatus"
Write-Host "YFINANCE_STATUS: $YFinanceStatus"
Write-Host "PENDING_FORWARD_ROWS: $PendingForwardRows"
Write-Host "COMBINED_READ_FIRST: $CombinedReadFirst"
Write-Host "COMBINED_REPORT: $CombinedReport"
Write-Host "PROFILE: $Profile"
Write-Host ""
